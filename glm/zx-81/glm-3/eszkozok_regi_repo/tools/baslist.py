#!/usr/bin/env python3
"""baslist.py — egy .T81/.P blokk BASIC-programjának kiratása a VALÓDI
ZX81 token-táblával.

A táblát az EightyOne hivatalos forrásából olvassa
(Source/zx81/zx81BasicLoader.cpp, `tokens[N] = " SZO ";` sorok) — ez az
a tábla, amivel a felhasználó emulátora a BASIC-listát készíti. Ha a
forrás nincs kéznél, a beágyazott másolatot használja (ugyanazok a
számok). A REM után álló gépi kódot NEM tokenizálja (a valódi gép
LIST-je is csak a "REM " szót írja ki), csak a hosszát és a címét adja meg.

Használat: python3 tools/baslist.py <kazetta.T81 | .P> [blokknév]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from zx81sim import load_blocks, ZX2ASC

EO_SRC = "/home/z/my-project/GLM/tmp/eo_src_full/Source/zx81/zx81BasicLoader.cpp"

# Beágyazott másolat (EightyOne, zx81BasicLoader.cpp) — a REM/PRINT/… sorrend:
FALLBACK = {
    0xD3: "PEEK", 0xD4: "USR", 0xD5: "STR$", 0xD6: "CHR$", 0xD7: "NOT",
    0xD8: "**", 0xD9: "OR", 0xDA: "AND", 0xDB: "<=", 0xDC: ">=",
    0xDD: "<>", 0xDE: "THEN", 0xDF: "TO", 0xE0: "STEP",
    0xE1: "LPRINT", 0xE2: "LLIST", 0xE3: "STOP", 0xE4: "SLOW",
    0xE5: "FAST", 0xE6: "NEW", 0xE7: "SCROLL", 0xE8: "CONT", 0xE9: "DIM",
    0xEA: "REM", 0xEB: "FOR", 0xEC: "GOTO", 0xED: "GOSUB", 0xEE: "INPUT",
    0xEF: "LOAD", 0xF0: "LIST", 0xF1: "LET", 0xF2: "PAUSE", 0xF3: "NEXT",
    0xF4: "POKE", 0xF5: "PRINT", 0xF6: "PLOT", 0xF7: "RUN", 0xF8: "SAVE",
    0xF9: "RAND", 0xFA: "IF", 0xFB: "CLS", 0xFC: "UNPLOT", 0xFD: "CLEAR",
    0xFE: "RETURN", 0xFF: "COPY",
}


def load_tokens(path=EO_SRC):
    toks = dict(FALLBACK)
    if not os.path.exists(path):
        return toks, False
    for line in open(path, encoding="latin-1"):
        line = line.strip()
        if not line.startswith("tokens["):
            continue
        try:
            idx = int(line[7:line.index("]")])
            word = line.split("=", 1)[1].strip()
            word = word.strip()[1:].split('"')[0].strip()
        except (ValueError, IndexError):
            continue
        if word:
            toks[idx] = word
    return toks, True


def fp5(b):
    """ZX81 ötbájtos lebegőpont -> int/float (ellenőrzéshez)."""
    e = b[0]
    if e == 0:
        return 0
    m = int.from_bytes(bytes([b[1] & 0x7F, b[2], b[3], b[4]]), "big")
    v = m * 2.0 ** (e - 128 - 32)
    return -v if b[1] & 0x80 else v


def list_line(body, toks, addr):
    """Egy sor törzsének kiratása; addr = a törzs címe a memóriában."""
    out = []
    i = 0
    rem_at = None
    while i < len(body):
        c = body[i]
        if c == 0x76:
            break
        if c >= 0xC0:
            out.append(toks.get(c, "{%02X}" % c))
            if c == toks.get(0xEA) and 0xEA in toks and c == 0xEA:
                rem_at = i + 1
                break
            if " " not in out[-1]:
                out.append(" ")
        elif c == 0x7E:
            v = fp5(body[i + 1:i + 6])
            out.append(str(int(v)) if float(v).is_integer() else str(v))
            i += 5
        else:
            out.append(ZX2ASC.get(c, "{%02X}" % c))
        i += 1
    text = "".join(out)
    if rem_at is not None:
        text += "<GEPI KOD: %d bajt, 0x%04X-0x%04X>" % (
            len(body) - rem_at - (1 if body[-1:] == b"\x76" else 0),
            addr + rem_at, addr + len(body) - 1)
    return text


def list_program(img, toks, base=0x4009):
    i = 0x407D - base            # a program mindig 0x407D-en kezdődik
    lines = []
    while i + 4 <= len(img):
        if img[i] == 0x76:
            break
        num = int.from_bytes(img[i:i + 2], "big")
        ln = int.from_bytes(img[i + 2:i + 4], "little")
        # Sorforma (a bizonyított régi builderrel azonos): [cím BE][hossz LE],
        # ahol hossz = törzs + 1; a törzs után áll a záró 0x76.
        body = img[i + 4:i + 3 + ln]
        lines.append((num, list_line(body, toks, base + i + 4)))
        i += 4 + ln
    return lines


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    toks, from_src = load_tokens()
    only = sys.argv[2] if len(sys.argv) > 2 else None
    print("token-tabla: %s" % ("EightyOne-forras" if from_src else "beagyazott"))
    for name, img in load_blocks(sys.argv[1]):
        if only and name != only:
            continue
        w = lambda a: int.from_bytes(img[a - 0x4009:a - 0x4009 + 2], "little")
        print("\n=== %s  (%d B, 0x4009-0x%04X)" % (name or "(.P)", len(img),
                                                 0x4009 + len(img) - 1))
        print("    D_FILE=0x%04X VARS=0x%04X E_LINE=0x%04X DF_SZ=%d "
              "STKEND=0x%04X 4026=0x%04X" % (w(0x400C), w(0x4010), w(0x4014),
                                            img[0x4022 - 0x4009], w(0x401C),
                                            w(0x4026)))
        for num, text in list_program(img, toks):
            print("  %4d %s" % (num, text))


if __name__ == "__main__":
    main()
