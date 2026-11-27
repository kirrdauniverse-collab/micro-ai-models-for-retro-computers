#!/usr/bin/env python3
"""asm.py — Pico AI saját Z80 assembler + disassembler.

Kétmenetes, címkés assembler a motorhoz használt Z80-részhalmozathoz
(nincs IX/IY, nincs interrupt-kezelés — a motor SLOW módban fut és a
megjelenítő NMI-t békén hagyjuk).

Szintaxis:
    ORG 0x4082            ; kezdőcím
    LABEL:                ; címke
    NAME EQU kifejezés    ; konstans
    DB 1,2,'A',"szoveg"   ; nyers bájtok (string = ASCII bájtok)
    DZ "PICO AI"          ; ZX81 display-kódokra kódolt szöveg (0x00-0x3F)
    DZI "FEJLEC"          ; ugyanaz inverzben (| 0x80 — D_FILE-biztos)
    DW 0x1234             ; 16 bites szavak, little-endian
    DS 64                 ; helyfoglalás (0-val töltve)
    INCLUDE "masik.z80"
    ; megjegyzés a ;-től a sor végéig
Kifejezések: + - * / & | ^ ^, zárójelek, 0x/$/%/dec/'c' literálok, címkék.
Használat:
    python3 asm.py forras.z80 -o engine.bin [--lst file.lst] [--map file.map]
    python3 asm.py --disasm file.bin --org 0x4082 [--len N]
"""
import re
import sys
import os

# ---------------------------------------------------------------- táblák

REGS8 = {"B": 0, "C": 1, "D": 2, "E": 3, "H": 4, "L": 5, "A": 7}
REGS8_MEM = list(REGS8) + ["(HL)"]
REGS16 = {"BC": 0, "DE": 1, "HL": 2, "SP": 3}
PUSHPOP = {"BC": 0, "DE": 1, "HL": 2, "AF": 3}
CONDS = {"NZ": 0, "Z": 1, "NC": 2, "C": 3, "PO": 4, "PE": 5, "P": 6, "M": 7}
JR_CONDS = {"NZ": 0x20, "Z": 0x28, "NC": 0x30, "C": 0x38}
ALU = {"ADD": 0x80, "ADC": 0x88, "SUB": 0x90, "SBC": 0x98,
       "AND": 0xA0, "XOR": 0xA8, "OR": 0xB0, "CP": 0xB8}
ROT = {"RLC": 0x00, "RRC": 0x08, "RL": 0x10, "RR": 0x18,
       "SLA": 0x20, "SRA": 0x28, "SRL": 0x38}

# ZX81 display-karakterkódok (ASCII -> ZX kód; ismeretlen -> szóköz)
ZXCODE = {}
for _i in range(26):
    ZXCODE[chr(65 + _i)] = 0x26 + _i
    ZXCODE[chr(97 + _i)] = 0x26 + _i
for _i in range(10):
    ZXCODE[str(_i)] = 0x1C + _i
ZXCODE.update({" ": 0x00, ".": 0x1B, ",": 0x1A, "?": 0x0F, ":": 0x0E,
               '"': 0x0B, "-": 0x16, "=": 0x14, "+": 0x15, "*": 0x17,
               "/": 0x18, "(": 0x10, ")": 0x11, "<": 0x13, ">": 0x12,
               ";": 0x19, "$": 0x0D})


class AsmError(Exception):
    pass


# ------------------------------------------------------------- kifejezések

TOKEN_RE = re.compile(r"""
    \s*(?:
      (?P<num>0[xX][0-9A-Fa-f]+|\$[0-9A-Fa-f]+|%[01]+|\d+)
    | (?P<chr>'(?:[^'\\]|\\.)')
    | (?P<id>[A-Za-z_.][A-Za-z0-9_.]*)
    | (?P<op>\*\*|[-+*/&|^()~])
    )""", re.X)


