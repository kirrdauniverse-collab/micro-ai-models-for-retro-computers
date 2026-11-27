#!/usr/bin/env python3
"""load_diag2.py — LOAD '' a ROM saját útján: key_script + rom_run.
A hideg start után MODE=1 (K), majd SHIFT+K (LOAD token), "", NEWLINE."""
import sys
sys.path.insert(0, "/home/z/my-project/GLM/repo/tools")
from romsim import RomSim, Tape

TAPE = "/home/z/my-project/GLM/repo/dist/ZX81PICO.T81"

sim = RomSim(TAPE)
sim.rom_run(max_steps=2_500_000)
sim.w(0x4027, 1)                    # K-mód (valóság-konform)
sim.tape = Tape(sim.blocks, start_at=0)

at = sim.total + 200
def shift_key(k, at):
    sim.key_script.append((at, "press", "\x00"))
    sim.key_script.append((at, "press", k))
    sim.key_script.append((at + 600, "release", k))
    sim.key_script.append((at + 650, "release", "\x00"))

shift_key("K", at)     # LOAD token
shift_key("P", at + 1400)   # "
shift_key("P", at + 2800)   # "
sim.key_script.append((at + 4200, "press", "\n"))
sim.key_script.append((at + 4600, "release", "\n"))

n = sim.rom_run(max_steps=20_000_000)
print("rom_run: %d lépés, %s, PC=%04X" % (n, sim.stop_reason, sim.pc))
el = sim.peek16(0x4014)
print("E_LINE=%04X tartalom: %s" % (el, " ".join("%02X" % b for b in sim.ram[el:el+8])))
print("D_FILE=%04X RAMTOP=%04X CDFLAG=%02X"
      % (sim.peek16(0x400C), sim.peek16(0x4004), sim.ram[0x403B]))
scr = [s for s in sim.screen().split("\n") if s.strip()]
for s in scr[:6]:
    print("   |%s|" % s)
