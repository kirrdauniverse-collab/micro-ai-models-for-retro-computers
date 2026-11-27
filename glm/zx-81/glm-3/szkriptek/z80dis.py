#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Kompakt, pontos Z80 disassembler — ZX81 ROM és .T81 gépikódhoz.
Használat:
    from z80dis import disasm_full, block
    txt, hossz, kov_pc = disasm_full(memoria, pc)
"""
R = ['B', 'C', 'D', 'E', 'H', 'L', '(HL)', 'A']
RP = ['BC', 'DE', 'HL', 'SP']
RP2 = ['BC', 'DE', 'HL', 'AF']
CC = ['NZ', 'Z', 'NC', 'C', 'PO', 'PE', 'P', 'M']
ROT = ['RLC', 'RRC', 'RL', 'RR', 'SLA', 'SRA', 'SLL', 'SRL']
ALU = ['ADD A', 'ADC A', 'SUB', 'SBC A', 'AND', 'XOR', 'OR', 'CP']


def u8(m, p):
    return m[p] & 0xFF


def i8(m, p):
    v = m[p] & 0xFF
    return v - 256 if v > 127 else v


def u16(m, p):
    return (m[p] | (m[p + 1] << 8)) & 0xFFFF


def hx8(v):
    return '$%02X' % (v & 0xFF)


def hx16(v):
    return '$%04X' % (v & 0xFFFF)


def _dis(m, pc):
    """Prefix nélküli (vagy már DD/FD-kontextusú) dekódolás.
    Visszaad: (szoveg, hossz, kovetkezo_pc) — PC-je a BASE-ra mutat."""
    op = m[pc]
    x, y, z = op >> 6, (op >> 3) & 7, op & 7
    p, q = y, (op >> 4) & 1

    if x == 0:
        if z == 0:
            if y == 0: return 'NOP', 1, pc + 1
            if y == 1: return "EX AF,AF'", 1, pc + 1
            if y == 2:
                off = i8(m, pc + 1)
                return 'DJNZ $%04X' % ((pc + 2 + off) & 0xFFFF), 2, pc + 2
            if y == 3:
                off = i8(m, pc + 1)
                return 'JR $%04X' % ((pc + 2 + off) & 0xFFFF), 2, pc + 2
            off = i8(m, pc + 1)
            return 'JR %s,$%04X' % (CC[y - 4], (pc + 2 + off) & 0xFFFF), 2, pc + 2
        if z == 1:
            if y % 2 == 0: return 'LD %s,%s' % (RP[y // 2], hx16(u16(m, pc + 1))), 3, pc + 3
            return 'ADD HL,%s' % RP[(y - 1) // 2], 1, pc + 1
        if z == 2:
            if y == 4: return 'LD (%s),HL' % hx16(u16(m, pc + 1)), 3, pc + 3
            if y == 5: return 'LD HL,(%s)' % hx16(u16(m, pc + 1)), 3, pc + 3
            if y == 6: return 'LD (%s),A' % hx16(u16(m, pc + 1)), 3, pc + 3
            if y == 7: return 'LD A,(%s)' % hx16(u16(m, pc + 1)), 3, pc + 3
        if z == 3:
            if y % 2 == 0: return 'INC %s' % RP[y // 2], 1, pc + 1
            return 'DEC %s' % RP[y // 2], 1, pc + 1
        if z == 4: return 'INC %s' % R[y], 1, pc + 1
        if z == 5: return 'DEC %s' % R[y], 1, pc + 1
        if z == 6: return 'LD %s,%s' % (R[y], hx8(u8(m, pc + 1))), 2, pc + 2
        # z == 7: egyszerű akkumulátor-rotációk / DAA stb.
        t = ['RLCA', 'RRCA', 'RLA', 'RRA', 'DAA', 'CPL', 'SCF', 'CCF'][y]
        return t, 1, pc + 1
    if x == 1:
        if z == 6 and y == 6: return 'HALT', 1, pc + 1
        return 'LD %s,%s' % (R[y], R[z]), 1, pc + 1
    if x == 2:
        return '%s %s' % (ALU[y], R[z]), 1, pc + 1
    # x == 3
    if z == 0: return 'RET %s' % CC[y], 1, pc + 1
    if z == 1:
        if y == 0: return 'POP BC', 1, pc + 1
        if y == 1: return 'RET', 1, pc + 1
        if y == 2: return 'POP DE', 1, pc + 1
        if y == 3: return 'EXX', 1, pc + 1
        if y == 4: return 'POP HL', 1, pc + 1
        if y == 5: return 'JP (HL)', 1, pc + 1
        if y == 6: return 'POP AF', 1, pc + 1
        return 'LD SP,HL', 1, pc + 1
    if z == 2: return 'JP %s,%s' % (CC[y], hx16(u16(m, pc + 1))), 3, pc + 3
    if z == 3:
        if y == 0: return 'JP %s' % hx16(u16(m, pc + 1)), 3, pc + 3
        if y == 1: return 'DB $CB', 1, pc + 1
        if y == 2: return 'OUT (%s),A' % hx8(u8(m, pc + 1)), 2, pc + 2
        if y == 3: return 'IN A,(%s)' % hx8(u8(m, pc + 1)), 2, pc + 2
        if y == 4: return 'EX (SP),HL', 1, pc + 1
        if y == 5: return 'EX DE,HL', 1, pc + 1
        if y == 6: return 'DI', 1, pc + 1
        return 'EI', 1, pc + 1
    if z == 4: return 'CALL %s,%s' % (CC[y], hx16(u16(m, pc + 1))), 3, pc + 3
    if z == 5:
        if y == 0: return 'PUSH BC', 1, pc + 1
        if y == 1: return 'CALL %s' % hx16(u16(m, pc + 1)), 3, pc + 3
        if y == 2: return 'PUSH DE', 1, pc + 1
        if y == 3: return 'CALL %s,%s' % (CC[1], hx16(u16(m, pc + 1))), 3, pc + 3
        if y == 4: return 'PUSH HL', 1, pc + 1
        if y == 5: return 'DB $%02X (CALL nz?)' % op, 1, pc + 1
        if y == 6: return 'PUSH AF', 1, pc + 1
        return 'DB $%02X' % op, 1, pc + 1
    if z == 6: return '%s %s' % (ALU[y], hx8(u8(m, pc + 1))), 2, pc + 2
    return 'RST $%02X' % (y * 8), 1, pc + 1


def _dis_cb(m, pc, idx=None):
    op = m[pc]
    y, z = (op >> 3) & 7, op & 7
    # y<8 belső rotációkra nincs itt szükség mind; BIT/SET/RES + rotációk:
    if op < 0x40:
        if idx:
            return '%s %s' % (ROT[y], '(%s)' % idx), 2, pc + 2
        return '%s %s' % (ROT[y], R[z]), 2, pc + 2
    grp, bit = (op >> 3) & 7, op & 7
    nm = ['BIT', 'RES', 'SET'][(op >> 6) - 1] if op >= 0x40 else ''
    if op >= 0x40:
        nm = ('BIT', 'RES', 'SET')[(op >> 6) - 1]
        bit = (op >> 3) & 7
        dst = '(%s)' % idx if idx else R[op & 7]
        return '%s %d,%s' % (nm, bit, dst), 2, pc + 2
    return 'CB %02X' % op, 2, pc + 2


def _dis_ed(m, pc):
    op = m[pc]
    x, y, z = op >> 6, (op >> 3) & 7, op & 7
    if x == 1:
        if z == 0 and y < 4: return 'IN %s,(C)' % R[y], 2, pc + 2
        if z == 1 and y < 4: return 'OUT (C),%s' % R[y], 2, pc + 2
        if z == 2 and y < 4: return 'SBC HL,%s' % RP[y], 2, pc + 2
        if z == 2 and y == 4: return 'LD (%s),HL' % hx16(u16(m, pc + 2)), 4, pc + 4
        if z == 2 and y == 5: return 'LD (%s),DE' % hx16(u16(m, pc + 2)), 4, pc + 4
        if z == 3 and y < 4: return 'LD (%s),%s' % (hx16(u16(m, pc + 2)), RP[y]), 4, pc + 4
        if z == 3 and y == 4: return 'LD HL,(%s)' % hx16(u16(m, pc + 2)), 4, pc + 4
        if z == 3 and y == 5: return 'LD DE,(%s)' % hx16(u16(m, pc + 2)), 4, pc + 4
        if z == 4 and y < 4: return 'LD %s,(%s)' % (RP[y], hx16(u16(m, pc + 2))), 4, pc + 4
        if op == 0x44: return 'NEG', 2, pc + 2
        if op == 0x45: return 'RETN', 2, pc + 2
        if op == 0x4D: return 'RETI', 2, pc + 2
        if op == 0x46: return 'IM 0', 2, pc + 2
        if op == 0x56: return 'IM 1', 2, pc + 2
        if op == 0x5E: return 'IM 2', 2, pc + 2
        if op == 0x57: return 'LD A,I', 2, pc + 2
        if op == 0x5F: return 'LD A,R', 2, pc + 2
        if op == 0x47: return 'LD I,A', 2, pc + 2
        if op == 0x4F: return 'LD R,A', 2, pc + 2
        if op == 0x67: return 'RRD', 2, pc + 2
        if op == 0x6F: return 'RLD', 2, pc + 2
    if x == 2:
        t = {0x40: 'LDI', 0x48: 'LDD', 0x50: 'LDI?DB', 0x52: 'DB ED,52',
             0x58: 'LDDR?', 0x5A: 'DB ED,5A',
             0x60: 'INI', 0x68: 'IND', 0x70: 'DB ED,70', 0x78: 'DB ED,78',
             0xA0: 'LDI', 0xA8: 'LDD', 0xB0: 'LDIR', 0xB8: 'LDDR',
             0xA1: 'CPI', 0xA9: 'CPD', 0xB1: 'CPIR', 0xB9: 'CPDR',
             0xA2: 'INI', 0xAA: 'IND', 0xB2: 'INIR', 0xBA: 'INDR',
             0xA3: 'OUTI', 0xAB: 'OUTD', 0xB3: 'OTIR', 0xBB: 'OTDR'}
        return t.get(op, 'DB ED,%02X' % op), 2, pc + 2
    return 'DB ED,%02X' % op, 2, pc + 2


def _dis_idx(m, pc, idx):
    """DD/FD prefixált utasítás dekódolása; pc a PREFIX UTÁNI bájtra mutat.
    A visszaadott 'n' a TELJES (prefixszel együtt vett) következő PC!"""
    op = m[pc]
    p = idx  # 'IX' / 'IY'
    if op == 0x21: return 'LD %s,%s' % (p, hx16(u16(m, pc + 1))), 4, pc + 4
    if op == 0x22: return 'LD (%s),%s' % (hx16(u16(m, pc + 1)), p), 4, pc + 4
    if op == 0x2A: return 'LD %s,(%s)' % (p, hx16(u16(m, pc + 1))), 4, pc + 4
    if op == 0x23: return 'INC %s' % p, 2, pc + 2
    if op == 0x2B: return 'DEC %s' % p, 2, pc + 2
    if op == 0x34:
        d = i8(m, pc + 1)
        return 'INC (%s%s)' % (p, _dd(d)), 3, pc + 3
    if op == 0x35:
        d = i8(m, pc + 1)
        return 'DEC (%s%s)' % (p, _dd(d)), 3, pc + 3
    if op == 0x36:
        d = i8(m, pc + 1)
        return 'LD (%s%s),%s' % (p, _dd(d), hx8(u8(m, pc + 2))), 4, pc + 4
    if op == 0xE3: return 'EX (SP),%s' % p, 2, pc + 2
    if op == 0xE5: return 'PUSH %s' % p, 2, pc + 2
    if op == 0xE1: return 'POP %s' % p, 2, pc + 2
    if op == 0xE9: return 'JP (%s)' % p, 2, pc + 2
    if op == 0xF9: return 'LD SP,%s' % p, 2, pc + 2
    if op == 0x86:
        d = i8(m, pc + 1)
        return 'ADD A,(%s%s)' % (p, _dd(d)), 3, pc + 3
    if op == 0x96:
        d = i8(m, pc + 1)
        return 'SUB (%s%s)' % (p, _dd(d)), 3, pc + 3
    if op == 0xBE:
        d = i8(m, pc + 1)
        return 'CP (%s%s)' % (p, _dd(d)), 3, pc + 3
    if op == 0x46:
        d = i8(m, pc + 1)
        return 'LD B,(%s%s)' % (p, _dd(d)), 3, pc + 3
    if op == 0x56:
        d = i8(m, pc + 1)
        return 'LD D,(%s%s)' % (p, _dd(d)), 3, pc + 3
    if op == 0x5E:
        d = i8(m, pc + 1)
        return 'LD E,(%s%s)' % (p, _dd(d)), 3, pc + 3
    if op == 0x66:
        d = i8(m, pc + 1)
        return 'LD H,(%s%s)' % (p, _dd(d)), 3, pc + 3
    if op == 0x6E:
        d = i8(m, pc + 1)
        return 'LD L,(%s%s)' % (p, _dd(d)), 3, pc + 3
    if op == 0x7E:
        d = i8(m, pc + 1)
        return 'LD A,(%s%s)' % (p, _dd(d)), 3, pc + 3
    if op == 0x70:
        d = i8(m, pc + 1)
        return 'LD (%s%s),B' % (p, _dd(d)), 3, pc + 3
    if op == 0x74:
        d = i8(m, pc + 1)
        return 'LD (%s%s),H' % (p, _dd(d)), 3, pc + 3
    if op == 0x75:
        d = i8(m, pc + 1)
        return 'LD (%s%s),L' % (p, _dd(d)), 3, pc + 3
    if op == 0x77:
        d = i8(m, pc + 1)
        return 'LD (%s%s),A' % (p, _dd(d)), 3, pc + 3
    if op == 0xCB:
        d = i8(m, pc + 1)
        cbop = m[pc + 2]
        if cbop < 0x40:
            nm = ROT[(cbop >> 3) & 7]
        else:
            nm = ('BIT', 'RES', 'SET')[(cbop >> 6) - 1] + ' %d,' % ((cbop >> 3) & 7)
        return '%s (%s%s)' % (nm, p, _dd(d)), 4, pc + 4
    if 0x40 <= op <= 0x7F and ((op >> 3) & 7) != 6 and (op & 7) != 6:
        return _dis(m, pc)  # sima r,r — HL-szerep nélkül
    return 'DB %s,%02X' % (idx, op), 2, pc + 2


def _dd(d):
    return ('+$%02X' % (d & 0xFF)) if d >= 0 else ('-$%02X' % (-d & 0xFF))


def disasm_full(m, pc):
    """Teljes prefix-tudó szétszerelés. Visszaad: (szöveg, hossz, következő_pc)."""
    b0 = m[pc]
    if b0 == 0xCB:
        t, l, n = _dis_cb(m, pc + 1)
        return t, l, pc + l
    if b0 == 0xED:
        t, l, n = _dis_ed(m, pc + 1)
        return t, l, pc + l
    if b0 == 0xDD:
        t, l, n = _dis_idx(m, pc + 1, 'IX')
        return t, l, n
    if b0 == 0xFD:
        t, l, n = _dis_idx(m, pc + 1, 'IY')
        return t, l, n
    return _dis(m, pc)


def _dis_cb(m, pc):
    """CB-prefix dekódolás; a pc a CB UTÁNI bájtra mutat."""
    op = m[pc]
    if op < 0x40:
        return '%s %s' % (ROT[(op >> 3) & 7], R[op & 7]), 2, pc + 1
    nm = ('BIT', 'RES', 'SET')[(op >> 6) - 1]
    return '%s %d,%s' % (nm, (op >> 3) & 7, R[op & 7]), 2, pc + 1


def block(m, start, end, labels=None):
    """Címkézett szétszerelés szövegként (start..end)."""
    labels = labels or {}
    out = []
    pc = start
    while pc <= end:
        if pc in labels:
            out.append('')
            out.append('%s:' % labels[pc])
        try:
            txt, ln, nxt = disasm_full(m, pc)
        except Exception as e:
            txt, ln, nxt = '?? (%s)' % e, 1, pc + 1
        raw = ' '.join('%02X' % (m[pc + i] & 0xFF) for i in range(min(ln, 4)))
        out.append(' %04X  %-14s %s' % (pc, raw, txt))
        pc = nxt
    return '\n'.join(out)


if __name__ == '__main__':
    # önteszt a ROM ismert részein
    rom = open('/home/z/my-project/GLM/refs/zx81.rom', 'rb').read()
    print(block(rom, 0x0000, 0x0060))
    print('---')
    print(block(rom, 0x0066, 0x0090))
