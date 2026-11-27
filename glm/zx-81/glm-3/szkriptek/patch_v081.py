#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v0.8.1 javítás — a valós gyökérokok bájtszintű orvoslása.

GYÖKÉROK (a EO-debugger képernyőkép + ROM-szétszerelés bizonyította):
  A motor chat/betöltés-várakozó hurokának farokcsapdája ($7AE0):
      LD A,(CDFLAG)  ; 3A 3B 40
      AND $80        ; E6 80
      JP Z,$02A9     ; CA A9 02   ← HIBÁS ÁG: NMI-off esetén a ROM
                                   DISPLAY-4-et hívja, ami DISPLAY-5
                                   (EI + JP (HL)) útján NMI-t VÁR — de
                                   az NMI generátor ki van kapcsolva →
                                   örök hurok a WAIT-INT ($0041-$0047)
                                   körzetben (PC 'számlál, de 004x marad')
  A v0.6.5 README már ismerte a hibát a /topic úton (ki javították:
  OUT FE + DISPLAY-3), de a NORMÁL várakozó hurokban ott maradt.

JAVÍTÁS (mind a 15 blokkban, azonos $7AE0 címen):
  $7AE5: CA A9 02 (JP Z,$02A9)  →  D3 FE FB (OUT ($FE); EI)
  Ezzel NMI-off esetén a motor BEkapcsolja az NMI-generátort és
  engedi a megszakításokat, majd a meglévő OUT(FE)+DISPLAY-3 útra
  fut — pontosan a /topic-út (v0.6.5-ben bizonyítottan működő) mintájára.

BANNER-frissítés:
  'tinyllm v0.6.5' → 'tinyllm v0.8.1' (ASCII, minden blokkban; a
  hossz azonos, a motor a sztringet \r\0-nal zárja → nem érzékeny a
  tartalomra, csak a hosszra).
"""
import sys

SRC = '/home/z/my-project/download/GLM_PicoAI_v0.8.0_kazetta.T81'
DST = '/home/z/my-project/download/GLM_PicoAI_v0.8.1_kazetta.T81'

OLD_TRAP = bytes([0x3A, 0x3B, 0x40, 0xE6, 0x80, 0xCA, 0xA9, 0x02,
                  0x79, 0xED, 0x44, 0x3C, 0x08, 0xD3, 0xFE, 0xC3, 0xA4, 0x02])
NEW_BRANCH = bytes([0xD3, 0xFE, 0xFB])          # OUT ($FE); EI
OLD_BANNER = b'tinyllm v0.6.5'
NEW_BANNER = b'tinyllm v0.8.1'

raw = open(SRC, 'rb').read()
out = bytearray(raw)
pos = 4                       # EO81 mágia után
nblk = 0
trap_fixes = 0
banner_fixes = 0
while pos + 48 <= len(out):
    name = bytes(out[pos:pos + 32]).rstrip(b'\0').decode()
    ln = int(bytes(out[pos + 32:pos + 48]).rstrip(b'\0'))
    data_start = pos + 48
    data = bytes(out[data_start:data_start + ln])
    # --- farokcsapda-javítás a blokkadaton belül
    j = data.find(OLD_TRAP)
    if j < 0:
        print('HIBA: %s — farokcsapda nem található!' % name)
        sys.exit(1)
    patched = bytearray(data)
    patched[j + 5:j + 8] = NEW_BRANCH        # CA A9 02 → D3 FE FB
    trap_fixes += 1
    # --- banner-frissítés
    for _ in range(data.count(OLD_BANNER)):
        b = bytes(patched).find(OLD_BANNER)
        patched[b:b + len(OLD_BANNER)] = NEW_BANNER
        banner_fixes += 1
    out[data_start:data_start + ln] = patched
    nblk += 1
    pos = data_start + ln

open(DST, 'wb').write(bytes(out))
print('blokkok: %d, farokcsapda-javítás: %d, banner-frissítés: %d' % (nblk, trap_fixes, banner_fixes))
print('kész: %s (%d bájt)' % (DST, len(out)))
