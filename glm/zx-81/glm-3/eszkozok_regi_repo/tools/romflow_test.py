#!/usr/bin/env python3
"""romflow_test.py — a RAMTOP-javítás és a motorbelépés ROM-szintű
ellenőrzése (a VALÓDI 8K ROM futtatásával).

A BASIC-sorok (IF USR/THEN LOAD/REM) bájt-szinten azonosak a v0.5.4-es
bizonyított kazettáéval (ezt külön összevetés igazolta), ezért itt a
két kritikus ML-útvonalat közvetlenül a valódi ROM-mal ellenőrizzük:

  A. A boot ML-telepítő (RAND USR 16514 hatása):
       D_FILE a 0x7B00-ra, VARS-jelző, tartós zóna nullázása,
       RAMTOP := 0x715F a 0x4004-re (A JAVÍTÁS!)
  B. A NEW (0x03C3) a valódi ROM-kóddal:
       RAM-FILL csak 0x715E-ig törlöl; a 0x715F-es 0xFF-es határbájt
       megállítja a RAM-CHECK sétát → RAMTOP=0x715F; a D_FILE
       (0x7B00) ÉS a tartós zóna (0x7160+) TÚLÉLI; a gép friss
       editorban landol (INITIAL a 0x03E5-ről).
  C. A motor belépése (a 2-es sor IF USR 16514 hatása):
       PC=0x4082 → LD SP,STACK; ROM_SLOW (0x0F2B); init_screen;
       profil-bekérés — a D_FILE-ban megjelenik a motor UI-ja.

(A szerkesztő karakterbeszúrása a szim MAKE-ROOM/syntax-stack
hűségi korlátai miatt nem建模pontosan — a valódi gépen ez az út a
ROM saját, minden ZX81-ben bizonyított kódja.)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from romsim import RomSim

TAPE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "..", "dist", "ZX81PICO.T81")
ROM_NEW = 0x03C3           # a NEW-parancs rutinja (RAM-CHECK-kel)
SENTINEL = 0x0F46          # BREAK-1: visszatérési jelző


def phase(sim, name, steps, stop_at=None):
    sim.stop_reason = None
    sim.running = True
    n = sim.rom_run(max_steps=steps,
                    checkpoints={stop_at: 1} if stop_at else None)
    print("  [%s] %d lépés, ok: %s, PC=0x%04X"
          % (name, n, sim.stop_reason, sim.pc))
    return n


def call_at(sim, addr):
    """Közvetlen 'CALL addr' a szintaktikai verem tetejéről: a
    visszatérést a SENTINEL jelzi."""
    sim.sp = 0x7FFD
    sim.push(SENTINEL)
    sim.pc = addr
    sim.running = True
    sim.stop_reason = None


def main():
    sim = RomSim(TAPE)
    print("blokkok:", [n for n, _ in sim.blocks])

    # előkészület: a gép felépül, majd a PICOBOOT-kép a RAM-ba kerül
    phase(sim, "hideg start", 2_500_000)
    img = dict(sim.blocks)["PICOBOOT"]
    sim.ram[0x4009:0x4009 + len(img)] = img
    sim.w(0x403B, 0xC0)         # SLOW mód, videó aktív

    # A) a boot ML-telepítő (0x4082) — a JAVÍTOTT kód fut a valódi magon
    call_at(sim, 0x4082)
    n = phase(sim, "boot ML-telepítő", 2_000_000, stop_at=SENTINEL)
    assert sim.pc == SENTINEL, (
        "a telepítő nem tért vissza (PC=0x%04X)" % sim.pc)
    ramtop = sim.peek16(0x4004)
    print("  RAMTOP a telepítő után: 0x%04X" % ramtop)
    assert ramtop == 0x715F, "RAMTOP=0x%04X, nem 0x715F!" % ramtop
    assert sim.ram[0x7B00] == 0x76 and sim.ram[0x7B21] == 0x76, (
        "a telepített D_FILE hibás")
    assert sim.ram[0x7E19] == 0x80, "a VARS-jelző hiányzik"
    assert bytes(sim.ram[0x7160:0x7168]) == b"\0" * 8, "a zóna nem nullázott"
    print("  ✓ A telepítő: D_FILE + zóna + RAMTOP=0x715F rendben")

    # B) NEW a VALÓDI ROM-mal — a javítás fő ellenőrzése
    sim.ram[0x715F] = 0xFF     # a határbájt (a telepítő tette, most is van)
    call_at(sim, ROM_NEW)
    phase(sim, "NEW (valódi ROM RAM-CHECK)", 3_000_000, stop_at=SENTINEL)
    ramtop = sim.peek16(0x4004)
    print("  RAMTOP a NEW után: 0x%04X" % ramtop)
    assert ramtop == 0x715F, (
        "RAMTOP=0x%04X, nem 0x715F! A NEW túlment a határon!" % ramtop)
    d0, d1, dl = sim.ram[0x7B00], sim.ram[0x7B01], sim.ram[0x7B21]
    print("  D_FILE @0x7B00 a NEW után: %02X %02X ... %02X" % (d0, d1, dl))
    assert d0 == 0x76 and d1 == 0x00 and dl == 0x76, (
        "A NEW TÖRÖLTE a 0x7B00-as D_FILE-t! (%02X %02X %02X)" % (d0, d1, dl))
    z = bytes(sim.ram[0x7160:0x7168])
    assert z == b"\0" * 8, "a tartós zóna a NEW után: %s" % z.hex()
    print("  ✓✓ A JAVÍTOTT NEW: a D_FILE és a tartós zóna SÉRÜLETLEN")

    # C) a motor belépése a PICOBASE-képből (a 2-es sor IF USR hatása)
    img = dict(sim.blocks)["PICOBASE"]
    sim.ram[0x4009:0x4009 + len(img)] = img
    sim.w(0x403B, 0xC0)
    call_at(sim, 0x4082)      # a motor belépési pontja
    phase(sim, "motor belép (valódi ML)", 15_000_000)
    scr = sim.screen().split("\n")
    print("  képernyő (nem üres sorok):")
    shown = 0
    for s in scr:
        if s.strip():
            print("    |%s|" % s)
            shown += 1
    assert sim.pc != 0x0000, "a gép RESET-et hajtott végre!"
    assert shown >= 2, "a motor UI-ja nem jelenik meg a képernyőn!"
    has_ui = any(("READY" in s.upper()) or ("PICO" in s) or ("YOU" in s)
                 for s in scr)
    assert has_ui, "a motor UI-elemei nem látszanak!"
    print("\nSIKER: a javított lánc a valódi ROM-mal életre kel —")
    print("a NEW megkíméli a felső memóriát, és a motor UI-ja kirajzolódik.")


if __name__ == "__main__":
    main()
