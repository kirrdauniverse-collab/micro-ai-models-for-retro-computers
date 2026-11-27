#!/usr/bin/env python3
"""trap_disasm.py — a $7AE0-es farokcsapda környékének kibontása a
v0.8.1 kazetta blokkjaiból, kézi Z80-dekódolással.

Cél: megérteni a várakozó hurkot, hogy a v0.9.2-es 3-bájtos csapda-patch
NE írjon portot (nincs sync-injektálás => nincs csíkos kép) és NE ugorjon
NMI-várakozásba FAST módban (nincs örök PC=$004x).
"""
import sys

Z80_SIMPLE = {
    0x00: ('NOP', 0), 0x76: ('HALT', 0), 0xC9: ('RET', 0),
    0xF3: ('DI', 0), 0xFB: ('EI', 0), 0xAF: ('XOR A', 0),
    0xA7: ('AND A', 0), 0xB7: ('OR A', 0), 0x2F: ('CPL', 0),
}


def disasm(buf, base):
    """Very small decoder: only what the trap region needs."""
    i, out = 0, []
    while i < len(buf):
        op = buf[i]
        addr = base + i
        if op in Z80_SIMPLE:
            out.append((addr, Z80_SIMPLE[op][0], buf[i:i+1]))
            i += 1
        elif op == 0x3A:  # LD A,(nn)
            out.append((addr, f'LD A,(${buf[i+2]:02X}{buf[i+1]:02X})', buf[i:i+3])); i += 3
        elif op == 0xE6:  # AND n
            out.append((addr, f'AND ${buf[i+1]:02X}', buf[i:i+2])); i += 2
        elif op == 0xF6:  # OR n
            out.append((addr, f'OR ${buf[i+1]:02X}', buf[i:i+2])); i += 2
        elif op == 0xC6:  # ADD A,n
            out.append((addr, f'ADD A,${buf[i+1]:02X}', buf[i:i+2])); i += 2
        elif op in (0xCA, 0xC2, 0xC3, 0xDA, 0xD2, 0xEA, 0xE2, 0xFA, 0xF2):
            mn = {0xCA: 'JP Z', 0xC2: 'JP NZ', 0xC3: 'JP', 0xDA: 'JP C',
                  0xD2: 'JP NC', 0xEA: 'JP PE', 0xE2: 'JP PO',
                  0xFA: 'JP M', 0xF2: 'JP P'}[op]
            out.append((addr, f'{mn},${buf[i+2]:02X}{buf[i+1]:02X}', buf[i:i+3])); i += 3
        elif op in (0x18, 0x38, 0x30, 0x28, 0x20, 0x10):
            mn = {0x18: 'JR', 0x38: 'JR C', 0x30: 'JR NC',
                  0x28: 'JR Z', 0x20: 'JR NZ', 0x10: 'DJNZ'}[op]
            off = buf[i+1]
            tgt = addr + 2 + (off - 256 if off > 127 else off)
            out.append((addr, f'{mn},${tgt:04X}', buf[i:i+2])); i += 2
        elif op == 0xD3:  # OUT (n),A
            out.append((addr, f'OUT (${buf[i+1]:02X}),A', buf[i:i+2])); i += 2
        elif op == 0xDB:  # IN A,(n)
            out.append((addr, f'IN A,(${buf[i+1]:02X})', buf[i:i+2])); i += 2
        elif op in (0xCD,):  # CALL nn
            out.append((addr, f'CALL ${buf[i+2]:02X}{buf[i+1]:02X}', buf[i:i+3])); i += 3
        elif op in (0xC4, 0xCC):  # CALL NZ/Z
            mn = {0xC4: 'CALL NZ', 0xCC: 'CALL Z'}[op]
            out.append((addr, f'{mn},${buf[i+2]:02X}{buf[i+1]:02X}', buf[i:i+3])); i += 3
        elif 0x40 <= op <= 0x7F and (op & 7) == 6:  # LD r,(HL) / LD (HL),r
            out.append((addr, f'LD-opcode ${op:02X}', buf[i:i+1])); i += 1
        elif op == 0x21:  # LD HL,nn
            out.append((addr, f'LD HL,${buf[i+2]:02X}{buf[i+1]:02X}', buf[i:i+3])); i += 3
        elif op == 0x7E:  # LD A,(HL)
            out.append((addr, 'LD A,(HL)', buf[i:i+1])); i += 1
        elif op == 0x32:  # LD (nn),A
            out.append((addr, f'LD (${'%02X%02X' % (buf[i+2], buf[i+1])}),A', buf[i:i+3])); i += 3
        elif op == 0xE9:  # JP (HL)
            out.append((addr, 'JP (HL)', buf[i:i+1])); i += 1
        elif op == 0xFE:  # CP n
            out.append((addr, f'CP ${buf[i+1]:02X}', buf[i:i+2])); i += 2
        elif op == 0xB8 <= op <= 0xBF:  # CP r
            out.append((addr, f'CP r(${op:02X})', buf[i:i+1])); i += 1
        else:
            out.append((addr, f'??? ${op:02X}', buf[i:i+1])); i += 1
    return out


def dump_trap(cassette, block, lo=0x7ADC, hi=0x7B00):
    raw = open(cassette, 'rb').read()
    pos = 4
    while pos + 48 <= len(raw):
        name = raw[pos:pos+32].rstrip(b'\0').decode()
        ln = int(raw[pos+32:pos+48].rstrip(b'\0'))
        data = raw[pos+48:pos+ln+48]
        if name == block:
            off = lo - 0x4009 + 8
            n = hi - lo
            print(f'== {name}: ${lo:04X}..${hi:04X} (blokkon beluli offset {off:#x})')
            for a, txt, b in disasm(data[off:off+n], lo):
                h = ' '.join(f'{x:02X}' for x in b)
                print(f'  {a:04X}: {h:<9} {txt}')
            return
        pos += 48 + ln


if __name__ == '__main__':
    base = '/home/z/my-project/download/'
    for blk in ('RTBOOT01', 'RTBASE16'):
        dump_trap(base + 'GLM_PicoAI_v0.8.1_kazetta.T81', blk)
        print()
