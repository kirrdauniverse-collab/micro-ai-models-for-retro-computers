#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RTBASE16 teljes szerkezeti elemzés:
- T81 blokkfejléc: ZX81-név (utolsó betű 7-es bittel) + 'fejléc' (0x74 bájt)
- utána: D_FILE (25×0x76) + BASIC program + VARS + 0x80 vége
- a gépikód (USR 16514 = $4082) a REM-ben, a $4082-től indul
- OUT ($FD)/(FE) keresése a blokkban: NMI ki/be (a PC=$0044 csapda oka)
"""
import sys
sys.path.insert(0, '/home/z/my-project/scripts')
from z80dis import block as dis_block

TOK = {
    0xD3: 'PEEK', 0xD4: 'USR', 0xDE: 'THEN', 0xDF: 'TO', 0xE4: 'SLOW', 0xE5: 'FAST',
    0xE6: 'NEW', 0xEA: 'REM', 0xEB: 'FOR', 0xEC: 'GOTO', 0xED: 'GOSUB', 0xEE: 'INPUT',
    0xEF: 'LOAD', 0xF0: 'LIST', 0xF1: 'LET', 0xF2: 'PAUSE', 0xF3: 'NEXT', 0xF4: 'POKE',
    0xF5: 'PRINT', 0xF6: 'PLOT', 0xF7: 'RUN', 0xF8: 'SAVE', 0xF9: 'RAND', 0xFA: 'IF',
    0xFB: 'CLS', 0xFD: 'RETURN', 0xFE: 'COPY', 0xFF: 'CLEAR',
}


def detok(b):
    out = []
    for c in b:
        if c in TOK: out.append(' ' + TOK[c])
        elif 0x20 <= c < 0x7F: out.append(chr(c))
        elif c == 0x76: out.append('⏎')
        else: out.append('<%02X>' % c)
    return ''.join(out)


path = '/home/z/my-project/download/GLM_PicoAI_v0.8.0_kazetta.T81'
raw = open(path, 'rb').read()

# T81 formátum: 8 bájtos rekordok: type, len lo, len hi, 5×0xFF? — megnézzük nyersen
print('T81 fejléc (első 32 bájt):', ' '.join('%02X' % b for b in raw[:32]))
print('méret:', len(raw))

# zx81sim load_blocks használata inkább:
sys.path.insert(0, '/home/z/my-project/GLM/repo/tools')
from zx81sim import load_blocks
blocks = load_blocks(path)
for name, data in blocks:
    if name != 'RTBASE16':
        continue
    print('\n=== RTBASE16 (%d bájt) ===' % len(data))
    # A név a blokk elején: pl. "79'&8*" — ezek az elsők
    k = 0
    while k < len(data) and not (data[k] & 0x80):
        k += 1
    print('név-bájtok: %d (0..%d), utolsó: %02X' % (k, k, data[k] if k < len(data) else -1))
    base = k + 1
    print('adat a név után @%04X ($%04X-től betöltésre)' % (base, 0x4009 + base))

    # Rendszerváltozó terület (0x74 = $4009..$407C) a base-től:
    sv = data[base:base + 0x74]
    def le16(o): return sv[o] | (sv[o + 1] << 8)
    print('sysvars $4009..$407C:')
    print('  D_FILE = $%04X' % le16(0x400C - 0x4009))
    print('  VARS   = $%04X' % le16(0x4010 - 0x4009))
    print('  E_LINE = $%04X' % le16(0x4014 - 0x4009))
    print('  CH_ADD = $%04X' % le16(0x4016 - 0x4009))
    print('  ERR_SP = $%04X' % le16(0x4012 - 0x4009))
    print('  RAMTOP = $%04X' % le16(0x4026 - 0x4009))

    prog = base + 0x74
    print('\nBASIC program @ $%04X, első bájtok: %s' % (
        0x4009 + prog, ' '.join('%02X' % b for b in data[prog:prog + 16])))
    # BASIC sorok:
    p = prog
    lineno = 1
    while p + 4 <= len(data) and data[p] != 0x80:
        n = (data[p] << 8) | data[p + 1]
        ll = (data[p + 2] << 8) | data[p + 3]
        if ll == 0 or p + 4 + ll > len(data):
            print('érvénytelen sor @%04X' % p)
            break
        body = data[p + 4:p + 4 + ll]
        print('$%04X sor %5d (%d B): %s' % (0x4009 + p, n, ll, detok(body)[:180]))
        p += 4 + ll
    print('program vége @ $%04X; VARS-tól: %s' % (0x4009 + p,
          ' '.join('%02X' % b for b in data[p:p + 12])))

    # OUT FD/FE és az usa-lánc keresése a REM-gépikódban:
    print('\n--- OUT ($FD) [NMI KI] és OUT ($FE) [NMI BE] előfordulásai ---')
    cnt_fd = 0
    for i in range(base, len(data) - 1):
        if data[i] == 0xD3 and data[i + 1] in (0xFD, 0xFE):
            print('@$%04X: OUT ($%02X)' % (0x4009 + i, data[i + 1]))
            cnt_fd += 1
    print('összesen OUT port-FD/FE:', cnt_fd)

    # $4082 (USR 16514) belépő kód:
    off = 0x4082 - 0x4009
    print('\n--- gépikód belépés $4082 (USR 16514) — első 40 utasítás ---')
    print(dis_block(data, off, off + 120))
    break
