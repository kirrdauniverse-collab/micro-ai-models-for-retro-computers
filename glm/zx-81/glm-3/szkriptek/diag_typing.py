#!/usr/bin/env python3
"""Diagnosztika: valódi ROM + begépelés. Mit csinál a szerkesztő egy 'R' lenyomásra?"""
import os, sys
sys.path.insert(0, "/home/z/my-project/GLM/repo/tools")
from romsim import RomSim

TAPE = "/home/z/my-project/GLM/repo/dist/ZX81PICO.T81"

def dump(sim, tag):
    print("[%s] PC=0x%04X SP=0x%04X CDFLAG=0x%02X MODE=0x%02X LASTK=%02X/%02X "
          "E_LINE=0x%04X DF_SZ=%02X D_FILE=0x%04X RAMTOP=0x%04X"
          % (tag, sim.pc, sim.sp, sim.ram[0x403B], sim.ram[0x4027],
             sim.ram[0x4025], sim.ram[0x4026],
             sim.peek16(0x4014), sim.ram[0x4022], sim.peek16(0x400C),
             sim.peek16(0x4004)))
    el = sim.peek16(0x4014)
    print("   E_LINE tartalma:", " ".join("%02X" % b for b in sim.ram[el:el+16]))
    scr = sim.screen().split("\n")
    nz = [s for s in scr if s.strip()]
    print("   képernyő nem-üres sorai:", nz[:4] if nz else "(üres)")

sim = RomSim(TAPE)
sim.rom_run(max_steps=2_500_000)
dump(sim, "hideg start")

# 'R' lenyomása tartósan
sim.stop_reason = None
sim.running = True
sim.key('R', True)
n = sim.rom_run(max_steps=300_000)
sim.key('R', False)
dump(sim, "R lenyomva 300e lépésig")

n = sim.rom_run(max_steps=1_500_000)
dump(sim, "R elengedve +1.5M")