class Expr:
    """Mini kifejezés-elemző (rekurzív leszállás)."""

    def __init__(self, text, labels, here):
        self.text = text
        self.labels = labels
        self.here = here
        self.pos = 0
        self.toks = []
        i = 0
        while i < len(text):
            if text[i].isspace():
                i += 1
                continue
            m = TOKEN_RE.match(text, i)
            if not m:
                raise AsmError(f"kifejezés-hiba: {text!r}")
            if m.group("num") is not None:
                v = m.group("num")
                if v[:2].lower() == "0x" or v[0] == "$":
                    self.toks.append(("n", int(v.lstrip("$"), 16)))
                elif v[0] == "%":
                    self.toks.append(("n", int(v[1:], 2)))
                else:
                    self.toks.append(("n", int(v, 10)))
            elif m.group("chr") is not None:
                c = m.group("chr")[1:-1]
                c = c.replace("\\n", "\n").replace("\\0", "\0").replace("\\\\", "\\")
                self.toks.append(("n", ord(c)))
            elif m.group("id") is not None:
                self.toks.append(("id", m.group("id")))
            elif m.group("op") is not None:
                self.toks.append(("op", m.group("op")))
            else:
                raise AsmError(f"kifejezés-hiba: {text!r}")
            i = m.end()
        if not self.toks:
            raise AsmError(f"üres kifejezés: {text!r}")

    def _peek(self):
        return self.toks[self.pos] if self.pos < len(self.toks) else (None, None)

    def _next(self):
        t = self._peek()
        self.pos += 1
        return t

    def eval(self):
        v = self._or_()
        if self.pos != len(self.toks):
            raise AsmError(f"fölösleges a kifejezés végén: {self.text!r}")
        return v

    def _or_(self):
        v = self._xor_()
        while self._peek() == ("op", "|"):
            self._next()
            v = v | self._xor_()
        return v

    def _xor_(self):
        v = self._and_()
        while self._peek() == ("op", "^"):
            self._next()
            v = v ^ self._and_()
        return v

    def _and_(self):
        v = self._add()
        while self._peek() == ("op", "&"):
            self._next()
            v = v & self._add()
        return v

    def _add(self):
        v = self._mul()
        while True:
            t, o = self._peek()
            if t == "op" and o in "+-":
                self._next()
                r = self._mul()
                v = v + r if o == "+" else v - r
            else:
                return v

    def _mul(self):
        v = self._unary()
        while True:
            t, o = self._peek()
            if t == "op" and o in "*/":
                self._next()
                r = self._unary()
                if o == "*":
                    v = v * r
                else:
                    if r == 0:
                        raise AsmError(f"osztás nullával: {self.text!r}")
                    v = int(v / r)  # előjeles egész osztás
            else:
                return v

    def _unary(self):
        t, o = self._next()
        if t == "op" and o == "-":
            return -self._unary()
        if t == "op" and o == "~":
            return ~self._unary()
        if t == "op" and o == "(":
            v = self._or_()
            if self._next() != ("op", ")"):
                raise AsmError(f"hiányzó zárójel: {self.text!r}")
            return v
        if t == "n":
            return o
        if t == "id":
            key = o
            if key == "$":
                return self.here
            if key not in self.labels:
                raise AsmError(f"ismeretlen címke: {key} ({self.text!r})")
            v = self.labels[key]
            if isinstance(v, tuple):  # előre hivatkozott címke: második menet
                raise AsmError(f"címke még nincs definiálva: {key}")
            return v
        raise AsmError(f"váratlan token: {t} {o} ({self.text!r})")


# ------------------------------------------------------------- assembler

