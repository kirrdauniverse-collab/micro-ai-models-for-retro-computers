#!/usr/bin/env python3
"""Empirikus billentyű-teszt: a valódi ROM editor mit ír az E_LINE-ba
egyes billentyűkre az új (EightyOne-hű) mátrixtal."""
import sys
sys.path.insert(0, "/home/z/my-project/GLM/repo/tools")
from romsim import RomSim

TAPE = "/home/z/my-project/GLM/repo/dist/ZX81PICO.T81"


def e_line(sim):
    el = sim.peek16(0x4014)
    return " ".join("%02X" % b for b in sim.ram[el - 4:el + 24]) + \
        "  [CH_ADD=%04X STKEND=%04X]" % (sim.peek16(0x4016), sim.peek16(0x401C))


def press(sim, ch, steps=250_000):
    sim.stop_reason = None
    sim.running = True
    sim.key(ch, True)
    sim.rom_run(max_steps=steps)
    sim.key(ch, False)
    sim.rom_run(max_steps=steps)


sim = RomSim(TAPE)
sim.rom_run(max_steps=2_500_000)
print("[hideg] MODE=%02X E_LINE: %s" % (sim.ram[0x4027], e_line(sim)))

# K-mód az első billentyűnél: 'R' -> RUN token (0xF7)?
press(sim, 'R')
print("[R]     MODE=%02X E_LINE: %s" % (sim.ram[0x4027], e_line(sim)))
press(sim, 'U')
print("[U]     MODE=%02X E_LINE: %s" % (sim.ram[0x4027], e_line(sim)))
press(sim, 'J')
print("[J]     MODE=%02X E_LINE: %s" % (sim.ram[0x4027], e_line(sim)))
