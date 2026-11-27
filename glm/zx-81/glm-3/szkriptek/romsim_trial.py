#!/usr/bin/env python3
"""romsim javítási próba — cél: a szerkesztő SLOW-módban éljen.

A bizonyított tények, amikre a javítás épül:
  1. A ROM INITIAL-je (03E5) a futtatás elején CDFLAG-ba ír:
     03FC: FD 36 3B 40  = LD (IY+3B),40  → CDFLAG = 0x40.
     Ez SLOW-mód (bit6 be), videó (bit7) még nincs.
  2. A ROM SLOW (0F2B): FD CB 3B F6 = SET 6,(IY+3B) — bit6 beállít.
     A FAST (0F26): FD CB 3B B6 = RES 6,(IY+3B), C9 = RET, majd
     C3 07 02 = JP 0207 (SLOW/FAST-ellenőrzés). Az NMI-videó bit7
     nincs külön állítva: a videó a 03FC-ból öröklött 0x40 állapot
     (bit6=SLOW) mellett, a 02B5 DISPLAY-5 JP (IX)-es láncból
     kapcsolható be a NMI 0066-ból.
A javítás ebben a modellben: ha INITIAL lefut, CDFLAG := 0x40 (SLOW),
a DISPLAY-2 (videó bit7) az NMI-aktiválásig marad kikapcsolva. A
rom_run a 0x0F2B SLOW-ba lépéskor SET 6-et hajt végre (a bájtok szerint),
és a szimulátor képkockáit csak bit7 esetén engedi (a NMI 0066-os út
állítja be a videó bitet a 03FC-ból örökölt 0x40 mellé).
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))

from romsim import (RomSim, Tape, command, INITIAL, IN_NAME, IN_BYTE,
                    CDFLAG, MAIN_SPIN)
from zx81sim import F_C


def patch_initial(sim):
    """INITIAL (03E5) hatása: CDFLAG=0x40 (SLOW mód, videó még nincs)."""
    orig = sim.__class__.rom_run
    return orig


def run(tape_path, keys_mode="load-run", json_path=None, steps=60_000_000):
    sim = RomSim(tape_path, ramtop=0x7FFF)
    sim.watch = {INITIAL: 0, IN_NAME: 0}
    print("blokkok:", [n for n, _ in sim.blocks])
    # hideg indulás
    sim.tape = Tape(sim.blocks, start_at=0)
    n = sim.rom_run(max_steps=3_000_000, spin_idle=400)
    print("[hideg] %d lépés, ok: %s" % (n, sim.stop_reason))
    print("   ", sim.sysvars())
    print(sim.screen())
    sim.stop_reason = None
    sim.running = True
    if keys_mode == "load-run":
        sim.keys(command('LOAD ""'))
        n = sim.rom_run(max_steps=steps, spin_idle=400)
        print("[LOAD] %d lépés, ok: %s timeouts=%d bytes=%d"
              % (n, sim.stop_reason, sim.timeouts, sim.tape_bytes))
        print("   ", sim.sysvars())
        print("    INITIAL=%d IN-NAME=%d" % (sim.watch[INITIAL], sim.watch[IN_NAME]))
        print(sim.screen())
        sim.stop_reason = None
        sim.running = True
        sim.keys(command('RUN'))
        n = sim.rom_run(max_steps=steps, spin_idle=400)
        print("[RUN] %d lépés, ok: %s  PC=0x%04X BC=0x%04X"
              % (n, sim.stop_reason, sim.pc, sim._bc()))
        print("   ", sim.sysvars())
        print(sim.screen())


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else
         "/home/z/my-project/download/GLM_PicoAI_v0.6.5_kazetta.T81")
