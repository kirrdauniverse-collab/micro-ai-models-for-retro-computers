#!/usr/bin/env python3
"""teljes_ut.py — a user pontos forgatókönyve a VALÓDI ROM betöltőjével:
hideg start -> LOAD "" (PICOBOOT a szalagról!) -> RUN -> INPUT (ENTER) ->
telepítő (RAND USR) + NEW -> LOAD "" (PICOBASE) -> RUN -> motor belépés.
Így a VARS/E_LINE/STKEND mutatókat maga a ROM IN-PROG hozza rendbe."""
import sys
sys.path.insert(0, "/home/z/my-project/GLM/repo/tools")
import romsim
from romsim import RomSim, Tape

TAPE = "/home/z/my-project/GLM/repo/dist/ZX81PICO.T81"

sim = RomSim(TAPE)
names = [n for n, _ in sim.blocks]

def status(tag):
    el = sim.peek16(0x4014)
    print("[%s] PC=%04X RAMTOP=%04X E_LINE=%04X STKEND=%04X VARS=%04X "
          "DF_SZ=%02X CDFLAG=%02X"
          % (tag, sim.pc, sim.peek16(0x4004), el, sim.peek16(0x401C),
             sim.peek16(0x4010), sim.ram[0x4022], sim.ram[0x403B]))
    scr = [s for s in sim.screen().split("\n") if s.strip()]
    for s in scr[:6]:
        print("   |%s|" % s)

def run(tag, steps):
    sim.stop_reason = None
    sim.running = True
    n = sim.rom_run(max_steps=steps)
    print("(%s) %d lépés -> %s, PC=%04X" % (tag, n, sim.stop_reason, sim.pc))
    return n

def shift_key(k, at):
    """SHIFT+k billentyű (K-mód token: pl. SHIFT+K = LOAD)."""
    sim.key_script.append((at, "press", "\x00"))
    sim.key_script.append((at, "press", k))
    sim.key_script.append((at + 400, "release", k))
    sim.key_script.append((at + 450, "release", "\x00"))

# 1) hideg start — a szalag az ELSŐ blokknál (PICOBOOT) álljon
sim.rom_run(max_steps=2_500_000)
sim.tape = Tape(sim.blocks, start_at=0)
status("hideg start")

# 2) LOAD "" begépelése: LOAD token = SHIFT+K; "" = SHIFT+P SHIFT+P; NEWLINE
at = sim.total + 200
shift_key("K", at)            # LOAD token
at += 800
shift_key("P", at)            # "
at += 800
shift_key("P", at)            # "
at += 800
sim.key_script.append((at, "press", "\n"))
sim.key_script.append((at + 400, "release", "\n"))
run("LOAD '' (PICOBOOT)", 40_000_000)
status("PICOBOOT betöltve?")

# 3) RUN begépelése (K-mód: 'R' első gombja RUN tokent ad)
at = sim.total + 200
sim.key_script.append((at, "press", "R"))
sim.key_script.append((at + 500, "release", "R"))
at += 800
sim.key_script.append((at, "press", "\n"))
sim.key_script.append((at + 400, "release", "\n"))
run("RUN (PICOBOOT)", 30_000_000)
status("PICOBOOT futás után")

# 4) INPUT A$ — ENTER
at = sim.total + 200
sim.key_script.append((at, "press", "\n"))
sim.key_script.append((at + 500, "release", "\n"))
run("INPUT ENTER", 20_000_000)
status("INPUT után")

# 5) telepítő + NEW lefutása
run("telepítő+NEW", 30_000_000)
status("NEW után")

# 6) LOAD "" — most a PICOBASE jön a szalagról
at = sim.total + 200
shift_key("K", at)
at += 800
shift_key("P", at)
at += 800
shift_key("P", at)
at += 800
sim.key_script.append((at, "press", "\n"))
sim.key_script.append((at + 400, "release", "\n"))
run("LOAD '' (PICOBASE)", 60_000_000)
status("PICOBASE betöltve?")

# 7) RUN — a 2-es sor (IF USR 16514=1) sorsa
at = sim.total + 200
sim.key_script.append((at, "press", "R"))
sim.key_script.append((at + 500, "release", "R"))
at += 800
sim.key_script.append((at, "press", "\n"))
sim.key_script.append((at + 400, "release", "\n"))
run("RUN (PICOBASE)", 60_000_000)
status("RUN után — 4/2?")
