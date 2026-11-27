#!/usr/bin/env python3
"""Az 'R' lenyomása utáni teljes út gyűrűs-pufferes nyomkövetése.
A SimError-t elkapjuk és az utolsó 90 lépést nyomtatjuk."""
import sys
sys.path.insert(0, "/home/z/my-project/GLM/repo/tools")
from romsim import RomSim
from zx81sim import SimError

TAPE = "/home/z/my-project/GLM/repo/dist/ZX81PICO.T81"

sim = RomSim(TAPE)
# RAMTOP-író megfigyelő: ki írja a 0x4004/0x4005-öt?
_writes = []
_orig_poke = sim.poke


def _watch_poke(addr, val):
    if addr in (0x4004, 0x4005):
        _writes.append((sim.pc, addr, val))
    return _orig_poke(addr, val)


sim.poke = _watch_poke

# hideg indulás SAJÁT nyomkövető ciklussal (a rom_run most elszáll)
sim.stop_reason = None
sim.running = True

ring = []
prev = []
n = 0
err = None
entered_disp2 = None
while n < 3_000_000:
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
        # --- a rom_run eltérítéseinek hű másola ---
        if pc == 0x034C:                      # IN-BYTE (kazetta)
            sim._tape_inbyte()
            n += 1
            sim.total += 1
            continue
        elif pc == 0x0207:                    # SLOW/FAST
            cd = sim.ram[0x403B]
            if ((cd >> 6) ^ (cd >> 7)) & 1:
                sim.w(0x403B, cd | 0xC0)
                sim._keyboard_effect()
                sim.f |= 0x01
            else:
                sim.f &= ~0x01 & 0xFF
            sim.pc = sim.pop()
            n += 1
            sim.total += 1
            continue
        elif pc == 0x0229:                    # DISPLAY-1 (CALL Z út)
            sim._keyboard_effect()
            sim.pc = sim.pop()
            n += 1
            sim.total += 1
            continue
        if 0x023E <= pc <= 0x02BB and entered_disp2 is None:
            entered_disp2 = list(ring)   # az elozo 60 lepes
        if entered_disp2 is not None and len(entered_disp2) < 140:
            entered_disp2.append((pc, "A=%02X B=%02X C=%02X D=%02X E=%02X H=%02X L=%02X "
                                  "SP=%04X" % (sim.a, sim.b, sim.c, sim.d, sim.e,
                                               sim.h, sim.l, sim.sp)))
        if pc > 0x7FFF and not prev:
            prev = list(ring)
            break
        ring.append((pc, "A=%02X B=%02X C=%02X D=%02X E=%02X H=%02X L=%02X "
                    "SP=%04X" % (sim.a, sim.b, sim.c, sim.d, sim.e,
                                 sim.h, sim.l, sim.sp)))
        if len(ring) > 60:
            ring.pop(0)
        if pc == 0x04CF:
            break
        sim.step()
        sim.total += 1
        n += 1
    except Exception as e:
        err = "%s: %s (PC=%04X)" % (type(e).__name__, e, sim.pc)
        break

if err:
    print("HIBA:", err)
else:
    print("hideg start kesz, PC=%04X" % sim.pc)
print("RAMTOP(0x4004)-írások:", ["PC=%04X addr=%04X val=%02X" % w for w in _writes])
if entered_disp2:
    print("--- DISPLAY-2 belepultek elotti 60 + utani lepesek ---")
    for i, (pc, regs) in enumerate(entered_disp2[:140]):
        print("%3d PC=%04X %s" % (i, pc, regs))
else:
    print("(nem jutott el a DISPLAY-2-be)")
el = sim.peek16(0x4014)
print("E_LINE (%04X):" % el,
      " ".join("%02X" % b for b in sim.ram[el:el + 10]))
print("MODE(0x4006)=%02X DF_SZ=%02X D_FILE=%04X VARS=%04X E_LINE=%04X STKEND=%04X RAMTOP=%04X"
      % (sim.ram[0x4006], sim.ram[0x4022], sim.peek16(0x400C),
         sim.peek16(0x4010), el, sim.peek16(0x401C), sim.peek16(0x4004)))