class Assembler:
    def __init__(self):
        self.labels = {}
        self.lines = []        # (fname, lineno, addr, src)
        self.org = None
        self.pc = 0
        self.errors = []

    # --- forrás betöltése (INCLUDE-kal)
    def load(self, path):
        out = []
        with open(path, encoding="utf-8") as f:
            for i, raw in enumerate(f, 1):
                s = raw.split(";")[0].strip()
                if not s:
                    continue
                if s.upper().startswith("INCLUDE "):
                    inc = s.split(None, 1)[1].strip().strip('"\'')
                    inc = os.path.join(os.path.dirname(path), inc)
                    out.extend(self.load(inc))
                    continue
                out.append((os.path.basename(path), i, s))
        return out

    # --- 1. menet: címkék
    def pass1(self, srcs):
        pc = 0
        org = None
        equ_re = re.compile(r"^([A-Za-z_.][A-Za-z0-9_.]*)\s+(EQU|=)\s+(.+)$")
        for fn, ln, s in srcs:
            self.lines.append((fn, ln, pc, s))
            if equ_re.match(s):
                continue  # a _name_equ már kezelte
            # címke a sor elején
            m = re.match(r"^([A-Za-z_.][A-Za-z0-9_.]*):\s*(.*)$", s)
            if m:
                if m.group(1) in self.labels:
                    raise AsmError(f"{fn}:{ln}: duplikált címke {m.group(1)}")
                self.labels[m.group(1)] = pc
                s = m.group(2).strip()
                if not s:
                    continue
            parts = s.split(None, 1)
            op = parts[0].upper()
            arg = parts[1].strip() if len(parts) > 1 else ""
            if op == "ORG":
                v = Expr(arg, self.labels, pc).eval()
                if org is None:
                    org = v
                pc = v
                self.org = org
            elif op == "EQU" or op == "=":
                raise AsmError(f"{fn}:{ln}: EQU csak 'NÉV EQU érték' alakban")
            elif op in ("DB", "DEFB", "DZ", "DZI", "DW", "DEFW", "DS", "ALIGN"):
                pc += self._dir_size(op, arg, pc, fn, ln)
            else:
                sz, _ = self._encode(op, arg, pc, fn, ln, final=False)
                pc += sz
        self.pc = pc
        self.org = org if org is not None else 0

    def _name_equ(self, srcs):
        """'NÉV EQU érték' és 'NÉV = érték' sorok kezelása (címke nélkül)."""
        for fn, ln, s in srcs:
            m = re.match(r"^([A-Za-z_.][A-Za-z0-9_.]*)\s+(EQU|=)\s+(.+)$", s)
            if m:
                if m.group(1) in self.labels:
                    raise AsmError(f"{fn}:{ln}: duplikált név {m.group(1)}")
                self.labels[m.group(1)] = Expr(m.group(3), self.labels, 0).eval()

    # --- direktívák mérete
    def _dir_size(self, op, arg, pc, fn, ln):
        if op == "DS":
            n = Expr(arg.split(",")[0], self.labels, pc).eval()
            return n
        if op == "ALIGN":
            n = Expr(arg, self.labels, pc).eval()
            return (n - (pc % n)) % n
        if op in ("DB", "DEFB"):
            return sum(self._db_item_len(it) for it in self._split_args(arg))
        if op in ("DW", "DEFW"):
            return 2 * len(self._split_args(arg))
        if op in ("DZ", "DZI"):
            txt = self._unquote(arg)
            return len(txt)
        return 0

    def _db_item_len(self, it):
        it = it.strip()
        if it.startswith(("'", '"')):
            return len(self._unquote(it))
        return 1

    @staticmethod
    def _split_args(arg):
        out, depth, cur = [], 0, ""
        inq = None
        for ch in arg:
            if inq:
                cur += ch
                if ch == inq:
                    inq = None
                continue
            if ch in "'\"":
                inq = ch
                cur += ch
            elif ch == "(":
                depth += 1
                cur += ch
            elif ch == ")":
                depth -= 1
                cur += ch
            elif ch == "," and depth == 0:
                out.append(cur.strip())
                cur = ""
            else:
                cur += ch
        if cur.strip():
            out.append(cur.strip())
        return out

    @staticmethod
    def _unquote(s):
        s = s.strip()
        if len(s) >= 2 and s[0] == s[-1] and s[0] in "'\"":
            body = s[1:-1]
            return (body.replace("\\n", "\n").replace("\\0", "\0")
                        .replace("\\\\", "\\").replace("\\'", "'"))
        raise AsmError(f"nem idézőjeles szöveg: {s!r}")

    # --- 2. menet: kód generálás
    def pass2(self):
        buf = bytearray()
        pc = self.org
        listing = []
        for fn, ln, _addr0, s in self.lines:
            m = re.match(r"^([A-Za-z_.][A-Za-z0-9_.]*):\s*(.*)$", s)
            if m:
                s = m.group(2).strip()
                if not s:
                    listing.append((fn, ln, pc, b"", f"{m.group(1)}:"))
                    continue
            parts = s.split(None, 1)
            op = parts[0].upper()
            arg = parts[1].strip() if len(parts) > 1 else ""
            if op == "ORG":
                newpc = Expr(arg, self.labels, pc).eval()
                if newpc < pc and len(buf):
                    raise AsmError(f"{fn}:{ln}: ORG visszafelé (0x{pc:04X}→0x{newpc:04X})")
                buf += b"\x00" * (newpc - pc)
                pc = newpc
                listing.append((fn, ln, pc, b"", s))
                continue
            m2 = re.match(r"^([A-Za-z_.][A-Za-z0-9_.]*)\s+(EQU|=)\s+(.+)$", s)
            if m2:
                listing.append((fn, ln, pc, b"", s))
                continue
            if op in ("DB", "DEFB"):
                data = bytearray()
                for it in self._split_args(arg):
                    if it.startswith(("'", '"')):
                        data += self._unquote(it).encode("latin-1")
                    else:
                        data.append(Expr(it, self.labels, pc) .eval() & 0xFF)
                buf += data
                listing.append((fn, ln, pc, bytes(data), s))
                pc += len(data)
                continue
            if op in ("DW", "DEFW"):
                data = bytearray()
                for it in self._split_args(arg):
                    v = Expr(it, self.labels, pc).eval() & 0xFFFF
                    data += bytes((v & 0xFF, v >> 8))
                buf += data
                listing.append((fn, ln, pc, bytes(data), s))
                pc += len(data)
                continue
            if op in ("DZ", "DZI"):
                txt = self._unquote(arg)
                data = bytearray()
                for ch in txt:
                    c = ZXCODE.get(ch, 0x00)
                    if op == "DZI":
                        c |= 0x80
                    data.append(c & 0xFF)
                buf += data
                listing.append((fn, ln, pc, bytes(data), s))
                pc += len(data)
                continue
            if op == "DS":
                n = Expr(arg.split(",")[0], self.labels, pc).eval()
                fill = 0
                if "," in arg:
                    fill = Expr(arg.split(",")[1], self.labels, pc).eval() & 0xFF
                buf += bytes([fill]) * n
                listing.append((fn, ln, pc, b"\x00" * 0, f"DS {n}"))
                pc += n
                continue
            if op == "ALIGN":
                n = Expr(arg, self.labels, pc).eval()
                pad = (n - (pc % n)) % n
                buf += b"\x00" * pad
                pc += pad
                listing.append((fn, ln, pc, b"", s))
                continue
            sz, enc = self._encode(op, arg, pc, fn, ln, final=True)
            buf += enc
            listing.append((fn, ln, pc, bytes(enc), s))
            pc += sz
        return bytes(buf), listing

    # --- utasítás-kódoló
    def _encode(self, op, arg, pc, fn, ln, final):
        """Visszaad: (méret, bájtok). final=False → csak a méret kell;
        az ismeretlen (előre hivatkozott) címkék 0-t adnak, mert ebben a
        részhalmozatban minden utasítás mérete csak az operandus ALAKJÁTÓL
        függ (nincs rövid/hosszú ugrás-változat)."""
        def E(t):
            try:
                return Expr(t, self.labels, pc).eval()
            except AsmError:
                if final:
                    raise
                return 0  # pass 1: a mérethez csak az alak számít

        def evalb(t):
            v = E(t)
            if final and (v < -128 or v > 255):
                raise AsmError(f"8 bites túlfutás: {t}")
            return v & 0xFF

        def rel(t, base):
            v = E(t)
            d = v - (base + 2)
            if final and not (-128 <= d <= 127):
                raise AsmError(f"JR-túlfutás: {t} (d={d})")
            return d & 0xFF
        try:
            return self._enc(op, arg, pc, final, E, evalb, rel)
        except AsmError:
            raise
        except Exception as e:
            raise AsmError(f"{fn}:{ln}: {op} {arg!r} — {e}")

    def _enc(self, op, arg, pc, final, E, evalb, rel):
        a = arg.strip()

        # --- egyszerű, argumentum nélküli
        simple = {"NOP": b"\x00", "HALT": b"\x76", "DAA": b"\x27",
                  "CPL": b"\x2F", "CCF": b"\x3F", "SCF": b"\x37",
                  "DI": b"\xF3", "EI": b"\xFB",
                  "RLCA": b"\x07", "RRCA": b"\x0F", "RLA": b"\x17",
                  "RRA": b"\x1F", "RETI": b"\xED\x4D", "NEG": b"\xED\x44",
                  "LDIR": b"\xED\xB0", "LDDR": b"\xED\xB8", "CPIR": b"\xED\xB1"}
        if op in simple and not a:
            return len(simple[op]), simple[op]
        if op == "RET" and not a:
            return 1, b"\xC9"

        # --- 16 bites HL-aritmetika (az ALU egyszerű ága ELŐTT)
        if op in ("ADD", "ADC", "SBC") and "," in a:
            d, s = [x.strip() for x in a.split(",", 1)]
            if d.upper() == "HL" and s.upper() in REGS16:
                if op == "ADD":
                    return 1, bytes((0x09 | (REGS16[s.upper()] << 4),))
                if op == "ADC":
                    return 2, bytes((0xED, 0x4A | (REGS16[s.upper()] << 4)))
                return 2, bytes((0xED, 0x42 | (REGS16[s.upper()] << 4)))

        # --- LD
        if op == "LD":
            return self._enc_ld(a, pc, final, evalb, rel, E)

        # --- PUSH/POP
        if op in ("PUSH", "POP") and a.upper() in PUSHPOP:
            q = PUSHPOP[a.upper()] << 4
            return 1, bytes((0xC1 | q if op == "POP" else 0xC5 | q,))

        # --- ALU
        if op in ALU:
            base = ALU[op]
            val = a.strip()
            if val.upper().replace(" ", "").startswith("A,"):
                val = val.split(",", 1)[1].strip()
            au = val.upper().replace(" ", "")
            if au == "(HL)":
                return 1, bytes((base | 6,))
            if au in REGS8:
                return 1, bytes((base | REGS8[au],))
            if au.startswith("(") or au in REGS16:
                raise AsmError(f"rossz ALU operandus: {a!r}")
            return 2, bytes((base | 0x46, evalb(val)))

        # --- 16 bites HL-aritmetika
        if op in ("ADD", "ADC", "SBC") and "," in a:
            d, s = [x.strip() for x in a.split(",", 1)]
            if d.upper() == "HL" and op == "ADD":
                if s.upper() in REGS16:
                    return 1, bytes((0x09 | (REGS16[s.upper()] << 4),))
            if d.upper() == "HL" and s.upper() in REGS16:
                if op == "ADC":
                    return 2, bytes((0xED, 0x4A | (REGS16[s.upper()] << 4)))
                if op == "SBC":
                    return 2, bytes((0xED, 0x42 | (REGS16[s.upper()] << 4)))
            if d.upper() == "A" and s.upper() in REGS16:
                raise AsmError("A,rr ALU nem létezik; használd A,(HL) úton")
        if op == "ADD" and a.upper() in REGS16:
            return 1, bytes((0x09 | (REGS16[a.upper()] << 4),))

        # --- INC/DEC
        if op in ("INC", "DEC"):
            au = a.upper().strip()
            if au in REGS16:
                b = (REGS16[au] << 4) | (0x03 if op == "INC" else 0x0B)
                return 1, bytes((b,))
            if au == "(HL)":
                return 1, bytes((0x34 if op == "INC" else 0x35,))
            if au in REGS8:
                b = (REGS8[au] << 3) | (4 if op == "INC" else 5)
                return 1, bytes((b,))
            raise AsmError(f"INC/DEC operandus: {a!r}")

        # --- forgatások/eltolások
        if op in ROT:
            au = a.upper().strip()
            if au == "(HL)":
                return 2, bytes((0xCB, ROT[op] | 6))
            if au in REGS8:
                return 2, bytes((0xCB, ROT[op] | REGS8[au]))
            raise AsmError(f"{op} operandus: {a!r}")
        if op in ("BIT", "RES", "SET"):
            m = re.match(r"^(\d)\s*,\s*(.+)$", a)
            if not m:
                raise AsmError(f"{op} alak: {op} b,r")
            b = int(m.group(1))
            tgt = m.group(2).strip().upper()
            base = {"BIT": 0x40, "RES": 0x80, "SET": 0xC0}[op]
            if tgt == "(HL)":
                return 2, bytes((0xCB, base | (8 * b) | 6))
            if tgt in REGS8:
                return 2, bytes((0xCB, base | (8 * b) | REGS8[tgt]))
            raise AsmError(f"{op} cél: {a!r}")

        # --- ugrások
        if op == "JP":
            if a.upper() == "(HL)":
                return 1, b"\xE9"
            if "," in a:
                cc, tgt = [x.strip() for x in a.split(",", 1)]
                cc = cc.upper()
                if cc not in CONDS:
                    raise AsmError(f"rossz feltétel: {cc}")
                v = E(tgt) & 0xFFFF
                return 3, bytes((0xC2 | (CONDS[cc] << 3), v & 0xFF, v >> 8))
            v = E(a) & 0xFFFF
            return 3, bytes((0xC3, v & 0xFF, v >> 8))
        if op == "JR":
            if "," in a:
                cc, tgt = [x.strip() for x in a.split(",", 1)]
                cc = cc.upper()
                if cc not in JR_CONDS:
                    raise AsmError(f"JR csak NZ/Z/NC/C: {cc}")
                d = rel(tgt, pc)
                return 2, bytes((JR_CONDS[cc], d))
            d = rel(a, pc)
            return 2, bytes((0x18, d))
        if op == "DJNZ":
            d = rel(a, pc)
            return 2, bytes((0x10, d))

        # --- hívások
        if op == "CALL":
            if "," in a:
                cc, tgt = [x.strip() for x in a.split(",", 1)]
                cc = cc.upper()
                if cc not in CONDS:
                    raise AsmError(f"rossz feltétel: {cc}")
                v = E(tgt) & 0xFFFF
                return 3, bytes((0xC4 | (CONDS[cc] << 3), v & 0xFF, v >> 8))
            v = E(a) & 0xFFFF
            return 3, bytes((0xCD, v & 0xFF, v >> 8))
        if op == "RET" and a:
            cc = a.upper()
            if cc not in CONDS:
                raise AsmError(f"rossz feltétel: {cc}")
            return 1, bytes((0xC0 | (CONDS[cc] << 3),))
        if op == "RST":
            v = E(a)
            if v % 8 or not (0 <= v <= 0x38):
                raise AsmError(f"RST cím 8-cal osztható 0..38h: {v}")
            return 1, bytes((0xC7 | v,))

        # --- EX
        if op == "EX":
            au = a.upper().replace(" ", "")
            if au == "DE,HL":
                return 1, b"\xEB"
            if au == "AF,AF'" or au == "AF,AF":
                return 1, b"\x08"
            if au == "(SP),HL":
                return 1, b"\xE3"
            raise AsmError(f"EX operandus: {a!r}")

        # --- port
        if op == "IN":
            au = a.upper().replace(" ", "")
            if au == "A,(C)":
                return 2, b"\xED\x78"
            m = re.match(r"^A,\((.+)\)$", au)
            if m:
                return 2, bytes((0xDB, evalb(m.group(1))))
            raise AsmError(f"IN operandus: {a!r}")
        if op == "OUT":
            au = a.upper().replace(" ", "")
            if au == "(C),A":
                return 2, b"\xED\x79"
            m = re.match(r"^\((.+)\),A$", au)
            if m:
                return 2, bytes((0xD3, evalb(m.group(1))))
            raise AsmError(f"OUT operandus: {a!r}")

        raise AsmError(f"nem támogatott utasítás: {op} {a}")

    def _enc_ld(self, a, pc, final, evalb, rel, E):
        # első felső szintű vesszőnél vágunk (idézőjel- és zárójelbiztos)
        depth, inq, cut = 0, None, -1
        for i, ch in enumerate(a):
            if inq:
                if ch == inq:
                    inq = None
                continue
            if ch in "'\"":
                inq = ch
            elif ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
            elif ch == "," and depth == 0:
                cut = i
                break
        if cut < 0:
            raise AsmError(f"LD alak (nincs vessző): {a!r}")
        dst, src = a[:cut].strip(), a[cut + 1:].strip()
        du, su = dst.upper(), src.upper()

        def paren_inner(t):
            t = t.strip()
            if len(t) >= 2 and t[0] == "(" and t[-1] == ")":
                inner = t[1:-1].strip()
                if inner.upper() not in ("HL", "BC", "DE", "C"):
                    return inner
            return None

        # --- regiszter-specialitások
        if du == "(HL)":
            if su in REGS8:
                return 1, bytes((0x70 | REGS8[su],))
            return 2, bytes((0x36, evalb(src)))
        if su == "(HL)":
            if du in REGS8:
                return 1, bytes((0x40 | (REGS8[du] << 3) | 6,))
            raise AsmError(f"LD cél (HL)-ből: {a!r}")
        if du in REGS8 and su in REGS8:
            return 1, bytes((0x40 | (REGS8[du] << 3) | REGS8[su],))
        if du == "A" and su == "(BC)":
            return 1, b"\x0A"
        if du == "A" and su == "(DE)":
            return 1, b"\x1A"
        if du == "(BC)" and su == "A":
            return 1, b"\x02"
        if du == "(DE)" and su == "A":
            return 1, b"\x12"
        if du == "SP" and su == "HL":
            return 1, b"\xF9"

        # --- (kifejezés) címzések
        inner_s = paren_inner(src)
        if du == "A" and inner_s is not None:
            v = E(inner_s) & 0xFFFF
            return 3, bytes((0x3A, v & 0xFF, v >> 8))
        if du == "HL" and inner_s is not None:
            v = E(inner_s) & 0xFFFF
            return 3, bytes((0x2A, v & 0xFF, v >> 8))
        if du == "DE" and inner_s is not None:
            v = E(inner_s) & 0xFFFF
            return 4, bytes((0xED, 0x5B, v & 0xFF, v >> 8))
        if du == "BC" and inner_s is not None:
            v = E(inner_s) & 0xFFFF
            return 4, bytes((0xED, 0x4B, v & 0xFF, v >> 8))
        inner_d = paren_inner(dst)
        if su == "A" and inner_d is not None:
            v = E(inner_d) & 0xFFFF
            return 3, bytes((0x32, v & 0xFF, v >> 8))
        if su == "HL" and inner_d is not None:
            v = E(inner_d) & 0xFFFF
            return 3, bytes((0x22, v & 0xFF, v >> 8))
        if su == "DE" and inner_d is not None:
            v = E(inner_d) & 0xFFFF
            return 4, bytes((0xED, 0x53, v & 0xFF, v >> 8))
        if su == "BC" and inner_d is not None:
            v = E(inner_d) & 0xFFFF
            return 4, bytes((0xED, 0x43, v & 0xFF, v >> 8))

        # --- közvetlen értékek
        if du in REGS8:
            if su in REGS8 or su in ("(BC)", "(DE)"):
                raise AsmError(f"LD formális hiba: {a!r}")
            return 2, bytes((0x06 | (REGS8[du] << 3), evalb(src)))
        if du in REGS16:
            if su.startswith("(") or su in REGS8 or su in REGS16:
                raise AsmError(f"LD formális hiba: {a!r}")
            v = E(src) & 0xFFFF
            return 3, bytes((0x01 | (REGS16[du] << 4), v & 0xFF, v >> 8))
        raise AsmError(f"LD alak ismeretlen: {a!r}")


