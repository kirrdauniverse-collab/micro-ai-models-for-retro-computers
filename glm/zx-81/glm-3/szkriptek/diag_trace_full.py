#!/usr/bin/env python3
"""Teljes utasításkövetés: az 'R' billentyűtől a szerkesztő útján.
Minden lépés PC-je + regiszterek, a SLOW-DISP-től 400 utasításig."""
import sys
sys.path.insert(0, "/home/z/my-project/GLM/repo/tools")
from romsim import RomSim

TAPE = "/home/z/my-project/GLM/repo/dist/ZX81PICO.T81"

sim = RomSim(TAPE)
sim.rom_run(max_steps=2_500_000)
sim.stop_reason = None
sim.running = True

sim.key('R', True)
log = []
n = 0
started = False
while n < 600_000 and len(log) < 420:
    if not sim.halted and n % 26 == 0 and (sim.ram[0x403B] & 0x80):
        sim._quick_nmi()
    if sim.halted:
        sim.nmi_countdown -= 1
        if sim.nmi_countdown <= 0:
            sim.nmi_countdown = 26
            sim._quick_nmi()
        sim.total += 1
        n += 1
        continue
    pc = sim.pc
    if pc == 0x04CF:
        started = True          # SLOW-DISP: itt vár a billentyűre
    if started:
        log.append((pc, "A=%02X B=%02X C=%02X D=%02X E=%02X HL=%04X SP=%04X IY=%04X"
                    % (sim.a, sim.b, sim.c, sim.d, sim.e, sim._hl(), sim.sp,
                       (sim.iyl | (sim.iyh << 8)) if hasattr(sim, 'iyl') else -1)))
    sim.step()
    sim.total += 1
    n += 1
    # a BACK-NEXT-nél (0523) álljunk meg: a gombfeldolgozás kész
    if started and pc == 0x0523:
        break

for i, (pc, regs) in enumerate(log):
    print("%3d PC=%04X %s" % (i, pc, regs))
el = sim.peek16(0x4014)
print("E_LINE (%04X):" % el,
      " ".join("%02X" % b for b in sim.ram[el:el + 10]))
print("MODE(0x4006)=%02X  DEBOUNCE(0x4027)=%02X" % (sim.ram[0x4006], sim.ram[0x4027]))
print("DF_SZ=%02X D_FILE=%04X VARS=%04X STKEND=%04X"
      % (sim.ram[0x4022], sim.peek16(0x400C), sim.peek16(0x4010),
         sim.peek16(0x401C)))
