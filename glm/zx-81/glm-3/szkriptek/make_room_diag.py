#!/usr/bin/env python3
"""make_room_diag.py — a POINTERS/MAKE-ROOM hibás futásának nyomkövetése.
A hideg start után a PICOBOOT RAM-ba, majd 'R' gomb — a szerkesztő útja."""
import sys
sys.path.insert(0, "/home/z/my-project/GLM/repo/tools")
from romsim import RomSim
from zx81sim import SimError

TAPE = "/home/z/my-project/GLM/repo/dist/ZX81PICO.T81"

sim = RomSim(TAPE)
sim.rom_run(max_steps=2_500_000)
img = dict(sim.blocks)["PICOBOOT"]
sim.ram[0x4009:0x4009 + len(img)] = img
sim.w(0x403B, 0xC0)

# 'R' lenyomása — a szerkesztő ADD-CHAR -> MAKE-ROOM útjáig követjük
sim.stop_reason = None
sim.running = True
sim.key('R', True)
log = []
n = 0
err = None
while n < 1_500_000:
    try:
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
        if 0x099E <= pc <= 0x09D2:
            log.append((pc, "A=%02X BC=%04X DE=%04X HL=%04X SP=%04X "
                        "F=%02X StkEnd=%04X"
                        % (sim.a, sim._bc(), sim._de(), sim._hl(), sim.sp,
                           sim.f, sim.peek16(0x401C))))
            if len(log) > 120:
                log.pop(0)
        sim.step()
        sim.total += 1
        n += 1
        if pc == 0x0523:
            break
    except Exception as e:
        err = "%s: %s (PC=%04X)" % (type(e).__name__, e, sim.pc)
        break

if err:
    print("HIBA:", err)
else:
    print("OK — elerte a BACK-NEXT-et")
for i, (pc, regs) in enumerate(log):
    print("%3d PC=%04X %s" % (i, pc, regs))
el = sim.peek16(0x4014)
print("E_LINE:", " ".join("%02X" % b for b in sim.ram[el:el + 10]))
