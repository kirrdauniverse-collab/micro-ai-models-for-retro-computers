#!/usr/bin/env python3
"""ROM-szintű ZX81 szimulátor — a VALÓDI 8K ROM fut a saját kódjával.

A szimulátor csak a hardvert modellezi, ROM-rutinokat nem helyettesít:
  - billentyűzet: a port-olvasás (IN A,(FE)) a lenyomott kulcsokat adja,
    a ROM saját KEYBOARD (02BB) és DECODE (07BD) rutinja dekódol;
  - képkocka: SLOW módban (CDFLAG 7. bitje be) képkockánként (FRAME_STEPS
    lépésenként) lefut a DISPLAY-2 (023E) hű modellje: LAST-K frissítés a
    valódi ROM KEYBOARD futtatásával, DEBOUNCE- lebomlás, „új billentyű”
    jelző (CDFLAG 0. bitje) — a ROM bájtjai szerint (02BB..0276);
  - kazetta: a szalag-bájtokat az IN-BYTE (034C) belépésénél adjuk; csend
    (blokkok között) esetén a ROM SAJÁT időtúllépési útja fut tovább
    (POP AF; POP AF; CP D; JP NC,INITIAL / IN-NAME);
  - a kijelző-generálás (DISPLAY-1/3/5) időzítő része funkcionálisan van
    modellezve: a ROM kódja nem fut végig rajta, csak a visszatérés.

A ROM-igazolás célja: a teljes lánc (friss gép → LOAD → RUN → boot-ML →
láncolt LOAD → motor → gépelés → válasz → /save) a valódi ROM-mal fusson.
"""
import sys
import os
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from zx81sim import (ZX81Sim, load_blocks, KEY_POS, ZX2ASC,
                     F_C, F_Z, F_N, F_S, F_H, F_P, SimError)

ROM_PATH = os.environ.get("ZX81ROM",
                          "/home/z/my-project/GLM/refs/zx81.rom")
# ROM-címek (a zx81.rom bájtjaiból dekódolva)
IN_BYTE = 0x034C       # szalag-bájt olvasása (időtúllépés: csend)
OUT_NAME = 0x030B      # SAVE: a név kiírása (a bájt (HL)-ben)
OUT_PROG = 0x0316      # SAVE: a programbájt kiírása (a bájt (HL)-ben)
IN_NAME = 0x0364       # IN-NAME: fejléc-várakozás (időtúllépésnél ide)
INITIAL = 0x03E5       # a ROM újrainicializálása (= reset-jelenség)
BREAK4 = 0x03A2        # SPACE a betöltés alatt
DISPLAY1 = 0x0229      # DISPLAY-1
SLOWFAST = 0x0207      # SLOW/FAST kapcsoló
DISPLAY3 = 0x0292      # DISPLAY-3 (képernyő-sor generátor)
WRITE_CH = 0x083E      # WRITE-CH: a szerkesztő printable-puffer-írása
LDIR_ROM = 0x09AA     # MAKE-ROOM LDIR: a puffer mozgatása (ROM-címre csúszva)
DISPLAY5 = 0x02B5      # DISPLAY-5 (időzítő)
KEYBOARD = 0x02BB
MAIN_SPIN = (0x04CF, 0x04D1)   # a szerkesztő főciklusa várakozó állapotban
PROG = 0x407D

# rendszer-változók (ROM-bájtokkal igazolva)
LASTK = 0x4025         # LAST-K: alsó bájt = sormaszk, felső = kulcsbitek
DEBOUNCE = 0x4027
CDFLAG = 0x403B        # 7. bit: videó be; 6. bit: SLOW mód; 0. bit: új billentyű
FRAMESV = 0x4034

FRAME_STEPS = int(os.environ.get("ROMSIM_FRAME_STEPS", "3000"))
HOLD = 3               # billentyű lenyomva ennyi képkockán át
GAP = 9                # következő billentyű ennyi képkockával később

SHIFT = (0xFE, 0)
NEWLINE = KEY_POS["\n"]

