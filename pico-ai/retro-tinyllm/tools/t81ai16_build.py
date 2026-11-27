#!/usr/bin/env python3
"""t81ai16_build.py - build the ONE-FILE ZX81 AI cassette (mistral_zx81ai16.t81).

Pipeline:
  1. preprocess ports/zx81/ai16/zx81ai.asm (resolve the numeric equ's,
     fold the kosarev-hostile expressions, expand db "..." literals into
     ZX81-charset bytes with the 0xFF terminator; 0x00 is the SPACE
     character on the ZX81, so 0xFF terminates every text)
  2. assemble with the pip "z80" package (kosarev)
  3. park the knowledge banks + MEM slot + the inert RT-TURBO stub as
     one blob (tools/ai16/zx81ai_kb.py)
  4. wrap everything with tools/t81frame.py into a single .t81 cassette:
     line 1 = 1 REM <engine>, line 2 = 2 RAND USR VAL "16514",
     then the parked RAM image below 0x8000 (16K machine!)

Usage: python3 tools/t81ai16_build.py [asm] [out.t81]
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, 'ai16'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))

from zx81ai_kb import build_blob, MEM_ADDR      # noqa: E402
from t81frame import build_image, zx_digits    # noqa: E402

ASM_PATH = os.path.join(ROOT, 'ports/zx81/ai16/zx81ai.asm')
OUT_PATH = os.path.join(ROOT, 'ports/zx81/mistral_zx81ai16.t81')
ENGINE_ORG = 0x4082


def preprocess(src_path):
    """asm text -> kosarev-clean source text (small subset preprocessor)."""
    lines = open(src_path).read().split('\n')

    def ev(expr, ns):
        expr = re.sub(r'\b([A-Z_][A-Z_0-9]*)\b',
                      lambda m: str(ns[m.group(1)])
                      if m.group(1) in ns else m.group(1), expr.strip())
        return eval(expr, {'__builtins__': {}})

    names = {}
    for ln in lines:
        s = ln.strip()
        if s and not s.startswith(';') and not s.startswith('.'):
            m = re.match(r'^([A-Z_][A-Z_0-9]*)\s+equ\s+(.+?)\s*(?:;.*)?$', s)
            if m:
                names.setdefault(m.group(1), m.group(2))
    equs = {}
    for _ in range(30):
        changed = False
        for k, v in names.items():
            if k in equs and isinstance(equs[k], int):
                continue
            try:
                equs[k] = ev(v, equs)
                changed = True
            except Exception:
                pass
        if not changed:
            break
    missing = set(names) - set(equs)
    if missing:
        raise SystemExit('EQU UNSOLVED: %s' % sorted(missing))

    pat = re.compile(r'(-?0x[0-9A-Fa-f]+|-?\d+)\s*([+\-])\s*'
                     r'(-?0x[0-9A-Fa-f]+|-?\d+)')

    def fold(core):
        changed = True
        while changed:
            changed = False
            m = pat.search(core)
            if m:
                a, b = int(m.group(1), 0), int(m.group(3), 0)
                val = a + b if m.group(2) == '+' else a - b
                core = core[:m.start()] + hex(val & 0xFFFF) + core[m.end():]
                changed = True
        return core

    from zx81ai_kb import enc
    out = []
    for s in lines:
        s = s.strip()
        if not s or s.startswith(';'):
            out.append('')
            continue
        if re.match(r'^[A-Z_][A-Z_0-9]*\s+equ\s+', s):
            out.append('')
            continue
        if s.lower().startswith('db ') or s.lower() == 'db':
            toks = re.findall(r'"([^"]*)"|([^,]+)', s[3:])
            items = []
            for m in toks:
                if m[0] != '':
                    b = enc(m[0]) + bytes([0xFF])
                    items += ['0x%02X' % x for x in b]
                else:
                    t = m[1].strip()
                    if t:
                        items.append(t)
            out.append('db ' + ', '.join(items))
            continue
        core = s.split(';')[0].rstrip()
        for name in sorted(equs, key=len, reverse=True):
            core = re.sub(r'\b%s\b' % name, hex(equs[name]), core)
        out.append(fold(core).strip())
    return '\n'.join(out)


def assemble(src):
    from z80._asm import Asm
    from z80._source import SourceFile
    code = Asm().assemble(SourceFile(src))
    code.resolve()
    blocks = code.encode()
    data = b''.join(b[1] for b in blocks if b[0] >= 0x4000)
    org = min(a for a, _ in blocks)
    return org, data


def main():
    asm = sys.argv[1] if len(sys.argv) > 1 else ASM_PATH
    out = sys.argv[2] if len(sys.argv) > 2 else OUT_PATH
    text = preprocess(asm)
    tmp = '/tmp/t81ai16_engine.src'
    with open(tmp, 'w') as f:
        f.write(text)
    org, engine = assemble(tmp)
    assert org == ENGINE_ORG, 'engine org 0x%X != 0x%X' % (org, ENGINE_ORG)
    engine_end = org + len(engine)

    blob = build_blob()
    margin = MEM_ADDR - engine_end
    if margin < 16:   # 15 bytes: the "2 RAND USR ..." line must fit above
        raise SystemExit(
            'engine too big: ends 0x%04X, MEM slot 0x%04X (%d bytes left)'
            % (engine_end, MEM_ADDR, margin))
    if engine_end > 0x8000:
        raise SystemExit('engine out of 16K RAM')

    print('engine    0x%04X..0x%04X  (%4d bytes)' % (org, engine_end - 1,
                                                     len(engine)))
    blob_end = MEM_ADDR + len(blob)
    if blob_end > 0x8000:
        raise SystemExit('blob out of 16K RAM')
    lines = [
        (1, b'\xEA' + engine),
        (2, b'\xF9\xD4\xC5\x0B' + zx_digits(ENGINE_ORG) + b'\x0B'),
    ]
    img, dfile = build_image(lines, blobs=[(MEM_ADDR, blob)])
    end = 0x4009 + len(img)
    print('image     0x%04X..0x%04X  (%4d bytes, fits 16K: %s)'
          % (0x4009, end - 1, len(img), end <= 0x8000))
    if end > 0x8000:
        raise SystemExit('image does NOT fit a 16K ZX81')

    name = b'ZX81 AI 16K'
    t81 = (b'EO81' + name.ljust(32, b'\x00')[:32]
           + ('%d' % len(img)).encode().ljust(16, b'\x00') + img)
    with open(out, 'wb') as f:
        f.write(t81)
    with open(out.rsplit('.', 1)[0] + '.p', 'wb') as f:
        f.write(img)
    print('cassette  %s (%d bytes) | D-file 0x%04X | blob %d bytes'
          % (out, len(t81), dfile, len(blob)))


if __name__ == '__main__':
    main()
