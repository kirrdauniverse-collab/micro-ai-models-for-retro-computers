#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Célzott ZX81 ROM szétszerelés: a PC=$0044 beragadás hívási láncának rekonstrukciója.
Címek az EO-debugger címkéi + kanonikus ZX81 ROM elrendezés alapján.
"""
import sys
sys.path.insert(0, '/home/z/my-project/scripts')
from z80dis import block

rom = open('/home/z/my-project/GLM/refs/zx81.rom', 'rb').read()

# Kanonikus ZX81 ROM címkék (Logan & O'Hara + EO-debugger szerint)
LBL = {
    0x0000: 'START (RESET)',
    0x0008: 'ERROR-1 (RST 08)',
    0x0018: 'S-LOW-SCAN/MAIN-1?',
    0x0020: 'MAIN-1A?',
    0x0028: 'RST28',
    0x0030: 'RST30',
    0x0038: 'INT-HANDLER (IM1)',
    0x0041: 'WAIT-INT',
    0x0045: 'SCAN-LINE',
    0x0049: 'CH-ADD+1',
    0x0056: 'ERROR-2',
    0x0066: 'NMI',
    0x0207: 'SUB-0207 (ERROR-2 hívja)',
    0x0282: 'MAIN-4?',
    0x028B: 'VEREM-TETŐ cím (hívó a főciklusból)',
    0x0348: 'LD-BYTES? (tape)',
    0x034C: 'IN-BYTE?',
    0x03E5: 'INITIAL',
    0x04EE: 'VEREM-CÍM (hívó)',
    0x083D: 'VEREM-CÍM (hívó)',
    0x09AA: 'VEREM-CÍM (hívó)',
    0x14BC: 'ERROR-2 célja (REPORT?)',
    0x1488: 'RST30 cél',
}

ranges = [
    (0x0200, 0x02A0, 'DISPLAY-1 / MAIN környék'),
    (0x0282, 0x02D0, 'MAIN-4 + a $028B hívási pont'),
    (0x04D0, 0x0520, '$04EE környéke'),
    (0x0820, 0x0870, '$083D környéke'),
    (0x0990, 0x09D0, '$09AA környéke'),
    (0x14A0, 0x14E0, '$14BC környéke (REPORT?)'),
]

for start, end, title in ranges:
    print('===== %s ($%04X-$%04X) =====' % (title, start, end))
    print(block(rom, start, end, LBL))
    print()

# A veremben látott konkrét címek utasításai:
for a in (0x0024, 0x028B, 0x04EE, 0x09AA, 0x083D):
    print('--- $%04X utasítás-környezet ---' % a)
    print(block(rom, a - 8, a + 12))
    print()
