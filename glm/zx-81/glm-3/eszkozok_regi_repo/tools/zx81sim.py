#!/usr/bin/env python3
"""zx81sim.py — ZX81-szimulátor a Pico AI motor fejlesztéséhez.

Mit ad:
- Z80-mag (a tools/asm.py által támogatott részhalmozat)
- 16 KB RAM + ROM-csapdák (CLS=0A2A, SLOW=0F2B, KEYBOARD=02BB, SET-FAST=02E7)
- D_FILE-ŐRSZEM: minden képernyő-memóriába írás ellenőrzött — tiltott kód
  (a „futó fekete csíkok" osztálya) azonnal SimError-t dob
- FRAMES-óra (20 ms képkockánként), SLOW/FAST mód
- billentyű-mátrix (8x5) szkriptezhető eseménysorral
- EO81/.T81/.P konténer: a ROM LOAD/SAVE lánc modellezése
  (a motor USR-visszatérése: A=1 -> LOAD, A=2 -> SAVE, A=0 -> program vége)
- képernyő-kiírás szövegként (inverz cellák kisbetűvel)

Használat:
    python3 zx81sim.py dist/ZX81PICO.T81 --script tests/chat_demo.txt
    python3 zx81sim.py --selftest
Vagy a Python API:
    sim = ZX81Sim(open('dist/ZX81PICO.T81','rb').read())
    sim.quickload('PICOBOOT')
    sim.type_text('...') ; sim.run_until_idle()
"""
import sys
import time

# ---------------------------------------------------------------- konstansok

VERSN = 0x4009
D_FILE_VAR = 0x400C
VARS_VAR = 0x4010
E_LINE_VAR = 0x4014
FRAMES = 0x4034
SPWORD = 0x4026
DFILE_DEFAULT = 0x7B00
PROG = 0x407D
ENGINE_ORG = 0x4082
RET_SENTINEL = 0x0000   # az USR-hívás visszatérési jelzője
IDLE_FLAG = 0x7A60      # a motor ide ír 0x55-öt a bemenet-várakozáskor

ROM_CLS = 0x0A2A
ROM_SLOW = 0x0F2B
ROM_SETFAST = 0x02E7
ROM_SLOWFAST = 0x0207
ROM_KEYBOARD = 0x02BB
ROM_DISPLAY = 0x0229
ROM_INPUT = 0x0EE9
ROM_LOAD = 0x0340

# 8x5-ös billentyűmátrix (port magas bájtja -> 5 kulcs, b0..b4)
# A VALÓDI ZX81-elrendezés (EightyOne forrás, kbstatus.cpp KBZX81 tábla —
# a felhasználó emulátora; a ROM dekóderével empirikusan is igazolva):
#   FE: SHIFT Z X C V    FD: A S D F G    FB: Q W E R T
#   F7: 1 2 3 4 5        EF: 0 9 8 7 6    DF: P O I U Y
#   BF: NEWLINE L K J H  7F: SPACE . M N B
KEY_ROWS = {0xFE: "\x00ZXCV", 0xFD: "ASDFG", 0xFB: "QWERT", 0xF7: "12345",
            0xEF: "09876", 0xDF: "POIUY", 0xBF: "\nLKJH", 0x7F: " .MNB"}
# \x00 = SHIFT, \n = NEWLINE; RUBOUT = SHIFT+'0' (nincs külön gomb)
KEY_POS = {}
for _row, _keys in KEY_ROWS.items():
    for _col, _k in enumerate(_keys):
        if _k not in KEY_POS:
            KEY_POS[_k] = (_row, _col)

# ZX81 kód -> ASCII (a D_FILE-őrszem és a képernyő-dump számára)
ZX2ASC = {}
for _i in range(26):
    ZX2ASC[0x26 + _i] = chr(65 + _i)
for _i in range(10):
    ZX2ASC[0x1C + _i] = str(_i)
ZX2ASC.update({0x00: " ", 0x1B: ".", 0x1A: ",", 0x0F: "?", 0x0E: ":",
               0x16: "-", 0x14: "=", 0x15: "+", 0x17: "*", 0x18: "/",
               0x10: "(", 0x11: ")", 0x13: "<", 0x12: ">", 0x19: ";",
               0x0B: '"', 0x0D: "$", 0x0C: "#"})


class SimError(Exception):
    pass


# ---------------------------------------------------------------- EO81/P

def load_blocks(path):
    """A .T81 kazetta blokkjai. Két elfogadott formátum:
    - [EO81-mágia] + blokkok (a régi, saját konténer — visszafelé kompat.)
    - blokkok közvetlenül: [név 32][hossz ASCII 16][adat] (a bizonyított
      ElevenOne-formátum; a hosszmező balra zárt ASCII, jobb oldalon \0)
    A sima .P eget üres névvel, egy blokkként adjuk vissza."""
    data = open(path, "rb").read()
    blocks = []
    i = 4 if data[:4] == b"EO81" else 0
    while i + 48 <= len(data):
        name_b = data[i:i + 32].rstrip(b"\0")
        len_b = data[i + 32:i + 48].rstrip(b"\0")
        if not len_b.isdigit():
            break            # nem blokkfejléc — maradék .P-ként kezeljük
        name = name_b.decode("ascii", "replace")
        n = int(len_b)
        blocks.append((name, data[i + 48:i + 48 + n]))
        i += 48 + n
    if blocks:
        return blocks
    return [("", data)]   # sima .P


def zx_name_to_ascii(codes):
    out = []
    for c in codes:
        if 0x26 <= c <= 0x3F:
            out.append(chr(65 + c - 0x26))
        elif 0x1C <= c <= 0x25:
            out.append(str(c - 0x1C))
        elif c == 0x16:
            out.append("-")
        else:
            out.append("?")
    return "".join(out)


# ---------------------------------------------------------------- Z80 mag

F_S, F_Z, F_H, F_P, F_N, F_C = 0x80, 0x40, 0x10, 0x04, 0x02, 0x01