# ASCII -> ZX81 belső karakterkód (a kazettanevekhez)
ASC2ZX = {}
for _i in range(26):
    ASC2ZX[chr(65 + _i)] = 0x26 + _i
for _i in range(10):
    ASC2ZX[str(_i)] = 0x1C + _i
ASC2ZX.update({'-': 0x16, '.': 0x1B, '?': 0x0F, '"': 0x0B})


class Tape:
    """A T81-blokkokból álló kazetta-jelfolyam:
    [csend][név+adat][csend][név+adat]... — a csend az IN-BYTE
    időtúllépését váltja ki (a valódi gépen a blokkok közti szünet).
    A szalag mindig csenddel kezdődik: a ROM LOAD-ja a cendet várja,
    mielőtt fejlécet keresne (különben a első blokkot átszalajtja)."""

    def __init__(self, blocks, start_at=0):
        self.blocks = list(blocks)
        self.segs = [("gap", b"")]
        for name, data in self.blocks:
            zxname = bytes(ASC2ZX.get(ch, 0x00) for ch in name)
            zxname = zxname[:-1] + bytes([zxname[-1] | 0x80])
            self.segs.append(("data", zxname + data))
            self.segs.append(("gap", b""))
        self.seg = 2 * start_at          # a start_at-adik blokk ELŐTTI csend
        self.off = 0

    def read(self):
        """Egy bájt, vagy None ha a jelenlegi szegmens csendes/elfogyott."""
        while self.seg < len(self.segs):
            kind, data = self.segs[self.seg]
            if kind == "data" and self.off < len(data):
                b = data[self.off]
                self.off += 1
                return b
            return None
        return None

    def advance(self):
        """A csend után a következő szegmensre lép."""
        self.seg += 1
        self.off = 0

    def where(self):
        """Melyik blokknál jár a szalag (0-tól), vagy -1 a végén."""
        for k, (name, _d) in enumerate(self.blocks):
            if self.seg <= 2 * k + 1:
                return k
        return -1


