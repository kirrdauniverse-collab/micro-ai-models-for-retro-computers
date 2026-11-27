#!/usr/bin/env python3
"""teljes_ut2.py — a user forgatókönyve, a LOAD parancs közvetlen
0x0340-hívásával (a szim szerkesztő-begépelési korlátai miatt):
hideg -> LOAD PICOBOOT -> RUN -> INPUT ENTER -> telepítő+NEW ->
LOAD PICOBASE -> RUN -> a 2-es sor: 4/2?"""
import sys
sys.path.insert(0, "/home/z/my-project/GLM/repo/tools")
from romsim import RomSim, Tape

TAPE = "/home/z/my-project/GLM/repo/dist/ZX81PICO.T81"

sim = RomSim(TAPE)
names = [n for n, _ in sim.blocks]

def status(tag):
    el = sim.peek16(0x4014)
    print("[%s] PC=%04X RAMTOP=%04X E_LINE=%04X STKEND=%04X VARS=%04X"
          % (tag, sim.pc, sim.peek16(0x4004), el, sim.peek16(0x401C),
             sim.peek16(0x4010)))
    scr = [s for s in sim.screen().split("\n") if s.strip()]
    for s in scr[:5]:
        print("   |%s|" % s)

def run(tag, steps):
    sim.stop_reason = None
    sim.running = True
    n = sim.rom_run(max_steps=steps)
    print("(%s) %d lépés -> %s, PC=%04X" % (tag, n, sim.stop_reason, sim.pc))

def do_load():
    """LOAD '' — a parancs közvetlen hívása (a CH_ADD az E_LINE-ra mutat,
    ahol a LOAD + '' + NEWLINE sor áll)."""
    el = sim.peek16(0x4014)
    sim.ram[el] = 0xEF
    sim.ram[el + 1] = 0x0B
    sim.ram[el + 2] = 0x8B
    sim.ram[el + 3] = 0x76
    sim.w(0x4016, el)         # CH_ADD a LOAD tokenra
    sim.w(0x4018, el + 5)
    sim.w(0x401A, el + 5)
    sim.sp = 0x7FFD
    sim.push(0x04CF)          # visszatérés a szerkesztő várakozásához
    sim.pc = 0x0340
    sim.running = True
    sim.stop_reason = None

# 1) hideg start
run("hideg start", 3_000_000)
status("hideg start")

# 2) LOAD PICOBOOT
sim.tape = Tape(sim.blocks, start_at=0)
do_load()
run("LOAD PICOBOOT", 40_000_000)
status("PICOBOOT betöltve")

def do_run():
    """RUN — a ROM NEXT-LINE (0x066C) futtatási ciklusának indítása:
    HL = a sor eleje (a sor-szám bájtjai), NXTLIN ugyanoda."""
    # A NEXT-LINE a HL-ben varja a sor kezdetet (a program-proxy elejet)
    prog = sim.peek16(0x407D)
    # a program kezdete (PROG): a ROM-ban a NXTLIN a program elejere mutat
    sim.w(0x4014 + 0x2C, prog)      # NXTLIN? — a cim hibas lehet; biztositjuk HL-lel is
    sim.sp = 0x7FFD
    sim.push(0x04CF)
    # HL-t a sor elejere allitjuk (a PC=066C elott):
    sim.h, sim.l = (prog >> 8) & 0xFF, prog & 0xFF
    sim.pc = 0x066C
    sim.running = True
    sim.stop_reason = None

# 3) RUN — a PICOBOOT 9-es sor: RAND USR 16514; a 10-es: NEW.
#    A NEXT-LINE (0x066C) indítása HL = program eleje (0x407D):
prog = 0x407D
print("program kezdet:", hex(prog))
do_run()
run("RUN (PICOBOOT)", 60_000_000)
status("PICOBOOT futás után")

# 4) INPUT A$ — ENTER (a bemenet az E_LINE-ba kerül):
sim.key_script.append((sim.total + 200, "press", "\n"))
sim.key_script.append((sim.total + 600, "release", "\n"))
run("INPUT ENTER", 20_000_000)
status("INPUT után")

# 5) a telepítő (RAND USR) + NEW lefutása — már a RUN alatt történt?
status("ellenőrzés: RAMTOP")
print("RAMTOP=%04X (a telepítő 0x715F-re állítja!)" % sim.peek16(0x4004))
print("D_FILE=%04X (0x7B00 lesz)" % sim.peek16(0x400C))

# 6) LOAD PICOBASE
sim.tape = Tape(sim.blocks, start_at=1)
do_load()
run("LOAD PICOBASE", 60_000_000)
status("PICOBASE betöltve")

# 7) RUN — a 2-es sor (IF USR 16514=1 THEN LOAD) sorsa!
do_run()
run("RUN (PICOBASE)", 60_000_000)
status("RUN után — 4/2?")