class ZX81Sim:
    def __init__(self, container, trace=False):
        self.blocks = (load_blocks(container) if isinstance(container, str)
                       else container)
        self.ram = bytearray(0x8000)
        self.ram[0x4000:0x4008] = b"\x00" * 8
        self.a = self.b = self.c = self.d = self.e = self.h = self.l = 0
        self.f = 0
        self.f2 = 0
        self.sp = 0
        self.pc = 0
        self.iy = 0x4000
        self.ix = 0
        self.a2 = 0
        self.regs2 = [0] * 6      # b2,c2,d2,e2,h2,l2 (EXX)
        self.ireg = 0
        self.rreg = 0
        self.rom_exec = False     # valódi ROM-mód: a ROM bájtjai futnak
        self.halted = False
        self.nmi_countdown = 26   # ~207 T-állapot = 26 lépés (soronkénti NMI)
        self.nmi_active = False
        self.nmi_ret = None
        self.slow = True
        self.cycles = 0
        self.frames = 0
        self.trace = trace
        self.log = []
        self.held = set()          # (row, col) lenyomva
        self.keyq = []             # (frame, muvelet, (row,col))
        self.running = False
        self.handoff_count = 0
        self.steps = 0
        self.stop_reason = None
        self.saved_blocks = []     # (név, kép) — a SAVE-trap eredménye
        self.ram[IDLE_FLAG] = 0

    # --- memória (D_FILE-őrszemmel)
    def _dfile(self):
        return self.ram[D_FILE_VAR] | (self.ram[D_FILE_VAR + 1] << 8)

    def peek(self, addr):
        return self.ram[addr & 0xFFFF]

    def poke(self, addr, val):
        addr &= 0xFFFF
        val &= 0xFF
        if addr < 0x2000:
            raise SimError(f"ROM-írás! 0x{addr:04X} <- 0x{val:02X} "
                           f"(PC=0x{self.pc:04X})")
        df = self._dfile()
        if (not self.rom_exec and df <= addr < df + 793
                and val not in (0x76,)):
            # érvényes: 0x00-0x3F (normál) vagy 0x80-0xBF (inverz)
            if not (val <= 0x3F or 0x80 <= val <= 0xBF):
                raise SimError(
                    f"D_FILE-ŐRSZEM: tiltott bájt 0x{val:02X} @ 0x{addr:04X} "
                    f"(PC=0x{self.pc:04X}) — ez okozná a futó fekete csíkokat!")
        self.ram[addr] = val

    def poke16(self, addr, val):
        self.poke(addr, val & 0xFF)
        self.poke(addr + 1, (val >> 8) & 0xFF)

    def peek16(self, addr):
        return self.ram[addr] | (self.ram[addr + 1] << 8)

    def w(self, addr, val):   # őrszem NÉLKÜLI írás (rendszer-változók)
        self.ram[addr] = val & 0xFF

    # --- regiszter-párok
    def _hl(self):
        return (self.h << 8) | self.l

    def _set_hl(self, v):
        self.h, self.l = (v >> 8) & 0xFF, v & 0xFF

    def _bc(self):
        return (self.b << 8) | self.c

    def _set_bc(self, v):
        self.b, self.c = (v >> 8) & 0xFF, v & 0xFF

    def _de(self):
        return (self.d << 8) | self.e

    def _set_de(self, v):
        self.d, self.e = (v >> 8) & 0xFF, v & 0xFF

    # --- verem
    def push(self, v):
        self.sp = (self.sp - 2) & 0xFFFF
        self.ram[self.sp] = v & 0xFF
        self.ram[self.sp + 1] = (v >> 8) & 0xFF

    def pop(self):
        v = self.ram[self.sp] | (self.ram[self.sp + 1] << 8)
        self.sp = (self.sp + 2) & 0xFFFF
        return v

    # --- zászlók
    def _sz(self, r):
        self.f = (self.f & ~(F_S | F_Z | F_P)) | (F_Z if r == 0 else 0) \
                 | (F_S if r & 0x80 else 0)

    def _add(self, x, y, carry=0, word=False):
        mask = 0xFFFF if word else 0xFF
        r = (x + y + carry) & mask
        c = 1 if x + y + carry > mask else 0
        h = 1 if ((x & 0xF if not word else x & 0xFFF)
                  + (y & 0xF if not word else y & 0xFFF) + carry) > \
            (0xF if not word else 0xFFF) else 0
        v = 1 if (~(x ^ y) & (x ^ r) & (0x8000 if word else 0x80)) else 0
        self.f = (self.f & ~(F_C | F_H | F_N | F_S | F_Z | F_P)) \
                 | (c * F_C) | (h * F_H) | (v * F_P) \
                 | (F_Z if (r & mask) == 0 else 0) \
                 | (F_S if r & (0x8000 if word else 0x80) else 0)
        return r & 0xFF if not word else r

    def _sub(self, x, y, borrow=0, word=False):
        mask = 0xFFFF if word else 0xFF
        r = (x - y - borrow) & mask
        c = 1 if x - y - borrow < 0 else 0
        v = 1 if ((x ^ y) & (x ^ r) & (0x8000 if word else 0x80)) else 0
        self.f = (self.f & ~(F_C | F_H | F_N | F_S | F_Z | F_P)) \
                 | F_N | (c * F_C) | (v * F_P) \
                 | (1 if ((x & 0xF) - (y & 0xF) - borrow) < 0 else 0) * F_H \
                 | (F_Z if (r & mask) == 0 else 0) \
                 | (F_S if r & (0x8000 if word else 0x80) else 0)
        return r & 0xFF if not word else r

    def _logic(self, r, half=False):
        self.f = (self.f & ~(F_C | F_N | F_H | F_S | F_Z)) \
                 | (F_H if half else 0) \
                 | (F_Z if r == 0 else 0) | (F_S if r & 0x80 else 0)

    def _inc8(self, v):
        r = (v + 1) & 0xFF
        self.f = (self.f & F_C) \
                 | (F_Z if r == 0 else 0) | (F_S if r & 0x80 else 0) \
                 | (F_H if (v & 0x0F) == 0x0F else 0)
        return r

    def _dec8(self, v):
        r = (v - 1) & 0xFF
        self.f = (self.f & F_C) | F_N \
                 | (F_Z if r == 0 else 0) | (F_S if r & 0x80 else 0) \
                 | (F_H if (v & 0x0F) == 0 else 0)
        return r

    def _cond(self, cc):
        return {0: not self.f & F_Z, 1: bool(self.f & F_Z),
                2: not self.f & F_C, 3: bool(self.f & F_C),
                4: not self.f & F_P, 5: bool(self.f & F_P),
                6: not self.f & F_S, 7: bool(self.f & F_S)}[cc]

    # --- keret/fájl-elemek
    def _advance_frame(self):
        self.frames += 1
        # ROM-módban a FRAMES csak akkor él, ha a videó/NMI aktív
        # (CDFLAG bit7) — különben a ROM RAM-CHECK-jét hamisan
        # megszakítanánk (a valódi gépen a RESET után a NTI még néma)
        if self.rom_exec and not (self.ram[0x403B] & 0x80):
            while self.keyq and self.keyq[0][0] <= self.frames:
                _, act, key = self.keyq.pop(0)
                if act == "down":
                    self.held.add(key)
                else:
                    self.held.discard(key)
            return
        self.v = (self.peek16(FRAMES) + 1) & 0xFFFF
        self.w(FRAMES, self.v & 0xFF)
        self.w(FRAMES + 1, self.v >> 8)
        # billentyű-események
        while self.keyq and self.keyq[0][0] <= self.frames:
            _, act, key = self.keyq.pop(0)
            if act == "down":
                self.held.add(key)
            else:
                self.held.discard(key)

    def keyboard_scan(self):
        """ROM KEYBOARD (02BB) modell: HL = nyers kulcs-bitmap
        (H = kulcsbitek, L = sor-kiválasztó bitek). A motor saját szkent
        futtat, ez csak a teljeség kedvéért."""
        h, l = 0xFF, 0xFF
        for row, col in self.held:
            l &= row
            h &= 0xE0 | ((0xFF ^ (1 << col)) & 0xFF)
        self.h, self.l = h, l
        return h, l

    # --- betöltés / mentés (a ROM LOAD/SAVE lánc modellje)
    def _walk_lines(self):
        lines = {}
        p = PROG
        while self.ram[p] != 0x76:
            num = (self.ram[p] << 8) | self.ram[p + 1]
            ln = self.ram[p + 2] | (self.ram[p + 3] << 8)
            body = self.ram[p + 4:p + 4 + ln - 1]
            lines[num] = (p, body)
            p += 4 + ln
            if p >= 0x7FFF:
                break
        return lines

    def get_load_name(self):
        lines = self._walk_lines()
        _, body = lines[2]
        return zx_name_to_ascii(body[24:32])

    def get_save_name(self):
        lines = self._walk_lines()
        _, body = lines[3]
        return zx_name_to_ascii(body[24:32])

    def quickload(self, name, log=True):
        for bn, data in self.blocks:
            if bn == name:
                self.ram[VERSN:VERSN + len(data)] = data
                self.ram[IDLE_FLAG] = 0
                self.sp = 0x7FFD       # fix 16K veremtető (a 0x4026-os
                self.push(RET_SENTINEL)  # szó LAST-K, nem SP-forrás!)
                self.pc = ENGINE_ORG
                self.running = True
                if log:
                    self.log.append(f"TAPE: LOAD {name} — {len(data)} bájt "
                                    f"(0x{VERSN:04X}-0x{VERSN + len(data):04X})")
                return True
        raise SimError(f"nincs ilyen blokk: {name!r}")

    def do_save(self, name):
        vend = self.peek16(VARS_VAR) + 1
        img = bytes(self.ram[VERSN:vend])
        self.saved_blocks.append((name, img))
        for i, (bn, _) in enumerate(self.blocks):
            if bn == name:
                self.blocks[i] = (name, img)
                self.log.append(f"TAPE: SAVE {name} — {len(img)} bájt felülírva")
                return
        self.blocks.append((name, img))
        self.log.append(f"TAPE: SAVE {name} — {len(img)} bájt (új blokk)")

    def do_load(self, name):
        self.quickload(name)

    # --- billentyű-injektálás
    def _press(self, key, shift=False, hold=2, off=0):
        """A gomb lenyomása off képkockával eltolva (a TYPE egymás UTÁN
        üti a billentyűket, nem egyszerre!)."""
        k = KEY_POS[key]
        t0 = self.frames + 1 + off
        self.keyq.append((t0, "down", k))
        if shift:
            sh = KEY_POS["\x00"]
            self.keyq.append((t0, "down", sh))
            self.keyq.append((t0 + hold, "up", sh))
        self.keyq.append((t0 + hold, "up", k))
        self.keyq.sort(key=lambda e: e[0])

    def type_text(self, text):
        """Szöveg beírása. ' ' = SHIFT+NEWLINE, '\\n' = NEWLINE,
        {S1}..{S9} = SHIFT+1..9, {SS} = SHIFT+S, {RUB} = RUBOUT gomb.
        Minden billentyű külön képkocka-csoportban (2 tartás + 2 szünet)."""
        i = 0
        off = 60          # lead-in: ~1,2 s csend (a rajzolás lecsengjen,
                          # az első gomb ne a kimenet alatt vesszen el)
        while i < len(text):
            if text[i] == "{":
                j = text.index("}", i)
                tok = text[i + 1:j]
                if tok == "SS":
                    self._press("S", shift=True, off=off)
                elif tok == "RUB":
                    self._press("0", shift=True, off=off)
                elif tok == "SNL":
                    self._press("\n", shift=True, off=off)
                elif tok.startswith("S"):
                    self._press(tok[1], shift=True, off=off)
                else:
                    raise SimError(f"ismeretlen billentyű-jel: {tok}")
                i = j + 1
            else:
                ch = text[i]
                if ch == " ":
                    self._press(" ", off=off)   # szóköz = VALÓDI spacegomb
                elif ch == "\n":
                    self._press("\n", off=off)
                else:
                    up = ch.upper()
                    if up in KEY_POS:
                        self._press(up, shift=ch.isupper(), off=off)
                    else:
                        raise SimError(f"nincs ilyen billentyű: {ch!r}")
                i += 1
            off += 4

    # --- futtatás
    def run(self, max_steps=2_000_000):
        n = 0
        while n < max_steps and self.running:
            self.step()
            n += 1
        return n

    def run_until_idle(self, max_steps=2_000_000):
        """Fut, amíg a motor nyugalmi állapotba nem kerül: a motor a
        bemenet-várakozáskor 0x55-öt ír az IDLE_FLAG (0x7A60) címre, és
        addig futunk, amíg ez fennáll és nincs lenyomott/sorban álló
        billentyű. (A képkockák addig is járnak, ahogy a valóságban.)"""
        n = 0
        calm = 0
        while n < max_steps and self.running:
            self.step()
            n += 1
            if self.ram[IDLE_FLAG] == 0x55 and not self.held and not self.keyq:
                calm += 1
                if calm > 4096:
                    return n
            else:
                calm = 0
        return n

    def step(self):
        self.steps += 1
        self.cycles += 8
        if self.cycles >= (16000 if self.slow else 33000):
            self.cycles = 0
            self._advance_frame()
        pc = self.pc
        if pc < 0x2000 and not self.rom_exec:
            self._rom_trap(pc)
            return
        op = self.ram[pc]
        if op in (0xDD, 0xFD):
            self._exec_ixiy(op)
            return
        npc = pc + 1

        # --- LD r,r' / (HL)
        if 0x40 <= op < 0x80 and op != 0x76:
            d, s = (op >> 3) & 7, op & 7
            if s == 6:
                self._st_r(d, self.ram[self._hl()])
            elif d == 6:
                self.poke(self._hl(), self._r_r(s))
            else:
                self._st_r(d, self._r_r(s))
            self.pc = npc
            return
        # --- LD r,n
        if (op & 0xC7) == 0x06:
            d = (op >> 3) & 7
            v = self.ram[npc]
            if d == 6:
                self.poke(self._hl(), v)
            else:
                self._st_r(d, v)
            self.pc = npc + 1
            return
        # --- DEC r / (HL) (a carry-t NEM bántja — valós Z80!)
        if (op & 0xC7) == 0x05:
            d = (op >> 3) & 7
            v = self.ram[self._hl()] if d == 6 else self._r_r(d)
            self._st_r(d, self._dec8(v)) if d != 6 else None
            if d == 6:
                self.poke(self._hl(), self._dec8(v))
            self.pc = npc
            return
        # --- INC r / (HL) (a carry-t NEM bántja — valós Z80!)
        if (op & 0xC7) == 0x04:
            d = (op >> 3) & 7
            v = self.ram[self._hl()] if d == 6 else self._r_r(d)
            if d == 6:
                self.poke(self._hl(), self._inc8(v))
            else:
                self._st_r(d, self._inc8(v))
            self.pc = npc
            return
        # --- ALU (r / (HL) / n formák)
        if 0x80 <= op <= 0xBF or op in (0xC6, 0xCE, 0xD6, 0xDE, 0xE6, 0xEE,
                                        0xF6, 0xFE):
            kind = op & 0xF8
            if op in (0xC6, 0xCE, 0xD6, 0xDE, 0xE6, 0xEE, 0xF6, 0xFE):
                v = self.ram[npc]
                npc += 1
            elif (op & 7) == 6:
                v = self.ram[self._hl()]
            else:
                v = self._r_r(op & 7)
            if kind in (0x80, 0xC0):        # ADD
                self.a = self._add(self.a, v)
            elif kind in (0x88, 0xC8):      # ADC
                self.a = self._add(self.a, v, 1 if self.f & F_C else 0)
            elif kind in (0x90, 0xD0):      # SUB
                self.a = self._sub(self.a, v)
            elif kind in (0x98, 0xD8):      # SBC
                self.a = self._sub(self.a, v, 1 if self.f & F_C else 0)
            elif kind in (0xA0, 0xE0):      # AND
                self.a = self.a & v
                self._logic(self.a, half=True)
            elif kind in (0xA8, 0xE8):      # XOR
                self.a = (self.a ^ v) & 0xFF
                self._logic(self.a)
            elif kind in (0xB0, 0xF0):      # OR
                self.a = self.a | v
                self._logic(self.a)
            else:                            # CP — csak a zászlók
                self._sub(self.a, v)
            self.pc = npc
            return
        # --- LD rr,nn / INC/DEC rr / ADD HL,rr
        if (op & 0xCF) == 0x01:
            q = op >> 4
            v = self.ram[npc] | (self.ram[npc + 1] << 8)
            self._st_rr(q, v)
            self.pc = npc + 2
            return
        if (op & 0xCF) == 0x03:
            q = op >> 4
            r = (self._rr_r(q) + 1) & 0xFFFF   # INC rr: zászlókat nem bántja
            self._st_rr(q, r)
            self.pc = npc
            return
        if (op & 0xCF) == 0x0B:
            q = op >> 4
            cur = self._rr_r(q)
            r = (cur - 1) & 0xFFFF
            self._st_rr(q, r)
            self.f |= F_N
            self.pc = npc
            return
        if op in (0x09, 0x19, 0x29, 0x39):
            q = op >> 4
            r = self._add(self._hl(), self._rr_r(q), word=True)
            self._set_hl(r)
            self.pc = npc
            return
        # --- egyszerűek
        simple = {0x00: "NOP", 0x76: "HALT", 0x27: "DAA", 0x2F: "CPL",
                  0x3F: "CCF", 0x37: "SCF", 0xF3: "DI", 0xFB: "EI",
                  0x07: "RLCA", 0x0F: "RRCA", 0x17: "RLA", 0x1F: "RRA",
                  0x08: "EXAF", 0xD9: "EXX"}
        if op in simple:
            what = simple[op]
            if what == "NOP" or what in ("DI", "EI"):
                pass
            elif what == "HALT":
                if self.rom_exec:
                    self.halted = True
                    self.pc = npc
                    return
                raise SimError("HALT a motorban (PC=0x%04X) — a motor "
                               "sose álljon le így" % pc)
            elif what == "EXAF":
                self.a, self.a2 = self.a2, self.a
                self.f, self.f2 = self.f2, self.f
            elif what == "EXX":
                for i, r in enumerate(("b", "c", "d", "e", "h", "l")):
                    cur = getattr(self, r)
                    setattr(self, r, self.regs2[i])
                    self.regs2[i] = cur
            elif what == "CPL":
                self.a = ~self.a & 0xFF
                self.f |= F_H | F_N
            elif what == "SCF":
                self.f = (self.f | F_C) & ~F_N & ~F_H
            elif what == "CCF":
                self.f = (self.f ^ F_C) & ~F_N
            elif what == "DAA":
                self.a = self._daa()
            elif what == "RLCA":
                self.f = (self.f & ~F_C) | (F_C if self.a & 0x80 else 0)
                self.a = ((self.a << 1) | (self.a >> 7)) & 0xFF
            elif what == "RRCA":
                self.f = (self.f & ~F_C) | (F_C if self.a & 1 else 0)
                self.a = ((self.a >> 1) | (self.a << 7)) & 0xFF
            elif what == "RLA":
                c = self.a & 0x80
                self.a = ((self.a << 1) | (1 if self.f & F_C else 0)) & 0xFF
                self.f = (self.f & ~F_C) | (F_C if c else 0)
            elif what == "RRA":
                c = self.a & 1
                self.a = (self.a >> 1) | (0x80 if self.f & F_C else 0)
                self.f = (self.f & ~F_C) | (F_C if c else 0)
            self.pc = npc
            return
        # --- ED xx
        if op == 0xED:
            sub = self.ram[npc]
            npc += 1
            if sub == 0x78:                       # IN A,(C)
                self.a = self._in(self._bc())
            elif sub == 0x79:                     # OUT (C),A
                self._out(self._bc(), self.a)
            elif sub == 0xB0:                     # LDIR
                self.poke(self._de(), self.ram[self._hl()])
                self._set_hl((self._hl() + 1) & 0xFFFF)
                self._set_de((self._de() + 1) & 0xFFFF)
                self._set_bc((self._bc() - 1) & 0xFFFF)
                if self._bc() != 0:
                    self.pc = pc  # újra az ED B0-ot
                    self.cycles += 16
                    return
            elif sub == 0xB8:                     # LDDR
                self.poke(self._de(), self.ram[self._hl()])
                self._set_hl((self._hl() - 1) & 0xFFFF)
                self._set_de((self._de() - 1) & 0xFFFF)
                self._set_bc((self._bc() - 1) & 0xFFFF)
                if self._bc() != 0:
                    self.pc = pc
                    self.cycles += 16
                    return
            elif sub == 0x44:                     # NEG
                self.a = self._sub(0, self.a)
            elif sub in (0x4D, 0x45):             # RETI / RETN
                self.pc = self.pop()
                return
            elif sub in (0x4B, 0x5B, 0x6B, 0x7B):  # LD rr,(nn)
                addr = self.ram[npc] | (self.ram[npc + 1] << 8)
                npc += 2
                v = self.ram[addr] | (self.ram[addr + 1] << 8)
                if sub == 0x4B:
                    self._set_bc(v)
                elif sub == 0x5B:
                    self._set_de(v)
                elif sub == 0x6B:
                    self._set_hl(v)
                else:
                    self.sp = v
            elif sub in (0x43, 0x53, 0x63, 0x73):  # LD (nn),rr
                addr = self.ram[npc] | (self.ram[npc + 1] << 8)
                npc += 2
                if sub == 0x43:
                    v = self._bc()
                elif sub == 0x53:
                    v = self._de()
                elif sub == 0x63:
                    v = self._hl()
                else:
                    v = self.sp
                self.ram[addr] = v & 0xFF
                self.ram[addr + 1] = v >> 8
            elif sub in (0x46, 0x56, 0x5E, 0x4E, 0x66, 0x6E):
                pass  # IM 0/1/2 — funkcionálisan semleges (NMI-modell)
            elif sub == 0x47:                     # LD I,A
                self.ireg = self.a
            elif sub == 0x4F:                     # LD R,A
                self.rreg = self.a
            elif sub == 0x5F:                     # LD A,R
                self.a = (self.rreg + (self.steps >> 1)) & 0xFF
                self.f = (self.f & ~(F_S | F_Z | F_H)) | \
                        (F_S if self.a & 0x80 else 0) | \
                        (F_Z if self.a == 0 else 0)
            elif sub == 0xA0:                     # LDI
                self.poke(self._de(), self.ram[self._hl()])
                self._set_hl((self._hl() + 1) & 0xFFFF)
                self._set_de((self._de() + 1) & 0xFFFF)
                self._set_bc((self._bc() - 1) & 0xFFFF)
                self.f = (self.f & ~(F_H | F_N | F_P)) | (F_H if
                          self._bc() else 0)
            elif sub == 0xB1:                     # CPIR
                v = self.ram[self._hl()]
                r = self._sub(self.a, v)
                self._set_hl((self._hl() + 1) & 0xFFFF)
                self._set_bc((self._bc() - 1) & 0xFFFF)
                if self._bc() and r != 0:
                    self.pc = pc
                    self.cycles += 16
                    return
            elif sub in (0x42, 0x52, 0x62, 0x72, 0x4A, 0x5A, 0x6A, 0x7A):
                q = (sub >> 4) & 3      # JAVÍTVA: korábban 'sub & 0x30 >> 4'
                # volt — a >> szorosabban köt, mint a &, így a q mindig 2
                # lett: minden SBC/ADC HL,rr valójában SBC/ADC HL,HL volt!
                # (Ettől a TEST-ROOM SBC HL,SP-je mindig 0-t adott és
                # fals REPORT-4-gel tért vissza — a begépelés sosem
                # sikerült a szimulátorban!)
                if sub & 0x08:                    # ADC HL,rr
                    r = self._add(self._hl(), self._rr_r(q),
                                  1 if self.f & F_C else 0, word=True)
                else:                             # SBC HL,rr
                    r = self._sub(self._hl(), self._rr_r(q),
                                  1 if self.f & F_C else 0, word=True)
                self._set_hl(r)
            else:
                raise SimError(f"ED {sub:02X} nincs implementálva "
                               f"(PC=0x{pc:04X})")
            self.pc = npc
            return
        # --- CB xx (forgatások, BIT/RES/SET)
        if op == 0xCB:
            sub = self.ram[npc]
            npc += 1
            r = (sub >> 3) & 7
            bit = (sub >> 3) & 7
            if sub < 0x40:
                v = self.ram[self._hl()] if (sub & 7) == 6 else self._r_r(sub & 7)
                names = {0: "RLC", 1: "RRC", 2: "RL", 3: "RR",
                         4: "SLA", 5: "SRA", 6: "SLL", 7: "SRL"}
                k = (sub >> 3) & 7
                if k == 0:      # RLC
                    c = v & 0x80
                    v = ((v << 1) | (1 if c else 0)) & 0xFF
                    self.f = (self.f & ~F_C) | (F_C if c else 0)
                elif k == 1:    # RRC
                    c = v & 1
                    v = (v >> 1) | (0x80 if c else 0)
                    self.f = (self.f & ~F_C) | (F_C if c else 0)
                elif k == 2:    # RL
                    c = v & 0x80
                    v = ((v << 1) | (1 if self.f & F_C else 0)) & 0xFF
                    self.f = (self.f & ~F_C) | (F_C if c else 0)
                elif k == 3:    # RR
                    c = v & 1
                    v = (v >> 1) | (0x80 if self.f & F_C else 0)
                    self.f = (self.f & ~F_C) | (F_C if c else 0)
                elif k == 4:    # SLA
                    self.f = (self.f & ~F_C) | (F_C if v & 0x80 else 0)
                    v = (v << 1) & 0xFF
                elif k == 5:    # SRA
                    self.f = (self.f & ~F_C) | (F_C if v & 1 else 0)
                    v = (v >> 1) | (v & 0x80)
                else:           # SRL
                    self.f = (self.f & ~F_C) | (F_C if v & 1 else 0)
                    v = v >> 1
                self._sz(v)
                if (sub & 7) == 6:
                    self.poke(self._hl(), v)
                else:
                    self._st_r(sub & 7, v)
            elif sub < 0x80:    # BIT b,r
                v = self.ram[self._hl()] if (sub & 7) == 6 else self._r_r(sub & 7)
                b = (sub >> 3) & 7
                self.f = (self.f & ~(F_Z | F_N | F_H)) | F_H | F_N | \
                         (F_Z if not (v & (1 << b)) else 0)
            elif sub < 0xC0:    # RES b,r
                v = self.ram[self._hl()] if (sub & 7) == 6 else self._r_r(sub & 7)
                b = (sub >> 3) & 7
                v &= ~(1 << b) & 0xFF
                if (sub & 7) == 6:
                    self.poke(self._hl(), v)
                else:
                    self._st_r(sub & 7, v)
            else:               # SET b,r
                v = self.ram[self._hl()] if (sub & 7) == 6 else self._r_r(sub & 7)
                b = (sub >> 3) & 7
                v |= 1 << b
                if (sub & 7) == 6:
                    self.poke(self._hl(), v)
                else:
                    self._st_r(sub & 7, v)
            self.pc = npc
            return
        # --- A,(BC)/(DE) és (BC)/(DE),A
        if op == 0x0A:
            self.a = self.ram[self._bc()]
        elif op == 0x1A:
            self.a = self.ram[self._de()]
        elif op == 0x02:
            self.poke(self._bc(), self.a)
        elif op == 0x12:
            self.poke(self._de(), self.a)
        elif op == 0x3A:
            self.a = self.ram[self.ram[npc] | (self.ram[npc + 1] << 8)]
            npc += 2
        elif op == 0x32:
            self.poke(self.ram[npc] | (self.ram[npc + 1] << 8), self.a)
            npc += 2
        elif op == 0x2A:
            self._set_hl(self.peek16(self.ram[npc] | (self.ram[npc + 1] << 8)))
            npc += 2
        elif op == 0x22:
            self.poke16(self.ram[npc] | (self.ram[npc + 1] << 8), self._hl())
            npc += 2
        elif op == 0xF9:
            self.sp = self._hl()
        elif op == 0xE9:
            self.pc = self._hl()
            return
        elif op == 0xEB:
            t = self._de()
            self._set_de(self._hl())
            self._set_hl(t)
        elif op == 0x08:
            t = self.f
            self.f = self.f2 if hasattr(self, "f2") else 0
            self.f2 = t
        elif op == 0xE3:   # EX (SP),HL
            t = self.peek16(self.sp)
            self.poke16(self.sp, self._hl())
            self._set_hl(t)
        elif op in (0xC5, 0xD5, 0xE5, 0xF5):
            q = ["BC", "DE", "HL", "AF"][(op >> 4) - 0xC]
            if q == "AF":
                self.push((self.a << 8) | self.f)
            else:
                self.push(self._rr_r({"BC": 0, "DE": 1, "HL": 2, "SP": 3}[q]))
        elif op in (0xC1, 0xD1, 0xE1, 0xF1):
            q = ["BC", "DE", "HL", "AF"][(op >> 4) - 0xC]
            v = self.pop()
            if q == "AF":
                self.a, self.f = v >> 8, v & 0xFF
            else:
                self._st_rr({"BC": 0, "DE": 1, "HL": 2, "SP": 3}[q], v)
        elif op == 0xC9:
            addr = self.pop()
            if addr == RET_SENTINEL:
                self._usr_return()
                return
            self.pc = addr
            return
        elif op in (0xC0, 0xC8, 0xD0, 0xD8, 0xE0, 0xE8, 0xF0, 0xF8):
            cc = (op >> 3) & 7
            if self._cond(cc):
                addr = self.pop()
                if addr == RET_SENTINEL:
                    self._usr_return()
                    return
                self.pc = addr
                return
        elif op == 0xC3:
            self.pc = self.ram[npc] | (self.ram[npc + 1] << 8)
            return
        elif op in (0xC2, 0xCA, 0xD2, 0xDA, 0xE2, 0xEA, 0xF2, 0xFA):
            cc = (op >> 3) & 7
            tgt = self.ram[npc] | (self.ram[npc + 1] << 8)
            self.pc = tgt if self._cond(cc) else npc + 2
            return
        elif op == 0x18 or (op & 0xE7) in (0x20, 0x28, 0x30, 0x38):
            d = self.ram[npc]
            d = d - 256 if d > 127 else d
            if op == 0x18:
                self.pc = npc + 1 + d
                return
            cc = (op >> 3) & 3
            if self._cond(cc):
                self.pc = npc + 1 + d
                return
            self.pc = npc + 1
            return
        elif op == 0x10:  # DJNZ
            d = self.ram[npc]
            d = d - 256 if d > 127 else d
            self.b = (self.b - 1) & 0xFF
            if self.b != 0:
                self.pc = npc + 1 + d
                return
            self.pc = npc + 1
            return
        elif op == 0xCD or op in (0xC4, 0xCC, 0xD4, 0xDC, 0xE4, 0xEC,
                                  0xF4, 0xFC):
            cc = 0 if op == 0xCD else (op >> 3) & 7
            tgt = self.ram[npc] | (self.ram[npc + 1] << 8)
            if op == 0xCD or self._cond(cc):
                self.push(npc + 2)
                self.pc = tgt
                return
            self.pc = npc + 2
            return
        elif op == 0xDB:
            self.a = self._in(self.ram[npc])
            npc += 1
        elif op == 0xD3:
            self._out(self.ram[npc], self.a)
            npc += 1
        elif (op & 0xC7) == 0xC7:
            self.push(npc)
            self.pc = op & 0x38
            return
        else:
            raise SimError(f"nem implementált opkód 0x{op:02X} "
                           f"(PC=0x{pc:04X})")
        self.pc = npc

    # --- IX/IY (DD/FD) utasításkészlet — a ZX81 ROM-hoz kell
    def _ixiy_reg(self):
        return self.ix if self._pfx == 0xDD else self.iy

    def _set_ixiy_reg(self, v):
        if self._pfx == 0xDD:
            self.ix = v
        else:
            self.iy = v

    def _exec_ixiy_cb(self, mop, addr):
        """FD CB dd op: BIT/RES/SET n,(IY+d)"""
        grp = mop & 0xC0
        bit = (mop >> 3) & 7
        if grp == 0x40:                       # BIT n,(IY+d)
            v = self.ram[addr]
            z = 0 if (v >> bit) & 1 else F_Z
            self.f = (self.f & ~(F_N | F_Z | F_H | F_P)) | z | F_H | \
                     (F_P if (v << bit) & 0x80 and False else 0)
        elif grp == 0x80:                     # RES n,(IY+d)
            self.poke(addr, self.ram[addr] & ~(1 << bit) & 0xFF)
        else:                                 # SET n,(IY+d)
            self.poke(addr, self.ram[addr] | (1 << bit))

    def _exec_ixiy(self, prefix):
        self._pfx = prefix
        pc = self.pc
        op = self.ram[pc + 1]
        npc = pc + 2
        if op == 0x21:                        # LD IX/IY,nn
            self._set_ixiy_reg(self.ram[npc] | (self.ram[npc + 1] << 8))
            self.pc = npc + 2
            return
        if op == 0xE1:                        # POP IX/IY
            self._set_ixiy_reg(self.pop())
            self.pc = npc
            return
        if op == 0xE5:                        # PUSH IX/IY
            self.push(self._ixiy_reg())
            self.pc = npc
            return
        if op == 0xE9:                        # JP (IX/IY)
            self.pc = self._ixiy_reg()
            return
        if op == 0xF9:                        # LD SP,IX/IY
            self.sp = self._ixiy_reg()
            self.pc = npc
            return
        if op in (0x09, 0x19, 0x29, 0x39):    # ADD IX/IY,rr
            q = op >> 4
            r = self._add(self._ixiy_reg(), self._rr_r(q), word=True)
            self._set_ixiy_reg(r)
            self.pc = npc
            return
        if op == 0xCB:                        # IX/IY CB dd op
            d = self.ram[npc]
            d = d - 256 if d > 127 else d
            mop = self.ram[npc + 1]     # az opkód a dd UTÁN áll!
            self._exec_ixiy_cb(mop, (self._ixiy_reg() + d) & 0xFFFF)
            self.pc = npc + 2
            return
        d = self.ram[npc]
        d = d - 256 if d > 127 else d
        addr = (self._ixiy_reg() + d) & 0xFFFF
        npc += 1
        if op == 0x36:                        # LD (IY+d),n
            self.poke(addr, self.ram[npc])
            self.pc = npc + 1
            return
        if op == 0x34:                        # INC (IY+d)
            self.poke(addr, self._inc8(self.ram[addr]))
            self.pc = npc
            return
        if op == 0x35:                        # DEC (IY+d)
            self.poke(addr, self._dec8(self.ram[addr]))
            self.pc = npc
            return
        if 0x46 <= op < 0x80 and (op & 7) == 6:      # LD r,(IY+d)
            self._st_r((op >> 3) & 7, self.ram[addr])
            self.pc = npc
            return
        if 0x70 <= op < 0x78:                        # LD (IY+d),r
            self.poke(addr, self._r_r(op & 7))
            self.pc = npc
            return
        if 0x80 <= op <= 0xBE and (op & 7) == 6:     # ALU A,(IY+d)
            v = self.ram[addr]
            kind = op & 0xF8
            if kind in (0x80, 0x88):
                self.a = self._add(self.a, v, carry=1 if kind == 0x88 and
                                   self.f & F_C else 0) & 0xFF
            elif kind in (0x90, 0x98):
                self.a = self._sub(self.a, v, borrow=1 if kind == 0x98 and
                                   self.f & F_C else 0) & 0xFF
            elif kind == 0xA0:
                self.a &= v
                self._logic(self.a)
            elif kind == 0xA8:
                self.a ^= v
                self._logic(self.a)
            elif kind == 0xB0:
                self.a |= v
                self._logic(self.a)
            elif kind == 0xB8:
                self._sub(self.a, v)
            self.pc = npc
            return
        raise SimError(f"nem implementált {'DD' if prefix == 0xDD else 'FD'}"
                       f"-opkód 0x{op:02X} (PC=0x{pc:04X})")

    # --- regiszter-segédek
    def _r_r(self, i):
        # lusta: a (HL) olvasást CSAK i==6 esetén végezzük el (a Galois-
        # LFSR például törvényesen tart 0x8000 feletti ÉRTÉKET a HL-ben,
        # ami nem cím — az eager kiértékelés ál-hibát dobott volna)
        if i == 6:
            return self.ram[self._hl()]
        return (self.b, self.c, self.d, self.e, self.h, self.l, 0, self.a)[i]

    def _st_r(self, i, v):
        if i == 0:
            self.b = v
        elif i == 1:
            self.c = v
        elif i == 2:
            self.d = v
        elif i == 3:
            self.e = v
        elif i == 4:
            self.h = v
        elif i == 5:
            self.l = v
        elif i == 6:
            self.poke(self._hl(), v)
        else:
            self.a = v

    def _rr_r(self, q):
        return (self._bc(), self._de(), self._hl(), self.sp)[q]

    def _st_rr(self, q, v):
        if q == 0:
            self._set_bc(v)
        elif q == 1:
            self._set_de(v)
        elif q == 2:
            self._set_hl(v)
        else:
            self.sp = v

    def _alu(self, kind, v):
        if kind in (0x80, 0x88, 0xC0, 0xC8):
            return self._add(self.a, v, 1 if (self.f & F_C and
                              kind in (0x88, 0xC8)) else 0)
        if kind in (0x90, 0x98, 0xD0, 0xD8):
            return self._sub(self.a, v, 1 if (self.f & F_C and
                              kind in (0x98, 0xD8)) else 0)
        if kind in (0xA0, 0xE0):
            self._logic(self.a & v, half=True)
            return self.a & v
        if kind in (0xA8, 0xE8):
            self._logic(self.a ^ v)
            return self.a ^ v
        if kind in (0xB0, 0xF0):
            self._logic(self.a | v)
            return self.a | v
        if kind in (0xB8, 0xF8):
            return self._sub(self.a, v)  # CP: csak zászlók
        raise SimError(f"ALU {kind:02X}?")

    def _daa(self):
        a, f = self.a, self.f
        corr = 0
        if (a & 0x0F) > 9 or f & F_H:
            corr |= 0x06
        if (a >> 4) > 9 or f & F_C or ((a >> 4) >= 9 and (a & 0x0F) > 9):
            corr |= 0x60
            c = 1
        else:
            c = 0
        if f & F_N:
            r = self._sub(a, corr)
        else:
            r = self._add(a, corr)
        self.f = (self.f & ~F_C) | (F_C if c else 0)
        return r

    def _in(self, port):
        if (port & 0xFF) == 0xFE:
            row = (port >> 8) & 0xFF
            bits = 0xFF
            for r, c in self.held:
                if r == row:
                    bits &= ~(1 << c) & 0xFF
            return bits
        return 0xFF

    def _out(self, port, val):
        pass  # a kazetta-bangolás a szimulátorban nem csinál semmit

    # --- ROM csapdák
    def _rom_trap(self, pc):
        if pc == ROM_SLOW:
            self.slow = True
            self.pc = self.pop()
        elif pc == ROM_SETFAST or pc == ROM_SLOWFAST:
            self.slow = False
            self.pc = self.pop()
        elif pc == ROM_CLS:
            df = self._dfile()
            for r in range(24):
                base = df + 1 + 33 * r
                for i in range(32):
                    self.ram[base + i] = 0x00
                self.ram[base + 32] = 0x76
            self.w(0x400E, (df + 1) & 0xFF)
            self.w(0x400F, (df + 1) >> 8)
            self.pc = self.pop()
        elif pc == ROM_KEYBOARD:
            self.keyboard_scan()
            self.pc = self.pop()
        elif pc == ROM_DISPLAY:
            self._advance_frame()
            self.pc = self.pop()
        elif pc == ROM_INPUT:
            raise SimError("a motor a ROM INPUT parancs-rutinját hívta — "
                           "a tervezés szerint ez nem történhet meg")
        elif pc == ROM_LOAD:
            raise SimError("ROM LOAD hívás ML-ből — a lánc BASIC-en át megy")
        else:
            raise SimError(f"ismeretlen ROM-cím: 0x{pc:04X}")

    def _usr_return(self):
        """A motor visszatért az USR-hívóhoz. A = visszatérési kód."""
        self.handoff_count += 1
        code = self.a
        if code == 1:
            name = self.get_load_name()
            self.do_load(name)
        elif code == 2:
            name = self.get_save_name()
            self.do_save(name)
            # a 4-es BASIC sor (RAND USR) újrahívja a motort:
            self.push(RET_SENTINEL)
            self.pc = ENGINE_ORG
        elif code == 0:
            self.running = False
            self.stop_reason = "program vége (A=0)"
        else:
            raise SimError(f"ismeretlen USR-visszatérési kód: {code}")

    # --- képernyő
    def screen_text(self):
        df = self._dfile()
        rows = []
        for r in range(24):
            base = df + 1 + 33 * r
            s = ""
            for i in range(32):
                c = self.ram[base + i]
                ch = ZX2ASC.get(c & 0x3F, "?")
                if c & 0x80:
                    ch = ch.lower()   # inverz cella -> kisbetű a dumpban
                s += ch
            rows.append(s.rstrip())
        return rows

    def dump_screen(self, title=""):
        rows = self.screen_text()
        out = []
        if title:
            out.append(f"--- {title} ---")
        out.append("+" + "-" * 32 + "+")
        for r in rows:
            out.append("|" + r.ljust(32) + "|")
        out.append("+" + "-" * 32 + "+")
        return "\n".join(out)

    def screen_has(self, substr):
        s = substr.upper()
        return any(s in r.upper() for r in self.screen_text())


