#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A ROM összes CDFLAG ($403B) és OUT($FD)/OUT($FE) érintésének kigyűjtése,
plusz a szalag-rutinok szétszerelése — a post-LOAD SLOW-visszaállítás nyomában.
Illetve RTBOOT01 és RTBASE16 CDFLAG-értéke a blokkok rendszerképében."""
import sys
sys.path.insert(0, '/home/z/my-project/scripts')
sys.path.insert(0, '/home/z/my-project/GLM/repo/tools')
from z80dis import block as dis_block
from zx81sim import load_blocks

rom = open('/home/z/my-project/GLM/refs/zx81.rom', 'rb').read()

print('=== OUT ($FD) / OUT ($FE) előfordulások a ROM-ban (D3 FD / D3 FE) ===')
for i in range(len(rom) - 1):
    if rom[i] == 0xD3 and rom[i + 1] in (0xFD, 0xFE):
        print('  $%04X: OUT ($%02X)   [kontextus: %s]' % (
            i, rom[i + 1], ' '.join('%02X' % b for b in rom[max(0, i - 6):i + 4])))

print()
print('=== $403B (CDFLAG) közvetlen érintések (FD-prefix IY+3B / 21 3B 40 / 3A 3B 40 / 32 3B 40) ===')
pats = [(b'\xfd\xcb\x3b', 'FD CB 3B (IY+3B) bit-művelet'),
        (b'\x21\x3b\x40', 'LD HL,$403B'),
        (b'\x3a\x3b\x40', 'LD A,($403B)'),
        (b'\x32\x3b\x40', 'LD ($403B),A'),
        (b'\x22\x3b\x40', 'LD ($403B),HL')]
for pat, desc in pats:
    start = 0
    while True:
        j = rom.find(pat, start)
        if j < 0:
            break
        print('  $%04X: %s' % (j, desc))
        start = j + 1

print()
print('=== Szalag-rutin régió szétszerelése $02E7-$0460 ===')
LBL = {0x02E7: 'FAST-segéd (BIT7 IY+3B)', 0x02EC: 'HALT-pont', 0x02F3: 'RET',
       0x02F4: 'hiba-kód?', 0x0300: '?', 0x031E: 'SUB-031E', 0x0346: '?'}
print(dis_block(rom, 0x02E7, 0x0345, LBL))

print()
print('=== Blokkok rendszerképében CDFLAG ($403B) és kulcsmutatók ===')
for bname in ('RTBOOT01', 'RTBASE16', 'RT-TUDOM'):
    for name, data in load_blocks('/home/z/my-project/download/GLM_PicoAI_v0.8.0_kazetta.T81'):
        if name != bname:
            continue
        # név-hossz kihagyás
        k = 0
        while k < len(data) and not (data[k] & 0x80):
            k += 1
        base = k + 1
        sv = data[base:base + 0x74]
        def le16(o): return sv[o] | (sv[o + 1] << 8)
        print('%s: CDFLAG($403B)=$%02X  D_FILE=$%04X VARS=$%04X E_LINE=$%04X RAMTOP=$%04X  DF_SZ($4022..)=?$%02X' % (
            name, sv[0x403B - 0x4009], le16(0x400C - 0x4009), le16(0x4010 - 0x4009),
            le16(0x4014 - 0x4009), le16(0x4026 - 0x4009), sv[0x4022 - 0x4009]))
        # $4027 és $4028 értékek is (DF-SZ / MARGIN?)
        print('   $4027=$%02X $4028=$%02X $4029-402A=$%04X $402C-402D=$%04X $4030-4031=$%04X $4034-4035=$%04X' % (
            sv[0x4027 - 0x4009], sv[0x4028 - 0x4009],
            le16(0x4029 - 0x4009), le16(0x402C - 0x4009),
            le16(0x4030 - 0x4009), le16(0x4034 - 0x4009)))
        break
