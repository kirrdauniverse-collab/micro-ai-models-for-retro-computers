#!/usr/bin/env python3
"""K-mód billentyű->token térkép empirikus felmérése a valódi ROM-mal."""
import sys
sys.path.insert(0, "/home/z/my-project/GLM/repo/tools")
from romsim import RomSim

TAPE = "/home/z/my-project/GLM/repo/dist/ZX81PICO.T81"
sim = RomSim(TAPE)
sim.rom_run(max_steps=2_500_000)

def press(ch, steps=250_000):
    sim.stop_reason = None
    sim.running = True
    sim.key(ch, True)
    sim.rom_run(max_steps=steps)
    sim.key(ch, False)
    sim.rom_run(max_steps=steps)

def rub(steps=300_000):
    sim.key("\x00", True)
    sim.key("0", True)
    sim.rom_run(max_steps=steps)
    sim.key("\x00", False)
    sim.key("0", False)
    sim.rom_run(max_steps=steps)

def tok():
    el = sim.peek16(0x4014)
    return sim.ram[el]

out = {}
for ch in "QWERTASDFGZXCVYUIOPHJKL NMB.":
    press(ch)
    t = tok()
    out[ch] = t
    rub()

print("K-mód: gomb -> token (a szó-tábla alapján):")
names = {0xF0: "LOAD", 0xF8: "RUN", 0xF9: "SAVE", 0xFA: "RAND", 0xD5: "USR",
         0xFB: "IF", 0xDF: "THEN", 0xF6: "PRINT", 0xEB: "REM", 0xEF: "INPUT",
         0xE7: "NEW", 0xF1: "LIST", 0xF2: "LET", 0xEE: "GOSUB", 0xED: "GOTO",
         0xE2: "LPRINT", 0xE3: "LLIST", 0xE4: "STOP", 0xE5: "SLOW",
         0xE6: "FAST", 0xE8: "SCROLL", 0xE9: "CONT", 0xEA: "DIM",
         0xEC: "FOR", 0xF3: "PAUSE", 0xF4: "NEXT", 0xF5: "POKE",
         0xF7: "PLOT", 0xFC: "CLS", 0xFD: "UNPLOT", 0xFE: "CLEAR",
         0xFF: "RETURN"}
for ch, t in out.items():
    print("  '%s' -> %02X (%s)" % (ch, t, names.get(t, "?")))
