import os as _os
RT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
# Build the ZX81 16K image: app + engine + tables + model + topic id -> .P image and EO81 .t81
import sys, re, struct
sys.path.insert(0, RT+'/tools')
from z80asm import Asm
from build_engine import CHARSET, zx_code_for_char

SRC = ['src/app1.asm', 'src/app3.asm', 'src/app4.asm', 'src/app5.asm', 'src/app6.asm', 'src/app7.asm', 'src/engine.asm']
ZXMAP = {' ': 0, '.': 27, ',': 26, '?': 15, ':': 14, '-': 22, '/': 24, '*': 23,
         '+': 21, '=': 20, '(': 16, ')': 17, '>': 18, '<': 19}

def zxcodes(text):
    out = []
    for ch in text.replace('{Q}', '\x01'):
        if ch == '\x01': out.append(11); continue
        if 'A' <= ch <= 'Z': out.append(38 + ord(ch) - ord('A')); continue
        if '0' <= ch <= '9': out.append(28 + ord(ch) - ord('0')); continue
        if ch in ZXMAP: out.append(ZXMAP[ch]); continue
        raise ValueError('no ZX code for %r' % ch)
    return out

def zxify(src):
    def rep(m):
        kind, text = m.group(1), m.group(2)
        codes = zxcodes(text) + ([255] if kind == 'zs' else [])
        return 'db ' + ','.join(str(c) for c in codes)
    return re.sub(r'\b(zn|zs)\s+"([^"]*)"', rep, src)

def assemble(model_path, lut_path, topic_id, base_dir=RT):
    text = '\n'.join(zxify(open(_os.path.join(base_dir, f)).read()) for f in SRC)
    a = Asm()
    a.assemble(text, 'app')
    mem = dict(a.out)
    code_end = max(mem) + 1
    assert code_end <= 0x5500, 'code overflows: %04x' % code_end
    # sq table: SQB=$6C00, base $6A00 (free RAM after the chat LOG)
    for n in range(-256, 256):
        v = (n * n) // 4
        addr = 0x6A00 + 2 * (n + 256)
        mem[addr] = v & 255; mem[addr + 1] = v >> 8
    src = open(lut_path).read()
    body = src[src.index('RT_EXP_LUT[256]'):].split('{', 1)[1].split('}', 1)[0]
    lut = [int(t) for t in re.findall(r'\d+', body)]
    assert len(lut) == 256
    for k in range(256):
        mem[0x6E00 + k] = min(255, lut[k] >> 4)
    blob = open(model_path, 'rb').read()
    assert blob[:4] == b'RTLM' and len(blob) == 2666
    for i, v in enumerate(blob):
        mem[0x5500 + i] = v
    mem[0x5F6A] = topic_id
    for code in range(64):
        if code == 0: idx = 1
        elif 38 <= code <= 63: idx = 2 + (code - 38)
        elif 28 <= code <= 37: idx = 33 + (code - 28)
        else: idx = {26: 28, 27: 29, 15: 30, 14: 43, 22: 44}.get(code, 1)
        mem[0x5F80 + code] = idx
    for idx in range(45):
        ch = CHARSET[idx]
        mem[0x5FC0 + idx] = 118 if idx == 0 else (zx_code_for_char(ch) if ch != "'" else 0)
    return mem, code_end

P_BASE = 0x4009
P_VARS = 0x7E19
REM_START = 0x407D
PROG_END = 0x6FA7                    # the 118 that closes line 1

def p_image(mem, start_hi=None):
    img = bytearray(P_VARS + 1 - P_BASE)
    for a, v in mem.items():
        if P_BASE <= a <= P_VARS: img[a - P_BASE] = v
    def put(addr, val, n=2, big=False):
        b = val.to_bytes(n, 'big' if big else 'little')
        for i, x in enumerate(b): img[addr - P_BASE + i] = x
    put(0x4009, 0, 1)                # VERSN
    put(0x400A, 1)                   # E_PPC
    put(0x400C, 0x7B00)              # D_FILE
    put(0x400E, 0x7B01)              # DF_CC
    put(0x4010, P_VARS)              # VARS
    put(0x4012, 0x407D)              # DEST (unused)
    put(0x4014, 0x7E1A)              # E_LINE
    put(0x4016, 0x7E1A)              # CH_ADD
    put(0x401A, 0x7E1F)              # STKBOT
    put(0x401C, 0x7E1F)              # STKEND
    put(0x401F, 0x405D)              # MEM
    put(0x4004, 0x8000)              # RAMTOP
    put(0x4022, 2, 1)                # DF_SZ: 2 lines in the lower part (ROM default)
    put(0x4028, 31, 1)               # MARGIN: 31 blank lines above the picture (PAL)
    put(0x4034, 0)                   # FRAMES
    put(0x403B, 0x40, 1)             # CDFLAG: SLOW
    # line 1: 0001, len, REM token, code 4082..6FA6, 118
    off = REM_START - P_BASE
    line1_len = 1 + (PROG_END - 0x4082) + 1
    img[off:off + 2] = bytes([0, 1])
    img[off + 2:off + 4] = line1_len.to_bytes(2, 'little')
    img[off + 4] = 0xEA              # REM
    # code/tables region already filled from mem (4082..6FA6), now the terminator
    img[PROG_END - P_BASE] = 118
    # line 2: RAND USR VAL "16514"
    l2 = PROG_END + 1
    body = bytes([0xF9, 0xD4, 0xC5, 11, 29, 34, 33, 29, 32, 11, 118])
    img[l2 - P_BASE:l2 - P_BASE + 4] = bytes([0, 2, len(body), 0])
    img[l2 - P_BASE + 4:l2 - P_BASE + 4 + len(body)] = body
    for k in range(25):              # D-file: header + 24 row ends = $76
        img[0x7B00 + 33 * k - P_BASE] = 0x76
    img[P_VARS - P_BASE] = 0x80
    # D-file cells: only the row ends ($76) stay; every other cell is blank.
    # (a stray $80 at $7E16 showed as a black block at the bottom right)
    for a in range(0x7B01, P_VARS):
        if (a - 0x7B00) % 33 != 0: img[a - P_BASE] = 0
    img[P_VARS - P_BASE] = 0x80
    return bytes(img)

def eo81(blocks):
    out = bytearray(b'EO81')
    for name, data in blocks:
        out += name.encode().ljust(32, b'\0')
        out += str(len(data)).encode().ljust(16, b'\0')
        out += data
    return bytes(out)

if __name__ == '__main__':
    base = RT+'/models/'
    lut = RT+'/ref/engine/rt_lut.h'
    mem, end = assemble(base + 'base_f.bin', lut, 0)
    print('code end %04x' % end)
    p = p_image(mem)
    print('image bytes', len(p), 'first', p[:8].hex(), 'last', p[-4:].hex())
