#!/usr/bin/env python3
"""build_t81.py — a Pico AI kazetta (EO81/.T81/.P) összeállítása.

Blokkok:
  PICOBOOT   ~1,6 KB  BASIC-betöltő: ismertető + ENTER-várakozás +
                     ML-telepítő (üres D_FILE a 0x7B00-ra, VARS-jelző,
                     tartós zóna nullázása, RAMTOP := 0x715F) + NEW.
                     A NEW után a felhasználó LOAD ""-t üt.
  PICOBASE   SHORT    motor + szótár + alaptudás; E_LINE = 0x7100
                     (a ROM LOAD eddig olvas — a szintaxis: a kép
                     saját E_LINE-ja határozza meg a hosszt); a D_FILE
                     (0x7B00) és a tartós zóna (0x7160+) NEM része a
                     képnek — a boot telepítette, a RAMTOP védi.
  PICOASTR   SHORT    csillagászat-csomag
  PICOSCIN   SHORT    tudomány-csomag

A 0x4009-től induló kép-recept (appmake-konvenció, a régi projektben
hármasan ellenőrizve): rendszer-változók 116 B; "1 REM <kód>" (org
0x4082); a szám-literálok után 0x7E + 5 bájtos ZX lebegőpontos érték.
A motor binárisában két bűnjelt keres és patchel a builder:
  AD DE B1 5C — NAMESLOT: a 2-es sor LOAD-név-mezőjének címe (téma-váltás)
  AD DE B2 5C — TAILSLOT: a REM-farok címe (72 B tartós-állapot-másolat)
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
Z = 0x4009
PROG = 0x407D
CODE_ORG = 16514
DFILE = 0x7B00
VARSND = DFILE + 793          # 0x7E19: a boot által telepített 0x80 jelző
DICT_HI = 0x5F00
KB = 0x6840
RAMTOP_NEW = 0x715F           # a boot által beállított, leengedett RAMTOP
SHORT_ELINE = 0x7040          # a SHORT képek vége (a ROM LOAD eddig olvas);
                               # a 0x7040-0x715F sáv a BASIC munkaterülete!

# ZX81 tokenek — a EightyOne hivatalos forrásából (Source/zx81/
# zx81BasicLoader.cpp, tokens[...] tábla): PRINT=245/F5, PLOT=246,
# INPUT=238/EE, NEW=230/E6, RAND=249/F9, USR=212/D4, IF=250/FA,
# THEN=222/DE, LOAD=239/EF, SAVE=248/F8, REM=234/EA, RUN=247/F7,
# RETURN=254/FE, COPY=255/FF.
# Megjegyzés: a v0.7.3 itt EGYEL ELCSÚSZTATOTT táblát tett be (0xEB=FOR
# a gépi kód elé, 0xF6=PLOT a PRINT helyére) — az volt a hibás "javítás".
T_PRINT, T_INPUT, T_NEW = 0xF5, 0xEE, 0xE6
T_RAND, T_USR, T_IF = 0xF9, 0xD4, 0xFA
T_THEN, T_LOAD, T_SAVE, T_REM = 0xDE, 0xEF, 0xF8, 0xEA
Q = 0x0B                      # idézőjel


def be16(v):
    return bytes(((v >> 8) & 0xFF, v & 0xFF))


def le16(v):
    return bytes((v & 0xFF, (v >> 8) & 0xFF))


def zx_txt(s):
    out = []
    for ch in s:
        if "A" <= ch <= "Z":
            out.append(0x26 + ord(ch) - 65)
        elif "a" <= ch <= "z":
            out.append(0x26 + ord(ch) - 97)
        elif "0" <= ch <= "9":
            out.append(0x1C + int(ch))
        elif ch == " ":
            out.append(0x00)
        elif ch == ".":
            out.append(0x1B)
        elif ch == ",":
            out.append(0x1A)
        elif ch == "-":
            out.append(0x16)
        elif ch == ":":
            out.append(0x0E)
        else:
            raise ValueError(f"rossz karakter: {ch!r}")
    return bytes(out)


def zx_digits(n):
    return bytes(0x1C + int(ch) for ch in str(n))


def zx_name(s):
    out = []
    for ch in s:
        if "A" <= ch <= "Z":
            out.append(0x26 + ord(ch) - 65)
        elif "0" <= ch <= "9":
            out.append(0x1C + int(ch))
        elif ch == "-":
            out.append(0x16)
        else:
            raise ValueError(f"rossz blokknév-karakter: {ch!r}")
    assert len(out) == 8
    return bytes(out)


def zx_fp(n):
    e = n.bit_length()
    m = round(n / (1 << e) * (1 << 32))
    assert 1 << 31 <= m < 1 << 32, f"zx_fp({n})"
    return bytes([0x80 + e, (m >> 24) & 0x7F, (m >> 16) & 0xFF,
                  (m >> 8) & 0xFF, m & 0xFF])


def num(n):
    """szám-literál programsorban: számjegyek + 0x7E + 5 bájtos FP farok"""
    return zx_digits(n) + b"\x7e" + zx_fp(n)


def dfile_blank():
    return b"\x76" + (b"\x00" * 32 + b"\x76") * 24


def line(num_, body):
    return be16(num_) + le16(len(body) + 1) + body + b"\x76"


def sysvars(dfile, vars_, eline, ramtop=0x7FFD):
    """Rendszerváltozó-fejléc a 0x4009-től induló képhez.
    Eltolás-recept (hivatalos ZX81-térkép, ROM-disassembly-ből):
      s[0]=VERSN(4009)  s[1:3]=E_PPC(400A)  s[3:5]=D_FILE(400C)
      s[5:7]=DF_CC(400E)  s[7:9]=VARS(4010)  s[9:11]=DEST(4012)
      s[11:13]=E_LINE(4014)  s[13:15]=CH_ADD(4016)
      s[15:17]=STKBOT(4018)  s[17:19]=STKEND(401A)
      s[21:23]=ERR_SP(401E)... helyette itt MEM(401C) — lent javítva.
    (A v0.7.2-ig élő verzió a STKBOT/STKEND és MEM mezőket 2 bájttal
    feljebb írta — a képfuttatás a felcsúszott STKEND miatt a ROM
    tükréből (0xC7xx) olvasta a verem-mutatót!)
    """
    s = bytearray(116)
    s[0] = 0                   # VERSN
    s[1:3] = le16(1)           # E_PPC
    s[3:5] = le16(dfile)       # D_FILE
    s[5:7] = le16(dfile + 1)   # DF_CC
    s[7:9] = le16(vars_)       # VARS
    s[9:11] = le16(0)          # DEST
    s[11:13] = le16(eline)     # E_LINE
    s[13:15] = le16(eline + 4) # CH_ADD
    s[15:17] = le16(eline + 5) # STKBOT
    s[17:19] = le16(eline + 5) # STKEND
    s[19:21] = le16(0x405D)    # MEM (0x401C)
    s[25] = 2                  # DF_SZ (0x4022)
    # FIGYELEM: a 0x4025-0x4027 NEM RAMTOP (az a 0x4004-en van, a kép
    # alatt!) — itt a LAST-K (0x4025: B, 0x4026: C) és a MODE (0x4027)
    # él: üres billentyű + K-mód a helyes induló érték!
    s[28:31] = bytes([0xFF, 0xFF, 0x01])   # LAST-K=FFFF, MODE=1 (K)
    s[32:34] = le16(dfile)     # D_FILE-másolat (0x4029)
    return bytes(s)


def wrap_eo81(name, data):
    return (name.encode().ljust(32, b"\0")
            + str(len(data)).encode().ljust(16, b"\0") + data)


def patch_marker(img, marker, value):
    """A bűnjel ELSŐ 2 bájtja maga a DW (LE) — felülírjuk; a jel
    maradék 2 bájtja (Bx 5C) holtadatként a helyén marad."""
    pos = img.index(marker)
    img[pos:pos + 2] = le16(value)
    return pos


def build_boot(inst):
    lines = [line(1, bytes([T_REM]) + inst)]
    intro = [
        (2, "PICO AI V0.1"),
        (3, "A TINY MIND ON A TINY MACHINE."),
        (4, "THIS TAPE SETS UP THE UPPER MEMORY."),
        (5, "PRESS ENTER TO CONTINUE."),
    ]
    for n, txt in intro:
        lines.append(line(n, bytes([T_PRINT, Q]) + zx_txt(txt) + bytes([Q])))
    lines.append(line(6, bytes([T_INPUT, 0x26, 0x0D])))        # INPUT A$
    lines.append(line(7, bytes([T_PRINT, Q])
                      + zx_txt("WHEN THE SCREEN CLEARS, TYPE LOAD")
                      + bytes([Q])))
    lines.append(line(8, bytes([T_PRINT, Q])
                      + zx_txt("FOLLOWED BY TWO QUOTES.")
                      + bytes([Q])))
    lines.append(line(9, bytes([T_RAND, T_USR]) + num(CODE_ORG)))
    lines.append(line(10, bytes([T_NEW])))
    prog = b"".join(lines) + b"\x76"
    end = PROG + len(prog)
    # BIZONYÍTOTT (v0.5.4) elrendezés: [program][D_FILE][VARS-jelző][E_LINE]
    # — a LOC-ADDR (0x0918) a VARS-tól LEFELÉ számolja a 0x76-os
    # sorvégeket, ezért kell a D_FILE-nak a VARS ELŐTT állnia!
    dfile = end                 # D_FILE közvetlenül a program után
    vars_ = dfile + 793         # VARS-jelző (0x80) a D_FILE után
    eline = vars_ + 1           # E_LINE a jelző után
    img = bytearray(sysvars(dfile, vars_, eline))
    img += prog
    img += dfile_blank()        # D_FILE a program után
    img += b"\x80"              # VARS vége-jelző a D_FILE után
    assert Z + len(img) == eline, "E_FILE nem esik a jelző utáni helyre"
    return bytes(img), eline


def build_engine(code, dict_bin, kb, load_name):
    body1 = bytes([T_REM]) + code + b"\x00" * 72     # REM-farok (TAILSLOT)
    l2 = (bytes([T_IF, T_USR]) + num(CODE_ORG) + b"\x14\x1d"
          + b"\x7e" + zx_fp(1)
          + bytes([T_THEN, T_LOAD, Q]) + zx_name(load_name) + bytes([Q]))
    l3 = (bytes([T_IF, T_USR]) + num(CODE_ORG) + b"\x14\x1e"
          + b"\x7e" + zx_fp(2)
          + bytes([T_THEN, T_SAVE, Q]) + zx_name("PICOBASE") + bytes([Q]))
    l4 = bytes([T_RAND, T_USR]) + num(CODE_ORG)
    ln1, ln2 = line(1, body1), line(2, l2)
    prog = ln1 + ln2 + line(3, l3) + line(4, l4) + b"\x76"
    img = bytearray(sysvars(DFILE, VARSND, SHORT_ELINE, RAMTOP_NEW))
    img += prog
    # patchek: a 2-es sor név-mezője (téma-váltás) és a REM-farok címe
    slot2 = PROG + len(ln1) + 4 + 24
    tail = CODE_ORG + len(code)
    patch_marker(img, b"\xad\xde\xb1\x5c", slot2)
    patch_marker(img, b"\xad\xde\xb2\x5c", tail)
    img = bytes(img)
    end = Z + len(img)
    assert end <= DICT_HI, f"a motor túl hosszú: 0x{end:04X}"
    img += b"\x00" * (DICT_HI - end)
    # A szótár ST-szótárai csak a ténylegesen használt bájtig kerülnek a
    # képre (a 1536 B-os puffert levágjuk) — ez hozza LEJJEBB a KB-t és
    # ezzel az E_LINE-t, hogy a BASIC értelmezőnek ~300 B szabad munkaterülete
    # maradjon STKEND és RAMTOP (0x715F) között (a 4-es hibakód ellen!).
    st_used = max(i for i, b in enumerate(dict_bin[0x400:]) if b) + 1
    img += dict_bin[:0x400 + st_used]
    img += b"\x00" * (KB - (Z + len(img)))
    img += kb
    end = Z + len(img)
    assert end <= SHORT_ELINE, f"SHORT túl hosszú: 0x{end:04X}"
    img += b"\x00" * (SHORT_ELINE - end)
    # A kép utolsó bájtja legyen 0x80: az EightyOne a blokk végét az
    # első 0x80-as bájtig méri visszafelé (a ROM-os kép vége a 0x80-as
    # VARS-jelző). A 0x70FF címre kerülő bájt a tartós zónában ül,
    # a gép számára ártalmatlan — a fájlformátum azonban megkívánja!
    img = bytearray(img)
    img[-1] = 0x80
    return bytes(img), slot2, tail


def main():
    bdir = os.path.join(HERE, "..", "engine", "build")
    dist = os.path.join(HERE, "..", "dist")
    os.makedirs(dist, exist_ok=True)
    code = open(os.path.join(bdir, "engine.bin"), "rb").read()
    inst = open(os.path.join(bdir, "bootinst.bin"), "rb").read()
    dict_bin = open(os.path.join(bdir, "dict.bin"), "rb").read()
    boot, boot_e = build_boot(inst)
    blocks = [("PICOBOOT", boot)]
    for name, pk in [("PICOBASE", "base.pk"), ("PICOASTR", "astronomy.pk"),
                     ("PICOSCIN", "science.pk")]:
        kb = open(os.path.join(bdir, pk), "rb").read()
        img, slot2, tail = build_engine(code, dict_bin, kb, name)
        blocks.append((name, img))
        print(f"{name}: {len(img)} B (SHORT), név-mező: 0x{slot2:04X}, "
              f"farok: 0x{tail:04X}")
    print(f"PICOBOOT: {len(boot)} B (E_LINE=0x{boot_e:04X})")
    # A hivatalos EightyOne .T81-formátum (forrás: EightyOne
    # Source/tzx/tzxload.cpp, LoadT81File): a fájl "EO81" mágiával
    # KEZDŐDIK (nélküle a betöltés elutasítva!), majd blokkonként
    # [név 32][hossz ASCII 16][adat]. A mágiát EGYSZER, az első blokk
    # előtt írjuk — pontosan mint a hivatkozott v0.5.4 TOPICS kazetta.
    tape = b"EO81" + b"".join(wrap_eo81(n, d) for n, d in blocks)
    out = os.path.join(dist, "ZX81PICO.T81")
    open(out, "wb").write(tape)
    print(f"ZX81PICO.T81: {len(tape)} B, {len(blocks)} blokk")
    assert tape[:4] == b"EO81", "hiányzik az EO81 mágia!"
    # szerkezeti ellenőrzés
    i = 4
    n = 0
    while i + 48 <= len(tape):
        nm = tape[i:i + 32].rstrip(b"\0").decode()
        ln = int(tape[i + 32:i + 48].rstrip(b"\0"))
        data = tape[i + 48:i + 48 + ln]
        dfile = data[3] | (data[4] << 8)
        eline = data[11] | (data[12] << 8)
        assert data[-1] == 0x80, (
            f"{nm}: az utolsó bájt 0x{data[-1]:02X}, nem 0x80 — "
            "az EightyOne levágná a blokk végét!")
        print(f"  {nm}: D_FILE=0x{dfile:04X} E_LINE=0x{eline:04X} "
              f"({len(data)} B), záró 0x80 OK")
        i += 48 + ln
        n += 1
    assert i == len(tape) and n == len(blocks)
    print("EO81 szerkezet: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