class RomSim(ZX81Sim):
    """Valódi ROM-mal futó ZX81 (a felhasználó EightyOne-jának modellje:
    RAMTOP alapértelmezetten 7FFF — 16 K RAM, a motor 7FFD-ig dolgozik)."""

    def __init__(self, container, ramtop=0x7FFF, trace=False):
        super().__init__(container, trace=trace)
        with open(ROM_PATH, "rb") as f:
            rom = f.read()
        assert len(rom) == 8192, "hibás ROM-méret"
        self.ram = bytearray(0x10000)
        self.ram[0x0000:0x2000] = rom
        self.rom = bytes(rom)          # csak olvasható ROM-másolat
        self.rom_exec = True
        self.rom_guard = False        # WRITE-CH a szerkesztőben a ROM-t kaparja
        self.tape = None
        self.save_log = []         # (forrás, bájt) a SAVE-ből
        self.key_script = []       # (képkocka, 'press'/'release', kulcs)
        self.total = 0
        self.watch = {}            # cím -> hányszor (megfigyelések)
        self.frame_no = 0
        self.next_frame = 0
        self.stop_reason = None
        self.running = True
        # RAM-CHECK hatása: a RAM 02-vel van feltöltve (MODE = K-mód),
        # RAMTOP a RAM teteje; a gép az INITIAL-ről indul.
        self.ram[0x4000:ramtop + 1] = b"\x02" * (ramtop + 1 - 0x4000)
        self.w(0x4004, ramtop & 0xFF)
        self.w(0x4005, ramtop >> 8)
        self.pc = INITIAL
        self.halted = False
        self.timeouts = 0
        self.tape_bytes = 0

    # --- kazetta-injektálás az IN-BYTE belépésénél
    def _tape_inbyte(self):
        b = self.tape.read() if self.tape else None
        if b is not None:
            self.c = b
            self.a = b
            self.pc = self.pop()
            self.tape_bytes += 1
            return
        # csend: a ROM saját időtúllépési útja:
        #   POP AF; POP AF; CP D; JP NC,INITIAL — különben IN-NAME
        if self.tape:
            self.tape.advance()
        self.pop()
        w2 = self.pop()
        self.a = (w2 >> 8) & 0xFF
        self.f = w2 & 0xFF
        self._cp(self.d)
        self.timeouts += 1
        self.pc = INITIAL if not (self.f & F_C) else IN_NAME

    def _cp(self, v):
        r = (self.a - v) & 0xFF
        self.f = (self.f & ~(F_C | F_Z | F_N | F_S | F_H | F_P)) \
            | (F_C if self.a < v else 0) | (F_Z if r == 0 else 0) \
            | F_N | (F_S if r & 0x80 else 0) \
            | (F_H if (self.a & 0xF) < (v & 0xF) else 0) \
            | (F_P if ((self.a ^ v) & (self.a ^ r) & 0x80) else 0)

    # --- SAVE-rögzítés (a 030B / 0316 címeken)
    def _save_capture(self, which):
        self.save_log.append((which, self.ram[self._hl()]))

    # --- billentyű-vezérlés
    def key(self, ch, press=True):
        if ch in KEY_POS:
            if press:
                self.held.add(KEY_POS[ch])
            else:
                self.held.discard(KEY_POS[ch])

    def keys(self, seq, at=None):
        """Kulcs-sorozat ütemezése: (sor, oszlop, shift) hármasok."""
        f = self.frame_no + 2 if at is None else at
        for (r, c, sh) in seq:
            self.key_script.append((f, "press", (r, c, sh)))
            self.key_script.append((f + HOLD, "release", (r, c, sh)))
            f += GAP
        return f

    def kbd(self, text, at=None, shifted=False):
        """Szöveg begépelése nyers (L-mód szerinti) kulcsokkal — a ROM
        maga dönti el K-módban, mit csinál egy betű (kulcsszó!)."""
        seq = []
        for ch in text:
            if ch == " ":
                seq.append((0x7F, 0, False))
            elif ch in KEY_POS:
                r, c = KEY_POS[ch]
                seq.append((r, c, shifted))
            else:
                raise ValueError("nincs ilyen billentyű: %r" % ch)
        return self.keys(seq, at)

    def _apply_key_script(self):
        ks = self.key_script
        while ks and ks[0][0] <= self.frame_no:
            _, act, (r, c, sh) = ks.pop(0)
            k = (r, c)
            if act == "press":
                self.held.add(k)
                if sh:
                    self.held.add(SHIFT)
            else:
                self.held.discard(k)
                if sh:
                    self.held.discard(SHIFT)

    # --- a valódi ROM KEYBOARD (02BB) lefuttatása a regiszterek megőrzésével
    def _keyboard_scan(self):
        keep = (self.a, self.f, self.b, self.c, self.d, self.e, self.h, self.l,
                self.a2, self.f2, tuple(self.regs2), self.ix, self.iy,
                self.sp, self.pc)
        SENT = 0x0005
        self.push(SENT)
        self.pc = KEYBOARD
        for _ in range(400):
            if self.pc == SENT:
                break
            self.step()
        h, l = self.h, self.l
        (self.a, self.f, self.b, self.c, self.d, self.e, self.h, self.l,
         self.a2, self.f2, r2, self.ix, self.iy, self.sp, self.pc) = keep
        self.regs2 = list(r2)
        return h, l

    # --- DISPLAY-2 (023E) hű modellje
    def _display2(self):
        h, l = self._keyboard_scan()
        old_l, old_h = self.ram[LASTK], self.ram[LASTK + 1]
        cy = 1 if (old_h >= 0xFE) else 0
        diff = (((h << 8) | l) - ((old_h << 8) | old_l) - cy) & 0xFFFF
        deb = self.ram[DEBOUNCE]
        a = (deb | (diff >> 8) | (diff & 0xFF)) & 0xFF
        self.ram[LASTK], self.ram[LASTK + 1] = l, h
        cd = self.ram[CDFLAG] & 0xFE
        newdeb = (0x1F if old_h < 0xFE else (deb & 0x1F)) >> 1
        if a == 0:
            cd |= 0x01
            if not (cd & 0x80):     # FAST: azonnal „új”, DEBOUNCE érintetlen
                newdeb = deb
        self.ram[DEBOUNCE] = newdeb
        self.ram[CDFLAG] = cd

    def _frame(self):
        """Egy képkocka (50 Hz): FRAMES csökken, billentyű-szkennelés."""
        fr = (self.peek16(FRAMESV) - 1) & 0xFFFF
        self.w(FRAMESV, fr & 0xFF)
        self.w(FRAMESV + 1, fr >> 8)
        self.frame_no += 1
        self._apply_key_script()
        self._display2()

    # --- futtatás
    def rom_run(self, max_steps=20_000_000, until=None, spin_idle=None):
        """Futtatás. until: fv, amely True esetén megáll (minden 256.
        lépésben hívjuk). spin_idle: ha megadott, a szerkesztő főciklusának
        ennyi egymás utáni várakozó lépése után megáll (billentyű nélkül)."""
        n = 0
        spin = 0
        while n < max_steps and self.running:
            t = self.total
            if t >= self.next_frame:
                self.next_frame = t + FRAME_STEPS
                # videó = bit7 (NMI generátor) ÉS bit6 (SLOW): FAST-ban
                # nincs képkocka-billentyű-szkennelés sem
                if (self.ram[CDFLAG] & 0xC0) == 0xC0:
                    self._frame()
            if self.halted:
                # HALT: a következő sorvég-int megszakítja (~207 T-állapot)
                self.nmi_countdown -= 1
                if self.nmi_countdown <= 0:
                    self.nmi_countdown = 26
                    self.halted = False
                self.total += 1
                n += 1
                continue
            pc = self.pc
            if pc in self.watch:
                self.watch[pc] += 1
            if pc == IN_BYTE:
                self._tape_inbyte()
            elif (pc in (WRITE_CH, LDIR_ROM)) and (
                    (pc == WRITE_CH and self._hl() < 0x2000)
                    or (pc == LDIR_ROM and self._de() < 0x2000)):
                # WRITE-CH (083E) a szerkesztőben a printable-pufferbe
                # ír; ha HL a ROM-ba mutat (0x1090: WORKSPACE alatti
                # csúszás), a valódi gép NEM írja meg a ROM-ot: a mi
                # modellünkben ez a lépés nem változtat semmit.
                self.pc = pc + 1
            elif pc == SLOWFAST:
                # SLOW/FAST (0x0207) a ROM bájtjai szerint: RET NC, ha
                # CDFLAG bit6 == bit7 (nincs teendő). Különben a kettő
                # eltér: SLOW-ra váltásnál (bit6 be) SET 7,(HL) — a videó
                # bekapcsol (0x40 -> 0xC0) —, FAST-ra váltásnál (bit6 ki)
                # RES 6,(HL) és az NMI-kapcsoló ki (0x80 -> 0x00).
                cd = self.ram[CDFLAG]
                if ((cd >> 6) ^ (cd >> 7)) & 1:
                    if cd & 0x40:
                        self.w(CDFLAG, cd | 0x80)   # SLOW: videó be
                    else:
                        self.w(CDFLAG, cd & 0xBF)   # FAST: bit6 ki, videó?
                    self._display2()
                    self.f |= F_C
                else:
                    self.f &= ~F_C & 0xFF
                self.pc = self.pop()
            elif pc == DISPLAY1:
                # DISPLAY-1 (a főciklus CALL Z,0229 útja): egy szkenn
                self._frame()
                self.pc = self.pop()
            elif pc == DISPLAY3:
                self.ix = self.pop()
                self.pc = self.ix
            elif pc == DISPLAY5:
                self.pc = self.pop()
            elif pc == OUT_NAME:
                self._save_capture("name")
                self.step()
            elif pc == OUT_PROG:
                self._save_capture("data")
                self.step()
            else:
                if pc > 0xFFFF or pc < 0 or (pc >= len(self.ram)):
                    self.stop_reason = "PC a RAM-on kivül: 0x%04X" % pc
                    self.running = False
                    break
                self.step()
            if self.pc == 0x0000:
                self.stop_reason = "RESET! (PC=0x0000)"
                self.running = False
                break
            if self.pc >= 0x10000 or (self.pc > 0x7FFF and self.pc < 0x8000):
                self.stop_reason = ("érvénytelen PC: 0x%04X (az utolsó "
                                    "utasítás PC=0x%04X volt)" % (self.pc, pc))
                self.running = False
                break
            # a szerkesztő várakozó ciklusa
            if pc in MAIN_SPIN:
                spin += 1
            else:
                spin = 0
            if spin_idle and spin >= spin_idle and not self.held \
                    and not self.key_script:
                self.stop_reason = "szerkesztő vár (üresjárás)"
                break
            self.total += 1
            n += 1
            if until and (n & 0xFF) == 0 and until():
                self.stop_reason = self.stop_reason or "feltétel teljesült"
                break
        if n >= max_steps and not self.stop_reason:
            self.stop_reason = "lépéskorlát"
        return n

    def _usr_return(self):
        """A motor visszatért a RET 0x0000-vel (az USR-cím alatti védelem):
        a valódi gépen a verem az USR-hívó BASIC-sorra áll vissza."""
        code = self.a
        self.handoff_count += 1
        if code == 0:
            self.stop_reason = "program vége (A=0)"
            self.running = False
            return
        # A=1: a BASIC a 6. sor IF USR...THEN LOAD-jával folytatódik,
        #      majd a 7. sor (RAND USR) újra behívja a motort.
        #      Az értelmező az E_PPC sorára áll vissza.
        self.stop_reason = "motor visszatért (A=%d)" % code
        self.running = False

    # --- képernyő (D_FILE alapján)
    def screen(self):
        df = self.peek16(0x400C)
        out = []
        for r in range(24):
            base = df + 1 + 33 * r
            row = []
            for i in range(32):
                c = self.ram[(base + i) & 0xFFFF]
                row.append(ZX2ASC.get(c & 0x7F, '?'))
            out.append("".join(row).rstrip())
        return "\n".join(out)

    def sysvars(self):
        return ("RAMTOP=0x%04X E_PPC=%d D_FILE=0x%04X DF_CC=0x%04X VARS=0x%04X "
                "E_LINE=0x%04X CH_ADD=0x%04X STKBOT=0x%04X STKEND=0x%04X "
                "DF_SZ=%d LAST-K=%02X%02X DEBOUNCE=%02X CDFLAG=%02X SP=0x%04X"
                % (self.peek16(0x4004), self.peek16(0x400A),
                   self.peek16(0x400C), self.peek16(0x400E),
                   self.peek16(0x4010), self.peek16(0x4014),
                   self.peek16(0x4016), self.peek16(0x401A),
                   self.peek16(0x401C), self.ram[0x4022],
                   self.ram[LASTK + 1], self.ram[LASTK], self.ram[DEBOUNCE],
                   self.ram[CDFLAG], self.sp))


