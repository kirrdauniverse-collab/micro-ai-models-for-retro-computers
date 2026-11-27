#!/usr/bin/env python3
"""Az R-billentyű feldolgozásának nyomkövetése a valódi ROM editor-útvonalán.
Cél: hol akad el (DECODE? MODE-SORT? ADD-CHAR/MAKE-ROOM?)"""
import sys
sys.path.insert(0, "/home/z/my-project/GLM/repo/tools")
from romsim import RomSim
from zx81sim import F_C

TAPE = "/home/z/my-project/GLM/repo/dist/ZX81PICO.T81"

sim = RomSim(TAPE)
sim.rom_run(max_steps=2_500_000)          # hideg start, editor vár
sim.stop_reason = None
sim.running = True

# régiók amik érdekelnek
REG = [
    (0x04CF, 0x0540, "EDITOR kulcsút"),
    (0x07BD, 0x07DC, "DECODE"),
    (0x099B, 0x09AE, "ONE-SPACE/MAKE-ROOM"),
    (0x09AD, 0x09D2, "POINTERS"),
    (0x0537, 0x0560, "CURSOR"),
    (0x0F4B, 0x0F55, "D-BOUNCE"),
]

def in_reg(pc):
    for lo, hi, name in REG:
        if lo <= pc <= hi:
            return name
    return None

# 'R' lenyomása, majd lépésenkénti figyelés max 400e lépésig
# (az NMI-injektálást a rom_run-hoz hasonlóan MI végezzük: 26 lépésenként,
#  CDFLAG bit7 esetén)
sim.key('R', True)
log = []
n = 0
while n < 400_000:
    if not sim.halted and n % 26 == 0 and (sim.ram[0x403B] & 0x80):
        sim._quick_nmi()
    if sim.halted:
        sim.nmi_countdown -= 1
        if sim.nmi_countdown <= 0:
            sim.nmi_countdown = 26
            sim._quick_nmi()
        sim.total += 1
        n += 1
        sim._apply_key_script()
        continue
    pc = sim.pc
    r = in_reg(pc)
    if r:
        log.append((n, pc, r, "A=%02X B=%02X C=%02X HL=%04X SP=%04X Fc=%d"
                    % (sim.a, sim.b, sim.c, sim._hl(), sim.sp,
                       1 if sim.f & F_C else 0)))
    sim.step()
    sim.total += 1
    n += 1
    sim._apply_key_script()
    if len(log) > 400:
        break

print("utolsó %d bejegyzés a régiókból:" % min(len(log), 60))
for e in log[-60:]:
    print("  %7d PC=%04X %-18s %s" % (e[0], e[1], e[2], e[3]))
el = sim.peek16(0x4014)
print("E_LINE most:", " ".join("%02X" % b for b in sim.ram[el:el+10]))
print("MODE=0x%02X CDFLAG=0x%02X" % (sim.ram[0x4027], sim.ram[0x403B]))
