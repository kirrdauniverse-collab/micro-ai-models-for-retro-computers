#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""motor_reelemzes_17.py — 17. menet: a v0.6.5 ALAPFÁJL $7AE0-s farokcsapda-
családjának teljes statikus re-elemzése, v0.9.2-vel összevetve.

(ATADASI_DOKUMENTUM.md 7. fejezet 1. pontjának statikus fele; az élő EO-
utasítás-követés törzsadatait ez a jelentés adja meg.)

Hozam:
  A) mindkét kazetta blokklistája
  B) $7AE0-$7AE5 oktett minden blokkban (a csapdacsalád egyedisége)
  C) $7A40-$7B00 disassembly (RTBOOT01 + RTBASE16, mindkét verzió) — a
     motor ROM-klón display-berendezése
  D) blokkonkénti bájt-eltérés v0.6.5 vs v0.9.2, címekkel
  E) a hiteles ZX81 ROM (refs/zx81.rom) bájt-pontos disassembly-ja
     $0290-$02C0 (DISPLAY-3/4/5) + $0030-$0050 (INT-restart/WAIT-INT)
  F) hivatkozás-keresés: ki hívja a $7A40-et és a $7ADA-t, hol a JP (IX)

Futtatás: python3 szkriptek/motor_reelemzes_17.py  (a munkaterület gyökeréblől)
Környezetfüggő útvonalak: nincsenek — minden útvonal a saját helyéhez
(__file__) képződik.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.dirname(HERE)                       # glm/zx-81/glm-3/
sys.path.insert(0, HERE)
from z80dis import disasm_full

V065 = os.path.join(WS, 'kazettak/GLM_PicoAI_v0.6.5_kazetta.T81')
V092 = os.path.join(WS, 'kazettak/GLM_PicoAI_v0.9.2_kazetta.T81')
ROM = os.path.join(WS, 'refs/zx81.rom')

LO, HI = 0x7A40, 0x7B00


def load_blocks(path):
    raw = open(path, 'rb').read()
    assert raw[:4] == b'EO81', 'hiányzó EO81 mágia!'
    pos, blocks = 4, []
    while pos + 48 <= len(raw):
        name = raw[pos:pos + 32].rstrip(b'\0').decode('latin2')
        ln = int(raw[pos + 32:pos + 48].rstrip(b'\0'))
        blocks.append((name, raw[pos + 48:pos + ln + 48]))
        pos += 48 + ln
    return blocks


def a2ram(off):
    """Kép-offset -> RAM-cím. Az első 8 bájt a ZX81-név; a RAM-kép $4009-től."""
    return 0x4009 + (off - 8) if off >= 8 else None


def ram2off(addr):
    return 8 + (addr - 0x4009)


def disasm_window(data, lo, hi, title):
    print(f'== {title}: ${lo:04X}-${hi:04X} ==')
    p = ram2off(lo)
    end = ram2off(hi)
    while p < end and p < len(data) - 4:
        t, ln, npc = disasm_full(data, p)
        h = ' '.join(f'{data[q]:02X}' for q in range(p, min(npc, end)))
        print(f'  {a2ram(p):04X}: {h:<11} {t}')
        p = npc
    print()


def main():
    b65 = load_blocks(V065)
    b92 = load_blocks(V092)
    print('== A) blokklista ==')
    print(f'v0.6.5: {len(b65)} blokk: {[n for n, _ in b65]}')
    print(f'v0.9.2: {len(b92)} blokk: {[n for n, _ in b92]}')
    assert [n for n, _ in b65] == [n for n, _ in b92]

    print()
    print('== B) $7AE0-$7AE5 oktett minden blokkban ==')
    print(f'{"blokk":10}  v0.6.5                     v0.9.2')
    for (n1, d1), (_, d2) in zip(b65, b92):
        o = ram2off(0x7AE0)
        h1 = ' '.join(f'{x:02X}' for x in d1[o:o + 6])
        h2 = ' '.join(f'{x:02X}' for x in d2[o:o + 6])
        print(f'{n1:10}  {h1:24}  {h2}')

    for target in ('RTBOOT01', 'RTBASE16'):
        print()
        d65 = dict(b65)[target]
        d92 = dict(b92)[target]
        disasm_window(d65, LO, HI, f'v0.6.5 {target}')
        disasm_window(d92, LO, HI, f'v0.9.2 {target}')

    print('== D) blokkonkénti bájt-eltérés v0.6.5 -> v0.9.2 ==')
    for (n, d1), (_, d2) in zip(b65, b92):
        diffs = [i for i in range(min(len(d1), len(d2))) if d1[i] != d2[i]]
        if not diffs:
            print(f'{n:10}: AZONOS ({len(d1)} B)')
            continue
        regions, start, prev = [], diffs[0], diffs[0]
        for i in diffs[1:]:
            if i - prev > 8:
                regions.append((start, prev))
                start = i
            prev = i
        regions.append((start, prev))
        regs = ', '.join(
            f'${a2ram(x):04X}..${a2ram(y):04X}' for x, y in regions[:12])
        print(f'{n:10}: {len(diffs)} B eltér, régiók: {regs}')

    rom = open(ROM, 'rb').read()
    print()
    print('== E) ZX81 ROM bájt-pontos disassembly ==')
    p = 0x0290
    while p < 0x02C0:
        t, ln, npc = disasm_full(rom, p)
        h = ' '.join(f'{rom[q]:02X}' for q in range(p, min(npc, 0x02C0)))
        print(f'  {p:04X}: {h:<11} {t}')
        p = npc
    print()
    p = 0x0030
    while p < 0x0050:
        t, ln, npc = disasm_full(rom, p)
        h = ' '.join(f'{rom[q]:02X}' for q in range(p, min(npc, 0x0050)))
        print(f'  {p:04X}: {h:<11} {t}')
        p = npc

    print()
    print('== F) hivatkozások ==')
    targets = {0x7A40: 'CALL/JP $7A40', 0x7A60: 'JP $7A60',
               0x7AC9: 'LD IX/JP $7AC9', 0x7ADA: 'CALL/JP $7ADA'}
    for tag, blocks in (('v0.6.5', b65), ('v0.9.2', b92)):
        print(f'-- {tag} --')
        for n, data in blocks:
            if n not in ('RTBOOT01', 'RTBASE16'):
                continue
            found = []
            for i in range(8, len(data) - 2):
                ra = a2ram(i)
                if ra is not None and 0x7A40 <= ra <= 0x7AF4:
                    continue  # a régió önhivatkozásai (ismertek)
                lo, hi = data[i + 1], data[i + 2]
                tgt = lo | (hi << 8)
                if tgt in targets and data[i] in (0x21, 0xCD, 0xC3, 0x2A, 0x22, 0x11, 0x01):
                    found.append((ra, data[i], tgt))
                elif tgt in targets and data[i] == 0xDD and data[i + 1] == 0x21:
                    found.append((ra, 0xDD21, tgt))
            print(f'  {n}: ' + ('; '.join(
                f'@${ra:04X} op{op:02X}->${tgt:04X}' for ra, op, tgt in found)
                or 'nincs'))
        d = dict(blocks)['RTBASE16']
        nix = sum(1 for i in range(8, len(d) - 1)
                  if d[i] == 0xDD and d[i + 1] == 0xE9)
        print(f'  RTBASE16 JP (IX) (DD E9) darabszám: {nix}')


if __name__ == '__main__':
    main()
