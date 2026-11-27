#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v0.8.1 teljes ellenőrzése:
1) 15 blokk, EO81-formátum, méretek
2) A farokcsapda-javítás minden blokkban ($7AE0)
3) A banner 'tinyllm v0.8.1' minden blokkban (RTBOOT01 kivételével)
4) A blokk-szerkezet sértetlensége: E_LINE/D_FILE/VARS/0x80/EO-vágás
5) A v0.6.5/v0.8.0 fájlhatások (md5) — a keveredés-kérdés tényekkel
"""
import hashlib
import sys

sys.path.insert(0, '/home/z/my-project/scripts')
sys.path.insert(0, '/home/z/my-project/GLM/repo/tools')
from zx81sim import load_blocks

T81 = '/home/z/my-project/download/GLM_PicoAI_v0.8.1_kazetta.T81'
TRAP = bytes([0x3A, 0x3B, 0x40, 0xE6, 0x80, 0xD3, 0xFE, 0xFB, 0x79, 0xED, 0x44, 0x3C, 0x08, 0xD3, 0xFE, 0xC3, 0xA4, 0x02])
OLD_BRANCH = bytes([0x3A, 0x3B, 0x40, 0xE6, 0x80, 0xCA, 0xA9, 0x02])

raw = open(T81, 'rb').read()
ok = True
assert raw[:4] == b'EO81', 'EO81 mágia hiányzik'
print('1) EO81 mágia: OK — méret: %d bájt' % len(raw))

blocks = load_blocks(T81)
print('2) blokkok: %d' % len(blocks))
expect = ['RTBOOT01', 'RTBASE16'] + ['RT-TUDOM', 'RT-MAGYR', 'RT-HOBBI', 'RT-EGESZ',
         'RT-MUNKA', 'RT-MUVES', 'RT-TANUL', 'RT-IRODA', 'RT-FILME', 'RT-PROGI',
         'RT-ASTRO', 'RT-ASCII', 'RT-VERSE']
names = [n.strip() for n, _ in blocks]
assert names == expect, 'blokknév-sorrend eltér: %s' % names
print('   nevek: OK —', ', '.join(names[:4]), '...')

# 3) farokcsapda + banner
for name, data in blocks:
    k = 0
    while k < len(data) and not (data[k] & 0x80):
        k += 1
    base = k + 1
    j = data.find(TRAP, base)
    j_old = data.find(OLD_BRANCH, base)
    b = data.find(b'tinyllm v0.8.1', base)
    b_old = data.find(b'tinyllm v0.6.5', base)
    t_ok = j >= 0 and j_old < 0
    if name == 'RTBOOT01':
        bn_ok = b < 0 and b_old < 0
        bn = '(nincs banner — ez a helyes)'
    else:
        bn_ok = b >= 0 and b_old < 0
        bn = '@$%04X' % (0x4009 + b - base) if b >= 0 else '??'
    st = 'OK' if t_ok and bn_ok else 'HIBA'
    if st == 'HIBA':
        ok = False
    print('   %-10s csapda %s  banner %s  %s' % (
        name, '@$%04X' % (0x4009 + j - base) if j >= 0 else '??', bn, st))

# 4) szerkezet: E_LINE, VARS-vég 0x80, utolsó bájt 0x80
for name, data in blocks:
    k = 0
    while k < len(data) and not (data[k] & 0x80):
        k += 1
    base = k + 1
    sv = data[base:base + 0x74]
    def le16(o): return sv[o] | (sv[o + 1] << 8)
    eline = le16(0x4014 - 0x4009)
    dfile = le16(0x400C - 0x4009)
    calc = 0x4009 + len(data) - base
    last = data[-1]
    okk = eline == calc and dfile == 0x7B00 and last == 0x80
    if not okk:
        ok = False
    print('   %-10s E_LINE=$%04X (várt $%04X) D_FILE=$%04X záró=%02X %s' % (
        name, eline, calc, dfile, last, 'OK' if okk else 'HIBA'))

# 5) md5-különbségek
print('5) md5 (a keveredés-kérdés tényes alapja):')
for f in ('GLM_PicoAI_v0.6.5_kazetta.T81', 'GLM_PicoAI_v0.8.0_kazetta.T81',
          'GLM_PicoAI_v0.8.1_kazetta.T81'):
    p = '/home/z/my-project/download/' + f
    h = hashlib.md5(open(p, 'rb').read()).hexdigest()
    print('   %s  %s' % (h, f))

print()
print('ÖSSZEGZÉS: %s' % ('MINDEN OK' if ok else 'HIBA VAN!'))
sys.exit(0 if ok else 1)
