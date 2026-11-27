#!/usr/bin/env python3
"""Billentyűzet-mátrix próba a VALÓDI ROM-mal: minden (félsor, bit)
esetben lefuttatjuk a ROM KEYBOARD (0x02BB) és DECODE (0x07BD) rutinját,
és kiírjuk, milyen karakterkódot ad. Cél: a szimulátor KEY_ROWS tábláját
a ROM szerint igazolni (vagy kijavítani), mert a gépelést a ROM dekódolja.
"""
import sys
sys.path.insert(0, "/home/z/my-project/GLM/repo/tools")
import romsim
from zx81sim import KEY_ROWS, ZX2ASC

RET = 0x7FFE


def call(sim, addr, limit=3000):
    sim.push(RET)
    sim.pc = addr
    for i in range(limit):
        if sim.pc == RET:
            return i
        sim.step()
    return -1


def main():
    sim = romsim.RomSim([])
    rows = [0xFE, 0xFD, 0xFB, 0xF7, 0xEF, 0xDF, 0xBF, 0x7F]
    names = {0xFE: "SHIFT Z X C V", 0xFD: "A S D F G", 0xFB: "Q W E R T",
             0xF7: "1 2 3 4 5", 0xEF: "0 9 8 7 6", 0xDF: "P O I U Y",
             0xBF: "NEWLINE L K J H", 0x7F: "SPACE . M N B"}
    print("a szimulátor jelenlegi táblája:")
    for r in rows:
        print("  %02X: %r" % (r, KEY_ROWS[r]))
    print()
    print("valódi ROM KEYBOARD (02BB) + DECODE (07BD) eredménye:")
    for r in rows:
        print("sor %02X  (EO/szim elnevezés: %s)" % (r, names[r]))
        for col in range(5):
            sim.held = {(r, col)}
            sim.a = 0x7F
            sim.b, sim.c = 0xFE, 0xFE
            sim.h, sim.l = 0xFF, 0xFF
            n1 = call(sim, 0x02BB)
            h, l = sim.h, sim.l
            # LAST-K tárolása úgy, ahogy a DISPLAY-2 teszi
            sim.w(0x4025, l)
            sim.w(0x4026, h)
            sim.b, sim.c = h, l
            n2 = call(sim, 0x07BD)
            ch = sim.ram[sim._hl()] if 0 <= sim._hl() < len(sim.ram) else -1
            carry = 1 if sim.f & 0x01 else 0
            print("  bit%d  H=%02X L=%02X  HL=%04X  kód=%02X (%s)  CY=%d  "
                  "lépés=%d/%d" % (col, h, l, sim._hl(), ch,
                                   ZX2ASC.get(ch, "?"), carry, n1, n2))
    sim.held = set()


if __name__ == "__main__":
    main()
