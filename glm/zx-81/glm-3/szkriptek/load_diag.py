#!/usr/bin/env python3
"""load_diag.py — a LOAD '' begépelése utáni ROM-út nyomkövetése.
Megnézzük: eljut-e a NEXT-PROG/IN-BYTE ciklusba, vagy el sem indul?"""
import sys
sys.path.insert(0, "/home/z/my-project/GLM/repo/tools")
from romsim import RomSim, Tape

TAPE = "/home/z/my-project/GLM/repo/dist/ZX81PICO.T81"

sim = RomSim(TAPE)
sim.rom_run(max_steps=2_500_000)
sim.tape = Tape(sim.blocks, start_at=0)

def shift_key(k, at):
    sim.key_script.append((at, "press", "\x00"))
    sim.key_script.append((at, "press", k))
    sim.key_script.append((at + 400, "release", k))
    sim.key_script.append((at + 450, "release", "\x00"))

# SHIFT+K lenyomása TARTÓSAN + MODE=1 (K-mód) a valóság szerint:
sim.w(0x4027, 1)
sim.key('\x00', True)   # SHIFT
sim.key('K', True)
print('LAST-K most: %02X,%02X  MODE=%02X'
      % (sim.ram[0x4025], sim.ram[0x4026], sim.ram[0x4027]))

log = []
n = 0
hit_load = False
while n < 8_000_000:
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
    # a LOAD-ut útjának megfigyelése
    if 0x0340 <= pc <= 0x03A6 or pc in (0x0D9A,):
        hit_load = True
    if hit_load:
        log.append((pc, "A=%02X B=%02X C=%02X D=%02X E=%02X HL=%04X"
                    % (sim.a, sim.b, sim.c, sim.d, sim.e, sim._hl())))
        if len(log) > 300:
            log.pop(0)
    sim.step()
    sim.total += 1
    n += 1
    sim._apply_key_script()   # a key_script elemeinek alkalmazása!
    # a betöltés befejeződhetett: elérte a szerkesztőt újra
    if hit_load and pc == 0x04CF:
        break

print("LOAD út érintve:", hit_load)
for i, (pc, regs) in enumerate(log[:60]):
    print("%3d PC=%04X %s" % (i, pc, regs))
print("... (összesen %d bejegyzés)" % len(log))
for i, (pc, regs) in enumerate(log[-30:]):
    print("%3d PC=%04X %s" % (len(log) - 30 + i, pc, regs))
el = sim.peek16(0x4014)
print("E_LINE=%04X D_FILE=%04X RAMTOP=%04X"
      % (el, sim.peek16(0x400C), sim.peek16(0x4004)))
print("E_LINE tartalma:", " ".join("%02X" % b for b in sim.ram[el:el + 20]))
