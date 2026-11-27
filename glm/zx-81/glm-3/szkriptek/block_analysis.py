#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RTBASE16 blokk elemzése: BASIC sorok, sztringek, gépikód-utastítások
az OUT(FD)/OUT(FE) [NMI ki/be] keresésével — a PC=$0041 WAIT-INT csapda okához.
"""
import sys
sys.path.insert(0, '/home/z/my-project/scripts')
sys.path.insert(0, '/home/z/my-project/GLM/repo/tools')
from z80dis import block as dis_block
from zx81sim import load_blocks

# Helyes token-tábla (a 7. menet ROM szó-táblájából)
TOK = {
    0xD3: 'PEEK', 0xD4: 'USR', 0xDE: 'THEN', 0xDF: 'TO',
    0xE4: 'SLOW', 0xE5: 'FAST', 0xE6: 'NEW',
    0xEA: 'REM', 0xEB: 'FOR', 0xEC: 'GOTO', 0xED: 'GOSUB',
    0xEE: 'INPUT', 0xEF: 'LOAD', 0xF0: 'LIST', 0xF1: 'LET',
    0xF2: 'PAUSE', 0xF3: 'NEXT', 0xF4: 'POKE', 0xF5: 'PRINT',
    0xF6: 'PLOT', 0xF7: 'RUN', 0xF8: 'SAVE', 0xF9: 'RAND',
    0xFA: 'IF', 0xFB: 'CLS', 0xFD: 'RETURN', 0xFE: 'COPY', 0xFF: 'CLEAR',
}


def detok(b):
    out = []
    for c in b:
        if 0x00 <= c < 0x0B:
            out.append(' graphics')
        elif c in TOK:
            out.append(' ' + TOK[c])
        elif 0x20 <= c < 0x7F:
            out.append(chr(c))
        elif c == 0x76:
            out.append('\n[76]')
        else:
            out.append('<%02X>' % c)
    return ''.join(out)


def find_t81():
    return '/home/z/my-project/download/GLM_PicoAI_v0.8.0_kazetta.T81'


blocks = load_blocks(find_t81())
print('blokkok:', [(n, len(d)) for n, d in blocks][:4], '...')

for name, data in blocks:
    if name.strip() != 'RTBASE16':
        continue
    print('\n######## RTBASE16 blokk — %d bájt ########' % len(data))
    # A 0x74 bájt "fejléc" (rendszer-változó kép + munkaterület kezdete)
    print('--- első 0x80 bájt (hex) ---')
    for i in range(0, 0x80, 16):
        print('%04X: %s  %s' % (0x4009 + i, ' '.join('%02X' % b for b in data[i:i + 16]),
                                 ''.join(chr(b) if 0x20 <= b < 0x7F else '.' for b in data[i:i + 16])))
    # ASCII sztringek keresése (a banner: "0.6.5", "RT-", stb.)
    print('\n--- ASCII sztringek (>=4 hosszú futamok) ---')
    cur, st = [], 0
    for i, b in enumerate(data):
        if 0x20 <= b < 0x7F:
            if not cur:
                st = i
            cur.append(b)
        else:
            if len(cur) >= 4:
                print('@%04X ($%04X): %r' % (st, 0x4009 + st, bytes(cur)))
            cur = []
    # BASIC sorok eleme: 0x74 után
    print('\n--- BASIC sorok (0x74 offszett után) ---')
    p = 0x74
    while p + 4 <= len(data) and data[p] != 0x80:
        ln = (data[p] << 8) | data[p + 1]
        ll = (data[p + 2] << 8) | data[p + 3]
        if ll == 0 or p + 4 + ll > len(data):
            print('HIBA: érvénytelen sorhossz @%04X (ln=%d, ll=%d)' % (0x4009 + p, ln, ll))
            break
        body = data[p + 4:p + 4 + ll]
        txt = detok(body)
        print('$%04X: %5d (hossz %4d): %s' % (0x4009 + p, ln, ll, txt[:200]))
        p += 4 + ll
    print('program vége @ $%04X, ott: %s' % (0x4009 + p, ' '.join('%02X' % b for b in data[p:p + 8])))
    break
