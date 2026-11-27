#!/usr/bin/env python3
"""Kazetta blokkjainak BASIC-listája token szinten (a valódi ZX81
token-tábla szerint), hogy bizonyítható legyen:
  - a gépi kód csak REM (0xEA) után áll,
  - szöveget csak a motor ír a képernyőre (a betöltő BASIC-ben nincs PLOT),
  - minden blokk E_LINE-ja = 0x4009 + blokkhossz (a ROM LOAD-ja ennél
    a bájtnál fejezi be a betöltést — ld. LD-BYTES 0x01FC).
A számok 5 bájtos ZX81 lebegőpontos alakban állnak a képen; a dekóder
kiírt értékét a "16514"-es sorokon lehet ellenőrizni.
"""
import sys
sys.path.insert(0, "/home/z/my-project/GLM/repo/tools")
from zx81sim import load_blocks

TOK = {0xD3: 'PEEK', 0xD4: 'USR', 0xD5: 'STR$', 0xD6: 'CHR$', 0xD7: 'NOT',
       0xD8: 'BIN', 0xDE: 'THEN', 0xDF: 'TO', 0xE0: 'STEP', 0xE1: 'LPRINT',
       0xE2: 'LLIST', 0xE3: 'STOP', 0xE4: 'SLOW', 0xE5: 'FAST', 0xE6: 'NEW',
       0xE7: 'SCROLL', 0xE8: 'CONT', 0xE9: 'DIM', 0xEA: 'REM', 0xEB: 'FOR',
       0xEC: 'GOTO', 0xED: 'GOSUB', 0xEE: 'INPUT', 0xEF: 'LOAD', 0xF0: 'LIST',
       0xF1: 'LET', 0xF2: 'PAUSE', 0xF3: 'NEXT', 0xF4: 'POKE', 0xF5: 'PRINT',
       0xF6: 'PLOT', 0xF7: 'RUN', 0xF8: 'SAVE', 0xF9: 'RAND', 0xFA: 'IF',
       0xFB: 'CLS', 0xFC: 'UNPLOT', 0xFD: 'CLEAR', 0xFE: 'RETURN',
       0xFF: 'COPY'}


def le16(img, off):
    return img[off] | (img[off + 1] << 8)


def be16(img, off):
    return (img[off] << 8) | img[off + 1]


def fp(b):
    if b[0] == 0:
        return "0"
    m = (((b[1] & 0x7F) | 0x80) << 24) | (b[2] << 16) | (b[3] << 8) | b[4]
    v = m * 2.0 ** (b[0] - 159)
    return str(int(round(v))) if abs(v - round(v)) < 1e-6 else "%.4g" % v


def decode(body, limit=110):
    out, i, q = [], 0, False
    while i < len(body) and len(out) < limit:
        c = body[i]
        if c == 0x76:
            out.append("⏎")
            break
        if q:
            if c == 0x0B:
                q = False
                out.append('"')
            elif 0x26 <= c <= 0x3F:
                out.append(chr(ord('A') + c - 0x26))
            else:
                out.append("«%02X»" % c)
            i += 1
            continue
        if c == 0x0B:
            q = True
            out.append('"')
        elif c == 0x7E and i + 5 < len(body):
            out.append(fp(body[i + 1:i + 6]))
            i += 5
        elif c in TOK:
            out.append(TOK[c] + " ")
        elif 0x26 <= c <= 0x3F:
            out.append(chr(ord('A') + c - 0x26))
        elif 0x1C <= c <= 0x25:
            out.append(chr(ord('0') + c - 0x1C))
        elif 0x0D <= c <= 0x1B:
            out.append("«%02X»" % c)
        elif c == 0x00:
            out.append(" ")
        elif c < 0x10:
            out.append("«%02X»" % c)
        else:
            out.append("«%02X»" % c)
        i += 1
    return "".join(out)


def image_base(data):
    """A 0x4009 kezdete a blokkban (0, ha EO teszi elé a nevet)."""
    if data[0] not in (0x00, 0x01, 0xFF):
        k = 0
        while k < len(data) and not (data[k] & 0x80):
            k += 1
        return k + 1, "".join(chr(c & 0x3F) if 0x26 <= (c & 0x7F) <= 0x3F
                              else "?" for c in data[:k])
    return 0, ""


def analyze(path):
    blocks = load_blocks(path)
    print("fájl:", path, " blokkok:", len(blocks))
    for name, data in blocks:
        base, own = image_base(data)
        n = len(data) - base
        eline = le16(data, base + 0x0B)
        ok = (eline == 0x4009 + n)
        print("--- %s%s  kép=%d B  E_LINE=0x%04X  %s"
              % (name, (" (beépített ZX81-név: %r)" % own) if own else "", n,
                 eline, "E_LINE = 0x4009+hossz ✓" if ok else "!! E_LINE eltér"))
        if not ok:
            continue
        p = base + 0x74          # PROG = 0x407D
        while p + 4 <= len(data):
            if data[p] == 0x80:
                break
            num, ln = be16(data, p), le16(data, p + 2)
            if ln < 2 or p + 2 + ln > len(data):
                print("   hibás sorhossz @%d" % p)
                break
            body = data[p + 4:p + 2 + ln]
            addr = 0x407D + (p - base - 0x74) + 4
            if body[0] == 0xEA:
                print("   %d REM <gépi kód %d bájt, 0x%04X–0x%04X>"
                      % (num, ln - 2, addr + 1, addr + ln - 3))
            else:
                print("   %s" % decode(body).rstrip())
            p += 2 + ln
        last = data[-1]
        print("   utolsó bájt: 0x%02X %s" % (last, "(program-vég jelző ✓)"
                                           if last == 0x80 else "!!"))


if __name__ == "__main__":
    for p in sys.argv[1:]:
        analyze(p)
        print()
