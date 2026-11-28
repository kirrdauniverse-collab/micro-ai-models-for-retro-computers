import os as _os
RT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
# Assemble src/engine.asm and place data tables + model at their fixed addresses.
import sys, struct, math
sys.path.insert(0, RT+'/tools')
from z80asm import Asm

CHARSET = "\n abcdefghijklmnopqrstuvwxyz,.?!'0123456789:-"   # RTLM charset, index = model id

def zx_code_for_char(c):
    c = c.upper()
    if c == ' ': return 0
    if 'A' <= c <= 'Z': return 38 + ord(c) - ord('A')
    if '0' <= c <= '9': return 28 + ord(c) - ord('0')
    return {',': 26, '.': 27, '?': 15, ':': 14, '-': 22}.get(c, 0)

def build(model_path, lut_path, src_path=RT+'/src/engine.asm'):
    a = Asm()
    a.assemble(open(src_path).read(), 'engine.asm')
    mem = {}
    for addr, v in a.out.items():
        mem[addr] = v
    code_end = max(a.out) + 1
    assert code_end <= 0x4E00, 'code overflows data area: %x' % code_end
    # sq[n] = floor(n*n/4), n in [-256,255] at SQB+2n, SQB=$4F00 -> table base $4D00
    base = 0x4E00
    for n in range(-256, 256):
        v = (n * n) // 4
        addr = base + 2 * (n + 256)
        mem[addr] = v & 255; mem[addr + 1] = v >> 8
    # EXPS at $5100: min(255, LUT[k] >> 4)
    import re
    src = open(lut_path).read()
    body = src[src.index('RT_EXP_LUT[256]'):].split('{', 1)[1].split('}', 1)[0]
    lut = [int(t) for t in re.findall(r'\d+', body)]
    assert len(lut) == 256
    for k in range(256):
        mem[0x5200 + k] = min(255, lut[k] >> 4)
    blob = open(model_path, 'rb').read()
    assert blob[:4] == b'RTLM' and len(blob) == 2666
    for i, v in enumerate(blob):
        mem[0x5300 + i] = v
    # MAPIN_T $5C80: ZX81 code (0..63) -> model index
    for code in range(64):
        idx = 1
        if code == 0: idx = 1
        elif 38 <= code <= 63: idx = 2 + (code - 38)          # A..Z -> a..z
        elif 28 <= code <= 37: idx = 33 + (code - 28)         # 0..9
        else:
            inv = {26: 28, 27: 29, 15: 30, 14: 43, 22: 44}
            idx = inv.get(code, 1)
        mem[0x5E00 + code] = idx
    # MAPOUT_T $5CC0: model index -> ZX81 code
    for idx in range(45):
        ch = CHARSET[idx]
        mem[0x5E40 + idx] = 118 if idx == 0 else zx_code_for_char(ch) if ch != '\'' else 0
    return mem, code_end

if __name__ == '__main__':
    mem, end = build(RT+'/models/base_f.bin', RT+'/ref/engine/rt_lut.h')
    lo, hi = min(mem), max(mem)
    print('code end %04x, image %04x..%04x (%d bytes)' % (end, lo, hi, hi - lo + 1))
