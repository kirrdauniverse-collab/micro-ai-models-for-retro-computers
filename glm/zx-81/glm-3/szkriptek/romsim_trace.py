#!/usr/bin/env python3
"""A v0.6.5 lánc RÉSZLETES követése a valódi ROM-mal.

Cél: megtalálni, mi történik a RUN után — hol fut szét a gép. A romsim
fő szála minden 2000. lépésben mintát vesz (PC, SP, D_FILE, E_PPC,
CDFLAG), és ha PC érvénytelen lesz, az utolsó 40 mintát kiírja.
"""
import sys
import os

sys.path.insert(0, "/home/z/my-project/GLM/repo/tools")
from romsim import RomSim, Tape, command, INITIAL, IN_NAME, CDFLAG

TAPE = sys.argv[1] if len(sys.argv) > 1 else \
    "/home/z/my-project/download/GLM_PicoAI_v0.6.5_kazetta.T81"

sim = RomSim(TAPE, ramtop=0x7FFF)
sim.watch = {INITIAL: 0, IN_NAME: 0}
sim.tape = Tape(sim.blocks, start_at=0)

# 1) hideg indulás
n = sim.rom_run(max_steps=3_000_000, spin_idle=400)
print("[hideg] %d lépés, %s" % (n, sim.stop_reason))
sim.stop_reason = None
sim.running = True

# 2) LOAD ""
sim.keys(command('LOAD ""'))
n = sim.rom_run(max_steps=60_000_000, spin_idle=400)
print("[LOAD] %d lépés, %s  bájtok=%d" % (n, sim.stop_reason, sim.tape_bytes))
print("   ", sim.sysvars())
scr = sim.screen()
print("képernyő első sorai:", [s for s in scr.splitlines() if s][:4])
sim.stop_reason = None
sim.running = True

# 3) RUN — mintavétellel
samples = []
early = []
orig_step = None
sim.keys(command('RUN'))
n = 0
MAX = 40_000_000
while n < MAX and sim.running:
    t = sim.total
    if t >= sim.next_frame:
        sim.next_frame = t + 3000
        if sim.ram[CDFLAG] & 0x80:
            sim._frame()
    pc = sim.pc
    if pc == 0x034C:
        sim._tape_inbyte()
    elif pc == 0x0207:
        cd = sim.ram[CDFLAG]
        if ((cd >> 6) ^ (cd >> 7)) & 1:
            from zx81sim import F_C
            if cd & 0x40:
                sim.w(CDFLAG, cd | 0x80)
            else:
                sim.w(CDFLAG, cd & 0x3F)
            sim._display2()
            sim.f |= F_C
        else:
            sim.f &= ~F_C & 0xFF
        sim.pc = sim.pop()
    elif pc == 0x0229:
        sim._frame()
        sim.pc = sim.pop()
    elif pc == 0x0292:
        sim.ix = sim.pop()
        sim.pc = sim.ix
    elif pc == 0x02B5:
        sim.pc = sim.pop()
    elif pc == 0x083E and sim._hl() < 0x2000:
        sim.pc = pc + 1
    elif pc == 0x09AA and sim._de() < 0x2000:
        sim.pc = pc + 1
    else:
        if pc > 0xFFFF or pc >= len(sim.ram):
            sim.stop_reason = "PC a RAM-on kívül: 0x%04X" % pc
            sim.running = False
            break
        try:
            sim.step()
        except Exception as e:
            sim.stop_reason = "kivétel: %s" % e
            sim.running = False
            break
    if sim.pc == 0x0000:
        sim.stop_reason = "RESET! (PC=0x0000)"
        sim.running = False
        break
    if (n % 2000) == 0:
        samples.append((n, sim.pc, sim.sp, sim.peek16(0x400C),
                        sim.peek16(0x400A), sim.ram[CDFLAG]))
    if n < 200000 and (n % 200) == 0:
        early.append((n, sim.pc, sim.sp, sim.peek16(0x4004),
                      sim.peek16(0x400C), sim.peek16(0x4014)))
    sim.total += 1
    n += 1

print("[RUN] %d lépés, %s  frame_no=%d key_script=%d" % (n, sim.stop_reason, sim.frame_no, len(sim.key_script)))
print("    futás végi regiszterek: A=%02X BC=%04X DE=%04X HL=%04X IX=%04X IY=%04X" % (sim.a, sim._bc(), sim._de(), sim._hl(), sim.ix, sim.iy))
print("   ", sim.sysvars())
print("utolsó 40 minta (lépés, PC, SP, D_FILE, E_PPC, CDFLAG):")
for s in samples[-40:]:
    print("   %8d  PC=%04X SP=%04X D_FILE=%04X E_PPC=%04X CD=%02X" % s)
print("első futás-lépések (lépés, PC, SP, RAMTOP, D_FILE, E_LINE):")
for s in early[:400]:
    print("   %8d  PC=%04X SP=%04X RAMTOP=%04X D_FILE=%04X E_LINE=%04X" % s)
