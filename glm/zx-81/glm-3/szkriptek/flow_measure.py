#!/usr/bin/env python3
"""A TELJES valódi út mérése a valódi ROM-mal:
hideg start -> LOAD "" -> RUN -> ENTER -> NEW -> LOAD "" -> RUN
Minden TEST-ROOM (0x0EC5) hívást naplóz (STKEND/SP/BC), és a REPORT-4
(0x0ED3) töréspontnál részletes állapotot Dumpol."""
import sys
sys.path.insert(0, "/home/z/my-project/GLM/repo/tools")
from romsim import RomSim
from zx81sim import F_C

TAPE = "/home/z/my-project/GLM/repo/dist/ZX81PICO.T81"

sim = RomSim(TAPE)

tr_log = []          # az utolsó TEST-ROOM hívások
report4 = {"hit": False}


def run(steps, tag=""):
    """rom_run hű mása + TEST-ROOM/REPORT-4 nyomkövetés."""
    n = 0
    while n < steps and sim.running:
        if sim.halted:
            sim.nmi_countdown -= 1
            if sim.nmi_countdown <= 0:
                sim.nmi_countdown = 26
                sim._quick_nmi()
            sim.total += 1
            n += 1
            sim._apply_key_script()
            continue
        if n % 26 == 0 and (sim.ram[0x403B] & 0x80):
            sim._quick_nmi()
        pc = sim.pc
        if pc == 0x0EC5:      # TEST-ROOM
            tr_log.append((sim.peek16(0x401C), sim.sp, sim._bc()))
            if len(tr_log) > 40:
                tr_log.pop(0)
        elif pc == 0x0ED3:    # REPORT-4!
            report4["hit"] = True
            report4["stkend"] = sim.peek16(0x401C)
            report4["sp"] = sim.sp
            report4["e_ppc"] = sim.peek16(0x400A)
            report4["pc"] = pc
            sim.stop_reason = "REPORT-4"
            sim.running = False
            break
        if pc == 0x034C:
            sim._tape_inbyte()
        elif pc == 0x0207:
            cd = sim.ram[0x403B]
            if ((cd >> 6) ^ (cd >> 7)) & 1:
                sim.w(0x403B, cd | 0xC0)
                sim._keyboard_effect()
                sim.f |= F_C
            else:
                sim.f &= ~F_C & 0xFF
            sim.pc = sim.pop()
        elif pc == 0x0229:
            sim._keyboard_effect()
            sim.pc = sim.pop()
        elif pc == 0x0292:
            sim.ix = sim.pop()
            sim._keyboard_effect()
            sim.pc = sim.ix
        elif pc == 0x02B5:
            sim.pc = sim.pop()
        else:
            sim.step()
        if sim.pc == 0x0000 and sim.total > 100:
            sim.stop_reason = "RESET!"
            sim.running = False
            break
        sim.total += 1
        n += 1
        sim._apply_key_script()
    if tag:
        print("[%s] %d lépés, stop=%s, PC=%04X" % (tag, n, sim.stop_reason, sim.pc))
    return n


def keys(ch, t0, hold=400, gap=400):
    sim.key_script.append((t0, "press", ch))
    sim.key_script.append((t0 + hold, "release", ch))
    return t0 + hold + gap


def quote(t0, hold=400, gap=400):
    """SHIFT+P kombináció: mindkettő egyszerre lenyomva."""
    sim.key_script.append((t0, "press", "\x00"))     # SHIFT
    sim.key_script.append((t0, "press", "P"))
    sim.key_script.append((t0 + hold, "release", "\x00"))
    sim.key_script.append((t0 + hold, "release", "P"))
    return t0 + hold + gap


def eline_dump(tag):
    el = sim.peek16(0x4014)
    print("  E_LINE@%04X: %s | MODE=%02X DF_SZ=%02X STKEND=%04X RAMTOP=%04X "
          "VARS=%04X D_FILE=%04X" % (el, " ".join("%02X" % b for b in
                                                  sim.ram[el:el + 10]),
                                     sim.ram[0x4006], sim.ram[0x4022],
                                     sim.peek16(0x401C), sim.peek16(0x4004),
                                     sim.peek16(0x4010), sim.peek16(0x400C)))


# --- 1. hideg start
run(2_500_000, "hideg start")
eline_dump("hideg")

# --- 2. LOAD "" begépelése: J (=LOAD), SHIFT+P x2 (=két idézőjel), NEWLINE
t = sim.total + 200
t = keys("J", t)
t = quote(t)
t = quote(t)
t = keys("\n", t)
run(t - sim.total + 2_000_000, "LOAD begépelve")
eline_dump("LOAD sor")

# --- 3. a kazetta-betöltés (PICOBOOT)
run(6_000_000, "PICOBOOT betöltés")
eline_dump("PICOBOOT")

# --- 4. RUN begépelése + lefuttatása (bemutató -> INPUT)
t = sim.total + 200
t = keys("R", t)
t = keys("\n", t)
run(t - sim.total + 3_000_000, "RUN (bemutató)")

# --- 5. ENTER az INPUT-nak, majd a telepítő + NEW
t = sim.total + 200
t = keys("\n", t)
run(t - sim.total + 6_000_000, "ENTER -> telepítő + NEW")

# --- 6. LOAD "" újra (PICOBASE)
t = sim.total + 200
t = keys("J", t)
t = quote(t)
t = quote(t)
t = keys("\n", t)
run(t - sim.total + 2_000_000, "2. LOAD begépelve")
run(6_000_000, "PICOBASE betöltés")
eline_dump("PICOBASE")

# --- 7. RUN
t = sim.total + 200
t = keys("R", t)
t = keys("\n", t)
run(t - sim.total + 6_000_000, "RUN a PICOBASE-en")

# --- eredmény
print()
if report4["hit"]:
    print("!!! REPORT-4 (OUT OF RAM) eltalálva: STKEND=%04X SP=%04X "
          "E_PPC=%04X (szabad: %d B)" % (report4["stkend"], report4["sp"],
                                         report4["e_ppc"],
                                         report4["sp"] - report4["stkend"]))
print("az utolsó TEST-ROOM hívások (STKEND, SP, BC, szabad=SP-STKEND):")
for stk, sp, bc in tr_log[-20:]:
    print("   STKEND=%04X SP=%04X BC=%04X szabad=%d" % (stk, sp, bc, sp - stk))
print()
print("képernyő (nem üres sorok):")
for line in sim.screen().split("\n"):
    if line.strip():
        print("  |" + line + "|")
