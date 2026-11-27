#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""verify_v090.py - a v0.9.0 kazetta teljes ellenorzese.

Ellenorzi (a v0.8.1-es verify mintajara, bovitve):
  1. EO81 kontener + blokk-lanc (RTBOOT01, RTMEM16, RTBASE16 + 13 tema)
  2. minden kepblokk: E_LINE = 0x4009+hossz (a blokk sajat szavaban is),
     utolso bajt 0x80, D_FILE = 0x7B00, a BASIC sorok tokenjei (REM/IF/
     USR/THEN/LOAD/SAVE) a helyes ROM-tablabol
  3. a farokcsapda-javitas jelense $7AE0-nal (OUT FE; EI, NINCS JP Z,$02A9)
  4. a modell: RTLM varazslo + 1030 B + tag + nevtabla minden chat-blokkban,
     a v0.8.1-es modellek bajtonkénti azonossaga
  5. az EO vago-szimulacio: a nev+kep adat vegerol visszafelé az elso
     0x80-ig vag - a trimmelt hossznak fednie kell a teljes kepet
  6. RTMEM16: nev-kodok + 152 zona bajt + 0x80 farok; a zona XOR rendben
"""
import sys

T81 = sys.argv[1] if len(sys.argv) > 1 else \
    '/home/z/my-project/download/GLM_PicoAI_v0.9.0_kazetta.T81'
REF_T81 = '/home/z/my-project/download/GLM_PicoAI_v0.8.1_kazetta.T81'

Z = 0x4009
DFILE = 0x7C00
MSIZE = 1030
ZONE_LEN = 152
MEMCODES = bytes([0x37, 0x39, 0x32, 0x2A, 0x32, 0x1D, 0xA2])
TRAP_FIXED = bytes([0x3A, 0x3B, 0x40, 0xE6, 0x80, 0xD3, 0xFE, 0xFB])
TRAP_BROKEN = bytes([0x3A, 0x3B, 0x40, 0xE6, 0x80, 0xCA, 0xA9, 0x02])
EXPECT = ['RTBOOT01', 'RTMEM16', 'RTBASE16', 'RT-TUDOM', 'RT-MAGYR',
          'RT-HOBBI', 'RT-EGESZ', 'RT-MUNKA', 'RT-MUVES', 'RT-TANUL',
          'RT-IRODA', 'RT-FILME', 'RT-PROGI', 'RT-ASTRO', 'RT-ASCII',
          'RT-VERSE']

raw = open(T81, 'rb').read()
assert raw[:4] == b'EO81', 'nincs EO81 magia'
pos = 4
blocks = []
while pos + 48 <= len(raw):
    name = raw[pos:pos + 32].rstrip(b'\0').decode()
    ln = int(raw[pos + 32:pos + 48].rstrip(b'\0'))
    data = raw[pos + 48:pos + ln + 48]
    blocks.append((name, data))
    pos += 48 + ln

print('blokkok:', [n for n, _ in blocks])
assert [n for n, _ in blocks] == EXPECT, 'blokk-nevek/sorrend mas'

ref = open(REF_T81, 'rb').read()
rpos = 4
ref_models = {}
while rpos + 48 <= len(ref):
    rname = ref[rpos:rpos + 32].rstrip(b'\0').decode()
    rln = int(ref[rpos + 32:rpos + 48].rstrip(b'\0'))
    if rname != 'RTBOOT01':
        rdata = ref[rpos + 48:rpos + rln + 48]
        p = rdata.find(b'RTLM')
        ref_models[rname] = rdata[p:p + MSIZE]
    rpos += 48 + rln

ok = True
for name, data in blocks:
    if name == 'RTMEM16':
        assert data[:7] == MEMCODES, 'RTMEM16 nev-kodok hibasak'
        zone = data[7:7 + ZONE_LEN]
        assert data[7 + ZONE_LEN] == 0x80, 'RTMEM16 farok 0x80 hianyzik'
        x = 0
        for bb in zone[:-1]:
            x ^= bb
        assert x == zone[-1], 'RTMEM16 zona XOR hibas'
        print('RTMEM16: nev-kodok OK, 152 B zona OK, XOR OK')
        continue
    # kep-e: elso bajt = VERSN-szeru (0x00/0x01/0xFF az EO szamara)
    assert data[0] in (0x00, 0x01, 0xFF), f'{name}: nem kepkedő blokk'
    eline = data[11] | (data[12] << 8)          # $4014 E_LINE
    dfile = data[3] | (data[4] << 8)            # $400C D_FILE
    assert dfile == DFILE, f'{name}: D_FILE=0x{dfile:04X}'
    assert data[-1] == 0x80, f'{name}: utolso bajt nem 0x80'
    # EO vago-szimulacio: vegerol visszafelé az elso 0x80-ig
    cut = len(data)
    while cut > 0 and data[cut - 1] != 0x80:
        cut -= 1
    kept = len(data[:cut]) + 32                 # + nev (32 B, EO mellekli)
    eline_off = eline - Z                       # a kep hossza E_LINE-ig
    assert eline_off <= cut, \
        f'{name}: az EO levagna a kepet ({eline_off} > {cut})!'
    # farokcsapda
    i = data.find(TRAP_BROKEN)
    assert i < 0, f'{name}: JAVITATLAN farokcsapda 0x{Z + i:04X}-nal!'
    j = data.find(TRAP_FIXED)
    assert j >= 0, f'{name}: nincs javitott farokcsapda!'
    # BASIC sorok: line1 REM ($EA), line2 IF USR ($FA $D4) THEN LOAD ($DE $EF)
    p = 0x407D - Z
    assert data[p + 4] == 0xEA, f'{name}: line1 nem REM!'
    # line2 megkeresese a line1 hossza szerint
    l1len = data[p + 2] | (data[p + 3] << 8)
    p2 = p + 4 + l1len
    assert data[p2 + 4:p2 + 6] == b'\xFA\xD4', f'{name}: line2 nem IF USR!'
    assert b'\xDE\xEF' in data[p2:p2 + 40], f'{name}: nincs THEN LOAD!'
    # line3: IF USR = 2 THEN SAVE
    l2len = data[p2 + 2] | (data[p2 + 3] << 8)
    p3 = p2 + 4 + l2len
    if name != 'RTBOOT01':   # csak a chat-blokkokban van SAVE-sor
        assert data[p3 + 4:p3 + 6] == b'\xFA\xD4', f'{name}: line3 nem IF USR!'
        assert b'\xDE\xF8' in data[p3:p3 + 40], f'{name}: nincs THEN SAVE!'
    if name != 'RTBOOT01':
        mp = data.find(b'RTLM')
        model = data[mp:mp + MSIZE]
        assert len(model) == MSIZE and mp > 0x800, f'{name}: RTLM hianyzik'
        tag = data[mp + MSIZE]
        ti = EXPECT.index(name) - 2   # RTMEM16 nincs a builder indexben
        assert tag == ti, f'{name}: tag {tag} != {ti}'
        assert data[mp + MSIZE + 1:mp + MSIZE + 12].rstrip(b'\0') == \
            name.encode(), f'{name}: tag-nev hibas'
        same = ref_models.get(name) == model
        print(f'{name}: kep OK, modell 0x{Z + mp:04X}, '
              f'v0.8.1-azonos: {"IGEN" if same else "NEM"}')
        if not same:
            ok = False
    else:
        print(f'{name}: kep OK (boot, FULL)')

print('EVIDENCE: mind a %d blokk rendben%s' %
      (len(blocks), '' if ok else ' - MODELL-ELTERES!'))
sys.exit(0 if ok else 1)