def K(*ch):
    """K-mód szerinti kulcssor: betűkönél a kulcsszó-, számoknál a szám-
    billentyűt nyomjuk (shift nélkül)."""
    out = []
    for c in ch:
        if c == " ":
            out.append((0x7F, 0, False))
        else:
            r, col = KEY_POS[c.upper()]
            out.append((r, col, False))
    return out


def S(*ch):
    """SHIFT+billentyű sorozat."""
    out = []
    for c in ch:
        r, col = KEY_POS[c.upper()]
        out.append((r, col, True))
    return out


def NEWLINE_KEY():
    return (NEWLINE[0], NEWLINE[1], False)


def command(text):
    """K-módú parancs begépelése: pl. command('LOAD ""') → J, SHIFT+P,
    SHIFT+P, ENTER (a ROM maga dekódolja K-módban)."""
    seq = []
    for ch in text:
        if ch == '"':
            seq += S("P")
        elif ch == " ":
            seq += K(" ")
        else:
            seq += K(ch)
    seq.append(NEWLINE_KEY())
    return seq


def main():
    import json
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("tape", help="a .T81 kazetta útvonala")
    ap.add_argument("--ramtop", type=lambda x: int(x, 0), default=0x7FFF)
    ap.add_argument("--steps", type=int, default=60_000_000)
    ap.add_argument("--start-at", type=int, default=0)
    ap.add_argument("--keys", default="load-run",
                    help="load-run | run | list | none")
    ap.add_argument("--idle", type=int, default=400,
                    help="ennyi üresjárati lépés után állunk le")
    ap.add_argument("--json", default=None, help="eredmény JSON-fájlba")
    args = ap.parse_args()

    sim = RomSim(args.tape, ramtop=args.ramtop)
    sim.watch = {INITIAL: 0, IN_NAME: 0, BREAK4: 0, IN_BYTE: 0}
    print("blokkok:", [n for n, _ in sim.blocks])
    res = {}
    for addr in list(sim.watch):
        sim.watch[addr] = 0
    # 1) hideg indulás (RAM-CHECK hatása + INITIAL)
    sim.tape = Tape(sim.blocks, start_at=args.start_at)
    n = sim.rom_run(max_steps=3_000_000, spin_idle=args.idle)
    print("[1] hideg indulás: %d lépés, ok: %s" % (n, sim.stop_reason))
    print("    " + sim.sysvars())
    print(sim.screen())
    res["cold"] = {"steps": n, "reason": sim.stop_reason, "screen": sim.screen()}
    sim.stop_reason = None
    sim.running = True
    # 2) LOAD "" + RUN begépelése
    if args.keys == "load-run":
        sim.keys(command('LOAD ""'))
        n = sim.rom_run(max_steps=args.steps, spin_idle=args.idle)
        print("[2] LOAD: %d lépés, ok: %s  időtúllépések=%d  bájtok=%d "
              "frame_no=%d kulcspuffer=%d"
              % (n, sim.stop_reason, sim.timeouts, sim.tape_bytes,
                 sim.frame_no, len(sim.key_script)))
        print("    " + sim.sysvars())
        print("    INITIAL=%d IN-NAME=%d BREAK4=%d"
              % (sim.watch[INITIAL], sim.watch[IN_NAME], sim.watch[BREAK4]))
        print(sim.screen())
        res["load"] = {"steps": n, "reason": sim.stop_reason,
                       "timeouts": sim.timeouts, "bytes": sim.tape_bytes,
                       "initial": sim.watch[INITIAL],
                       "screen": sim.screen()}
        sim.stop_reason = None
        sim.running = True
        sim.keys(command('RUN'))
    elif args.keys == "run":
        sim.keys(command('RUN'))
    elif args.keys == "list":
        sim.keys(command('LIST'))
    if args.keys != "none":
        n = sim.rom_run(max_steps=args.steps, spin_idle=args.idle)
        print("[3] futás: %d lépés, ok: %s  INITIAL=%d IN-NAME=%d"
              % (n, sim.stop_reason, sim.watch[INITIAL], sim.watch[IN_NAME]))
        print("    PC=0x%04X  BC=0x%04X  " % (sim.pc, sim._bc()) + sim.sysvars())
        print("--- képernyő ---")
        scr = sim.screen()
        print(scr)
        res["run"] = {"steps": n, "reason": sim.stop_reason,
                      "initial": sim.watch[INITIAL], "pc": sim.pc,
                      "screen": scr, "sysvars": sim.sysvars()}
    if sim.save_log:
        names_ = [b for w, b in sim.save_log if w == "name"]
        data_ = [b for w, b in sim.save_log if w == "data"]
        print("SAVE %d név-bájt + %d adat-bájt" % (len(names_), len(data_)))
        res["save"] = {"name": names_, "data": data_}
    if args.json:
        with open(args.json, "w") as f:
            json.dump(res, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