# ---------------------------------------------------------------- driver

HELP = """Pico AI szimulátor-driver szkriptparancsok:
  LOAD <blokk>        blokk gyorsbetöltése és motorindítás
  TYPE <szöveg>       gépelés ({S1}..{S9}, {SS}, {RUB}, {SNL} speciális)
  RUN <n>             n utasítás futtatása
  IDLE                futtatás a nyugalmi állapotig
  WAIT <frame>        ennyi képkocka várása (futtatással)
  EXPECT <szöveg>     a képernyő tartalmazza (ellenőrzés)
  SNAP [cím]          képernyő-dump a naplóba
  ECHO <szöveg>       megjegyzés a naplóba
  END                 kilépés (a napló kiíródik)
"""


def run_script(sim, script_path, out_path=None):
    log = sim.log
    log.append("=== PICO AI szimulátoros menet ===")
    for raw in open(script_path, encoding="utf-8"):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 1)
        cmd = parts[0].upper()
        arg = parts[1].strip() if len(parts) > 1 else ""
        if cmd == "LOAD":
            sim.quickload(arg)
        elif cmd == "TYPE":
            sim.type_text(arg)
        elif cmd == "TYPEL":
            sim.type_text(arg + "\n")
        elif cmd == "RUN":
            sim.run(int(arg))
        elif cmd == "IDLE":
            sim.run_until_idle()
        elif cmd == "WAIT":
            target = sim.frames + int(arg)
            while sim.frames < target and sim.running:
                sim.run(4000)
        elif cmd == "EXPECT":
            if not sim.screen_has(arg):
                raise SimError(f"EXPECT sikertelen: {arg!r}\n"
                               + sim.dump_screen("képernyő"))
            log.append(f"OK: {arg!r} a képernyőn")
        elif cmd == "SNAP":
            log.append(sim.dump_screen(arg or "képernyő"))
        elif cmd == "ECHO":
            log.append(f"# {arg}")
        elif cmd == "END":
            break
        else:
            raise SimError(f"ismeretlen parancs: {line!r}")
    log.append("=== menet vége ===")
    text = "\n".join(log)
    print(text)
    if out_path:
        open(out_path, "w", encoding="utf-8").write(text + "\n")
    return sim


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        print(HELP)
        return 1
    if args[0] == "--selftest":
        return _selftest()
    container = args[0]
    script = None
    out = None
    i = 1
    while i < len(args):
        if args[i] == "--script":
            script = args[i + 1]
            i += 2
        elif args[i] == "--out":
            out = args[i + 1]
            i += 2
        else:
            i += 1
    sim = ZX81Sim(container)
    if script:
        run_script(sim, script, out)
    else:
        print("blokkok:", [n for n, _ in sim.blocks])
    return 0


def _selftest():
    """Kis önellenőrzés: Z80-mag + D_FILE-őrszem + EO81."""
    sim = ZX81Sim([("T", b"\x00" * 64)])
    sim.ram[0x5000:0x5008] = b"\x00\x01\x02\x03\x04\x05\x06\x07"
    # néhány utasítás kézzel
    sim.ram[0x6000] = 0x3A
    sim.ram[0x6001], sim.ram[0x6002] = 0x00, 0x50   # LD A,(0x5000)
    sim.pc = 0x6000
    sim.step()
    assert sim.a == 0, f"LD A,(nn): {sim.a}"
    # D_FILE-őrszem: tiltott kód
    sim.w(D_FILE_VAR, 0x00)
    sim.w(D_FILE_VAR + 1, 0x7B)   # D_FILE = 0x7B00
    try:
        sim.poke(0x7B05, 0x77)
        raise AssertionError("őrszem nem dobott!")
    except SimError as e:
        assert "D_FILE" in str(e)
    sim.poke(0x7B05, 0x80)   # inverz space: legális
    sim.poke(0x7B06, 0x3F)   # 'Z': legális
    print("selftest OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
