#!/usr/bin/env python3
"""t81_validate.py — a .T81 kazetta ellenőrzése PONTOSAN az EightyOne
emulátor LoadT81File() logikája szerint (forrás: EightyOne
Source/tzx/tzxload.cpp + Utils.cpp ConvertASCIIZX81).

Amit az emulátor csinál (és amit itt utánzunk):
1. Az első 4 bájt kötelezően "EO81" — különben a fájl ELUTASÍTVA.
2. Blokkonként: [32 B név, \\0-pad][16 B ASCII hossz, \\0-pad][adat].
   - hossz < 1 vagy > 65535 → a blokklánc vége.
   - "<...>" név: <Silence> = szünetblokk, egyéb = átugorlandó.
3. Ha az adat első bájtja 0x00 / 0x01 / 0xFF (a VERSN!), az emulátor a
   fejlécnévből SZINTETIZÁLJA a ZX81-as fájlnevet (ASCII→ZX81-karakter,
   az utolsó betű |0x80-tal — a ROM-os konvenció) és ELÉFŰZI a kép elé.
4. A [név+kép] adat VÉGÉTŐL visszafelé az első 0x80-as bájtig vág
   (a ROM-os kép utolsó bájtja a 0x80-as VARS-jelző).
5. Az így keletkező szalagblokk hossza legyen PONTOSAN
   [névhossz + (E_LINE − 0x4009)] — különben a ROM-os betöltés
   berozsdásodik vagy levágódik.
"""
import sys

ZX_CHARS = ("  ?????????:;-<>\"=+"
            "0123456789ABCDEFGHIJ"
            "KLMNOPQRSTUVWXYZ??")


def ascii_to_zx81_name(fname):
    """ConvertASCIIZX81 utánzat: a fejlécnév → ZX81-karakterek,
    az utolsó betű |0x80-tal."""
    out = bytearray()
    for ch in fname.upper():
        if ch == '_':
            ch = ' '
        try:
            out.append(ZX_CHARS.index(ch) if ch in ZX_CHARS else 0x00)
        except ValueError:
            out.append(0x00)
    if out:
        out[-1] |= 0x80
    return bytes(out)


def validate(path, verbose=True):
    data = open(path, 'rb').read()
    problems = []
    info = []
    if data[:4] != b"EO81":
        problems.append("NINCS 'EO81' mágia a fájl elején — az EightyOne "
                        "betöltője elutasítja a fájlt! (return false)")
    i = 4
    nblk = 0
    while i + 48 <= len(data):
        fname = data[i:i + 32].split(b"\0")[0].decode("ascii", "replace")
        flen = data[i + 32:i + 48].split(b"\0")[0].decode("ascii", "replace")
        if not flen.isdigit():
            if i < len(data) and nblk > 0:
                info.append("  [maradék %d bájt a blokkok után — figyelmeztetés]"
                            % (len(data) - i))
            break
        length = int(flen)
        if length < 1 or length > 65535:
            problems.append("blokk %d: érvénytelen hossz (%s)" % (nblk + 1, flen))
            break
        blk = data[i + 48:i + 48 + length]
        if len(blk) != length:
            problems.append("blokk %d (%s): a fájl csonka — %d/%d bájtot "
                            "tartalmaz" % (nblk + 1, fname, len(blk), length))
            break
        nblk += 1
        # a név-szintetizálás + a levágás emulálása
        if fname.startswith("<") and fname.endswith(">"):
            info.append("  %2d. <speciális> blokk: %s (%d)" % (nblk, fname, length))
            i += 48 + length
            continue
        synth = b""
        first = blk[0]
        if first in (0x00, 0x01, 0xFF):
            synth = ascii_to_zx81_name(fname) if fname else b""
        payload = synth + blk
        cut = len(payload)
        while cut > 0 and payload[cut - 1] != 0x80:
            cut -= 1
        trimmed = payload[:cut]
        eline = blk[11] | (blk[12] << 8) if len(blk) >= 13 else 0
        expect = len(synth) + (eline - 0x4009) if eline >= 0x4009 else None
        status = "OK"
        if expect is not None and len(trimmed) != expect:
            status = ("LEVÁGÁS! a blokk végétől %d bájt hiányzik/felesleges "
                      "(elvárt %d a névvel, maradt %d)"
                      % (len(payload) - len(trimmed), expect, len(trimmed)))
            problems.append("blokk %d (%s): %s" % (nblk, fname, status))
            status = "HIBA: " + status
        if verbose:
            info.append("  %2d. %-10s %5d B | első bájt=%02X | szintetizált "
                        "név %d B | E_LINE=0x%04X | trimmelt hossz=%d %s"
                        % (nblk, fname, length, first, len(synth), eline,
                           len(trimmed), "✓" if status == "OK" else "✗"))
        i += 48 + length
    if nblk == 0 and not problems:
        problems.append("egyetlen blokkot sem találtunk!")
    print("=== %s" % path.split('/')[-1])
    for line in info:
        print(line)
    if problems:
        print("PROBLÉMÁK:")
        for p in problems:
            print("  ✗", p)
        return False
    print("✓ A fájl szerkezete minden tekintetben MEGFELEL az EightyOne "
          "által elvárt .T81-formátumnak (%d blokk)." % nblk)
    return True


if __name__ == "__main__":
    ok = all(validate(p) for p in sys.argv[1:])
    sys.exit(0 if ok else 1)