def assemble(path, out_bin, lst_path=None, map_path=None):
    asm = Assembler()
    srcs = asm.load(path)
    asm._name_equ(srcs)
    asm.pass1(srcs)
    # a pass1 után a címkék kész; EQU-k a _name_equ-ből
    data, listing = asm.pass2()
    org = asm.org
    with open(out_bin, "wb") as f:
        f.write(data)
    if lst_path:
        with open(lst_path, "w", encoding="utf-8") as f:
            for fn, ln, addr, enc, s in listing:
                hexs = " ".join(f"{b:02X}" for b in enc[:8])
                more = "" if len(enc) <= 8 else ".."
                f.write(f"{addr:04X}  {hexs:<24}{more}  {s}\n")
    if map_path:
        with open(map_path, "w", encoding="utf-8") as f:
            for k in sorted(asm.labels, key=lambda x: asm.labels[x]
                            if isinstance(asm.labels[x], int) else 1 << 30):
                v = asm.labels[k]
                if isinstance(v, int):
                    f.write(f"{k:<24} = 0x{v:04X}\n")
    return asm, data, org, listing


# ---------------------------------------------------------- disassembler

REG8_REV = {0: "B", 1: "C", 2: "D", 3: "E", 4: "H", 5: "L", 6: "(HL)", 7: "A"}
ALU_REV = {0x80: "ADD", 0x88: "ADC", 0x90: "SUB", 0x98: "SBC",
           0xA0: "AND", 0xA8: "XOR", 0xB0: "OR", 0xB8: "CP",
           0xC0: "ADD", 0xC8: "ADC", 0xD0: "SUB", 0xD8: "SBC",
           0xE0: "AND", 0xE8: "XOR", 0xF0: "OR", 0xF8: "CP"}
