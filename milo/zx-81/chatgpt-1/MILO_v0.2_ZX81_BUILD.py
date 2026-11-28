#!/usr/bin/env python3
"""MILO v0.2 one-file ZX81 16K builder.

Keeps the proven v0.1 RAM/D-FILE image as a template, replaces the machine-code
REM line with the newly assembled engine, and replaces the parked knowledge
blob. This avoids re-generating the fragile ZX81 display/system-variable area.
"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from MILO_v0_2_ZX81_KB import build_blob, MEM_ADDR

ENGINE_ORG = 0x4082
D_FILE = 0x7908
P_START = 0x4009
BASIC_START = 0x407D
NXTLIN = 0x4029
T81_HEAD = 52

def preprocess(src_path):
    lines = open(src_path, encoding="utf-8").read().splitlines()
    def ev(expr, ns):
        expr = re.sub(r"\b([A-Z_][A-Z_0-9]*)\b",
                      lambda m: str(ns[m.group(1)]) if m.group(1) in ns else m.group(1),
                      expr.strip())
        return eval(expr, {"__builtins__": {}})
    names = {}
    for ln in lines:
        s = ln.strip()
        if s and not s.startswith(";") and not s.startswith("."):
            m = re.match(r"^([A-Z_][A-Z_0-9]*)\s+equ\s+(.+?)\s*(?:;.*)?$", s)
            if m:
                names.setdefault(m.group(1), m.group(2))
    equs = {}
    for _ in range(40):
        changed = False
        for k, v in names.items():
            if k in equs:
                continue
            try:
                equs[k] = ev(v, equs); changed = True
            except Exception:
                pass
        if not changed:
            break
    missing = set(names) - set(equs)
    if missing:
        raise SystemExit("EQU UNSOLVED: %s" % sorted(missing))

    from MILO_v0_2_ZX81_KB import enc
    out = []
    for ln in lines:
        s = ln.strip()
        if not s or s.startswith(";"):
            out.append("")
            continue
        if re.match(r"^[A-Z_][A-Z_0-9]*\s+equ\s+", s):
            out.append("")
            continue
        if s.lower().startswith("db ") or s.lower() == "db":
            toks = re.findall(r'"([^"]*)"|([^,]+)', s[3:])
            items = []
            for a, b in toks:
                if a:
                    items += ["0x%02X" % x for x in enc(a) + bytes([0xFF])]
                elif b.strip():
                    items.append(b.strip())
            out.append("db " + ", ".join(items))
            continue
        core = s.split(";")[0].rstrip()
        for name in sorted(equs, key=len, reverse=True):
            core = re.sub(r"\b%s\b" % name, hex(equs[name]), core)
        core = re.sub(r",\\s+\\(", ",(", core)
        out.append(core)
    return "\n".join(out)

def assemble(src):
    from z80._asm import Asm
    from z80._source import SourceFile
    code = Asm().assemble(SourceFile(src))
    code.resolve()
    blocks = code.encode()
    blocks = [b for b in blocks if b[0] >= 0x4000]
    org = min(a for a, _ in blocks)
    data = b"".join(b[1] for b in blocks)
    return org, data

def zx_line(number, body):
    payload = body + b"\x76"
    if len(payload) > 0xFFFF:
        raise SystemExit("BASIC line too long")
    return bytes([(number >> 8) & 255, number & 255,
                  (len(payload) >> 8) & 255, len(payload) & 255]) + payload

def zx_digits(n):
    return bytes(0x1C + int(ch) for ch in str(n))

def build_image(template_t81, engine, blob):
    raw = open(template_t81, "rb").read()
    if raw[:4] != b"EO81":
        raise SystemExit("bad T81 template")
    old_len = int(raw[36:52].split(b"\0", 1)[0] or b"0")
    img = bytearray(raw[T81_HEAD:T81_HEAD + old_len])
    if len(img) != old_len:
        raise SystemExit("template payload truncated")

    # Proven template boundaries.
    dfile = img[3] | (img[4] << 8)
    if dfile != D_FILE:
        raise SystemExit("unexpected D_FILE 0x%04X" % dfile)

    line1 = zx_line(1, b"\xEA" + engine)
    line2 = zx_line(2, b"\xF9\xD4\xC5\x0B" + zx_digits(ENGINE_ORG) + b"\x0B")
    program = line1 + line2
    start = BASIC_START - P_START
    d_off = dfile - P_START
    if start + len(program) > d_off:
        raise SystemExit("BASIC program overlaps D-FILE")
    img[start:d_off] = b"\0" * (d_off - start)
    img[start:start + len(program)] = program

    # NXTLIN is the autostart address of line 2.
    line2_addr = BASIC_START + len(line1)
    nx_off = NXTLIN - P_START
    img[nx_off:nx_off+2] = bytes([line2_addr & 255, (line2_addr >> 8) & 255])

    # Park the new knowledge image exactly where v0.1 parked it.
    blob_off = MEM_ADDR - P_START
    work_end = blob_off + len(blob)
    if work_end > d_off:
        raise SystemExit("knowledge blob overlaps D-FILE")
    img[blob_off:work_end] = blob

    return bytes(img)

def main():
    asm = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "MILO_v0.2_ZX81.asm")
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "MILO_v0.2_ZX81.t81")
    template = sys.argv[3] if len(sys.argv) > 3 else os.path.join(HERE, "MILO_v0.1_ZX81.t81")

    text = preprocess(asm)
    tmp = "/tmp/MILO_v0.2_engine.src"
    open(tmp, "w", encoding="utf-8").write(text)
    org, engine = assemble(tmp)
    if org != ENGINE_ORG:
        raise SystemExit("engine org 0x%04X != 0x%04X" % (org, ENGINE_ORG))
    print("engine  0x%04X..0x%04X (%d bytes)" % (org, org + len(engine) - 1, len(engine)))

    blob = build_blob()
    img = build_image(template, engine, blob)
    if len(img) > 0x8000 - P_START:
        raise SystemExit("image does not fit 16K")
    name = b"MILO v0.2 ZX81"
    t81 = (b"EO81" + name.ljust(32, b"\0")[:32] +
           str(len(img)).encode().ljust(16, b"\0") + img)
    open(out, "wb").write(t81)
    p = os.path.splitext(out)[0] + ".p"
    open(p, "wb").write(img)
    print("T81 %s (%d bytes), P %s (%d bytes), D_FILE 0x%04X" %
          (out, len(t81), p, len(img), D_FILE))

if __name__ == "__main__":
    main()