CC_REV = {0: "NZ", 1: "Z", 2: "NC", 3: "C", 4: "PO", 5: "PE", 6: "P", 7: "M"}
ZXREV = {}
for k, v in ZXCODE.items():
    if v not in ZXREV and k.isalpha() and k.islower():
        ZXREV[v] = k.upper()
for i in range(10):
    ZXREV[0x1C + i] = str(i)
ZXREV.update({0x00: " ", 0x1B: ".", 0x1A: ",", 0x0F: "?", 0x0E: ":", 0x16: "-",
              0x14: "=", 0x15: "+", 0x17: "*", 0x18: "/", 0x10: "(", 0x11: ")",
              0x13: "<", 0x12: ">", 0x19: ";"})


def zx_to_ascii(code):
    c = code & 0x3F
    return ZXREV.get(c, "?")


def disasm(data, org, max_len=None):
    out = []
    i = 0
    if max_len:
        data = data[:max_len]
    while i < len(data):
        addr = org + i
        b0 = data[i]
        txt = None
        size = 1
        if b0 == 0xCB:
            if i + 1 >= len(data):
                out.append((addr, data[i:], "CB ?"))
                break
            b1 = data[i + 1]
            size = 2
            if b1 < 0x40:
                names = ["RLC", "RRC", "RL", "RR", "SLA", "SRA", "?SL", "SRL"]
                txt = f"{names[b1 >> 3]} {REG8_REV[b1 & 7]}"
            else:
                names = ["BIT", "RES", "SET"]
                kind, bit = (b1 >> 6) & 3, (b1 >> 3) & 7
                txt = f"{names[kind - 1]} {bit},{REG8_REV[b1 & 7]}"
        elif b0 == 0xED:
            if i + 1 >= len(data):
                out.append((addr, data[i:], "ED ?"))
                break
            b1 = data[i + 1]
            size = 2
            tbl = {0x78: "IN A,(C)", 0x79: "OUT (C),A", 0xB0: "LDIR",
                   0xB8: "LDDR", 0xB1: "CPIR", 0x4D: "RETI",
                   0x42: "SBC HL,BC", 0x52: "SBC HL,DE", 0x62: "SBC HL,HL",
                   0x72: "SBC HL,SP", 0x4A: "ADC HL,BC", 0x5A: "ADC HL,DE",
                   0x6A: "ADC HL,HL", 0x7A: "ADC HL,SP"}
            txt = tbl.get(b1, f"ED {b1:02X} ?")
        elif b0 == 0x76:
            txt = "HALT"
        elif b0 in (0x00, 0x07, 0x0F, 0x17, 0x1F, 0x27, 0x2F, 0x3F, 0x37,
                    0xF3, 0xFB):
            tbl = {0x00: "NOP", 0x07: "RLCA", 0x0F: "RRCA", 0x17: "RLA",
                   0x1F: "RRA", 0x27: "DAA", 0x2F: "CPL", 0x3F: "CCF",
                   0x37: "SCF", 0xF3: "DI", 0xFB: "EI"}
            txt = tbl[b0]
        elif 0x40 <= b0 < 0x80 and b0 != 0x76:
            txt = f"LD {REG8_REV[(b0 >> 3) & 7]},{REG8_REV[b0 & 7]}"
        elif (b0 & 0xC7) == 0x06:
            if i + 1 >= len(data):
                out.append((addr, data[i:], "LD ?"))
                break
            size = 2
            v = data[i + 1]
            txt = f"LD {REG8_REV[(b0 >> 3) & 7]},{v}   ; 0x{v:02X}"
        elif b0 in (0x0A, 0x1A, 0x02, 0x12):
            tbl = {0x0A: "LD A,(BC)", 0x1A: "LD A,(DE)", 0x02: "LD (BC),A",
                   0x12: "LD (DE),A"}
            txt = tbl[b0]
        elif b0 in (0x3A, 0x32, 0x2A, 0x22):
            if i + 2 >= len(data):
                out.append((addr, data[i:], f"{b0:02X} ?"))
                break
            size = 3
            v = data[i + 1] | (data[i + 2] << 8)
            tbl = {0x3A: "LD A,(", 0x32: "LD (", 0x2A: "LD HL,(", 0x22: "LD ("}
            txt = f"{tbl[b0]}{v:04X})" + ("A" if b0 == 0x32 else
                                          ("HL" if b0 == 0x22 else ""))
        elif 0x01 <= (b0 & 0xCF) <= 0x01 and (b0 & 0x0F) in (1, 11):
            q = b0 >> 4
            rr = ["BC", "DE", "HL", "SP"][q]
            if i + 2 >= len(data):
                out.append((addr, data[i:], f"{b0:02X} ?"))
                break
            size = 3
            v = data[i + 1] | (data[i + 2] << 8)
            if b0 & 0x08:
                txt = f"DEC {rr}"
                size = 1
            else:
                txt = f"LD {rr},{v:04X}   ; 0x{v:04X}"
        elif b0 in (0x03, 0x13, 0x23, 0x33, 0x0B, 0x1B, 0x2B, 0x3B):
            q = b0 >> 4
            rr = ["BC", "DE", "HL", "SP"][q]
            txt = ("INC " if (b0 & 8) == 0 else "DEC ") + rr
        elif b0 in (0x09, 0x19, 0x29, 0x39):
            q = b0 >> 4
            txt = f"ADD HL,{['BC', 'DE', 'HL', 'SP'][q]}"
        elif 0x80 <= b0 < 0xC0 and (b0 & 0xC6) != 0xC6:
            # ALU r — kivéve a C6/CE/... közvetlen formákat
            if b0 in (0xC6, 0xCE, 0xD6, 0xDE, 0xE6, 0xEE, 0xF6, 0xFE):
                pass
            else:
                txt = f"{ALU_REV[b0 & 0xF8]} {REG8_REV[b0 & 7]}"
        if txt is None and b0 in (0xC6, 0xCE, 0xD6, 0xDE, 0xE6, 0xEE,
                                  0xF6, 0xFE):
            if i + 1 >= len(data):
                out.append((addr, data[i:], "ALU ?"))
                break
            size = 2
            v = data[i + 1]
            txt = f"{ALU_REV[b0 & 0xF8]} {v}"
        elif txt is None and (b0 & 0xC7) == 0x04:
            txt = ("INC " if (b0 & 8) == 0 else "DEC ") + REG8_REV[(b0 >> 3) & 7]
        elif txt is None and (b0 in (0x18, 0x10) or (b0 & 0xE7) in (0x20, 0x28, 0x30, 0x38)):
            if b0 in (0x18, 0x10, 0x20, 0x28, 0x30, 0x38):
                if i + 1 >= len(data):
                    out.append((addr, data[i:], "JR ?"))
                    break
                size = 2
                d = data[i + 1]
                tgt = addr + 2 + (d - 256 if d > 127 else d)
                tbl = {0x18: "JR", 0x10: "DJNZ", 0x20: "JR NZ", 0x28: "JR Z",
                       0x30: "JR NC", 0x38: "JR C"}
                txt = f"{tbl[b0]} {tgt:04X}"
        elif txt is None and b0 in (0xC3, 0xCD, 0xC2, 0xCA, 0xD2, 0xDA,
                                    0xE2, 0xEA, 0xF2, 0xFA, 0xC4, 0xCC,
                                    0xD4, 0xDC, 0xE4, 0xEC, 0xF4, 0xFC):
            if i + 2 >= len(data):
                out.append((addr, data[i:], "JP ?"))
                break
            size = 3
            v = data[i + 1] | (data[i + 2] << 8)
            if b0 in (0xC3, 0xCD):
                txt = ("JP " if b0 == 0xC3 else "CALL ") + f"{v:04X}"
            else:
                cc = CC_REV[(b0 >> 3) & 7]
                is_call = b0 in (0xC4, 0xCC, 0xD4, 0xDC, 0xE4, 0xEC, 0xF4, 0xFC)
                txt = f"{'CALL' if is_call else 'JP'} {cc},{v:04X}"
        elif txt is None and b0 == 0xE9:
            txt = "JP (HL)"
        elif txt is None and b0 in (0xC0, 0xC8, 0xD0, 0xD8, 0xE0, 0xE8,
                                    0xF0, 0xF8):
            txt = f"RET {CC_REV[(b0 >> 3) & 7]}"
        elif txt is None and b0 == 0xC9:
            txt = "RET"
        elif txt is None and b0 in (0xC1, 0xD1, 0xE1, 0xF1):
            txt = f"POP {['BC', 'DE', 'HL', 'AF'][(b0 >> 4) - 0xC]}"
        elif txt is None and b0 in (0xC5, 0xD5, 0xE5, 0xF5):
            txt = f"PUSH {['BC', 'DE', 'HL', 'AF'][(b0 >> 4) - 0xC]}"
        elif txt is None and b0 == 0xEB:
            txt = "EX DE,HL"
        elif txt is None and b0 == 0xF9:
            txt = "LD SP,HL"
        elif txt is None and b0 in (0xDB, 0xD3):
            if i + 1 >= len(data):
                out.append((addr, data[i:], "PORT ?"))
                break
            size = 2
            v = data[i + 1]
            txt = f"{'IN' if b0 == 0xDB else 'OUT'} A,({v:02X})"
        elif txt is None and (b0 & 0xC7) == 0xC7:
            txt = f"RST {b0 & 0x38:02X}"
        if txt is None:
            z = zx_to_ascii(b0)
            c = f"'{z}'" if z and z != "?" else ""
            txt = f"DB 0x{b0:02X} {c}"
        out.append((addr, data[i:i + size], txt))
        i += size
    return out


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    if sys.argv[1] == "--disasm":
        fn = sys.argv[2]
        org = 0x4082
        ln = None
        args = sys.argv[3:]
        for j in range(0, len(args) - 1, 2):
            if args[j] == "--org":
                org = int(args[j + 1], 0)
            elif args[j] == "--len":
                ln = int(args[j + 1], 0)
        data = open(fn, "rb").read()
        for addr, enc, txt in disasm(data, org, ln):
            hexs = " ".join(f"{b:02X}" for b in enc)
            print(f"{addr:04X}  {hexs:<9} {txt}")
        return 0
    src = sys.argv[1]
    out = "a.bin"
    lst = map_ = None
    args = sys.argv[2:]
    for j in range(0, len(args), 2):
        if args[j] == "-o":
            out = args[j + 1]
        elif args[j] == "--lst":
            lst = args[j + 1]
        elif args[j] == "--map":
            map_ = args[j + 1]
    asm, data, org, _ = assemble(src, out, lst, map_)
    print(f"OK: {len(data)} bájt, org=0x{org:04X}, vég=0x{org + len(data):04X}, "
          f"{len(asm.labels)} címke -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
