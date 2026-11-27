#!/usr/bin/env python3
"""Kazetta-blokkok elemzése abból a szempontból, mit csinál velük a
EightyOne (Source/tzx/tzxload.cpp, LoadT81File):
  - a blokkadat elé odailleszti a ZX81-nevet, ha az adat nem névvel kezdődik;
  - `while(length>0 && buffer2[length-1]!=0x80) length--;` — vagyis a
    blokkot az UTOLSÓ 0x80 bájtig vágja vissza.
A script minden blokkra kiírja: méret, utolsó 0x80 helye, EO által
levágott bájtok száma, E_LINE (0x400C-től a 0x0B-0x0C. offset),
D_FILE, RAMTOP-érték a 0x4026-os szóban, DF_SZ, az első sor tokenje.
"""
import sys
sys.path.insert(0, "/home/z/my-project/GLM/repo/tools")
from zx81sim import load_blocks


def le16(img, off):
    return img[off] | (img[off + 1] << 8)


def analyze(path):
    blocks = load_blocks(path)
    print("fájl:", path)
    print("blokkok száma:", len(blocks))
    tot_cut = 0
    for name, data in blocks:
        n = len(data)
        last80 = n - 1 - data[::-1].index(0x80) if 0x80 in data else -1
        # EO: név hozzáadása, ha az adat 0x00/0x01/0xFF-fel kezdődik
        zxname_len = 0
        if n and data[0] in (0x00, 0x01, 0xFF):
            zxname_len = len(name)
        full = data + b""
        eff = last80 + 1 if last80 >= 0 else 0   # EO számára betölthető
        cut = n - eff
        tot_cut += cut
        sysvars = data[0:0x74]
        info = ""
        base = 0
        if n and data[0] not in (0x00, 0x01, 0xFF):
            # a blokkadat saját maga előtt hordja a ZX81-nevet (utolsó
            # betű 7-es bitje 1) — a kép a név után kezdődik
            k = 0
            while k < n and not (data[k] & 0x80):
                k += 1
            base = k + 1
            info += "név=%r (%d B) " % (
                "".join(chr(c & 0x3F) if 0x26 <= (c & 0x7F) <= 0x3F else "?"
                        for c in data[:k]), base)
        sysvars = data[base:base + 0x74]
        if n - base >= 0x74 and sysvars[0] == 0x00:
            eline = le16(data, base + 0x4014 - 0x4009)
            dfile = le16(data, base + 0x400C - 0x4009)
            word26 = le16(data, base + 0x4026 - 0x4009)
            dfsz = data[base + 0x4022 - 0x4009]
            tok1 = data[base + 0x74 + 4]
            info += ("E_LINE=0x%04X D_FILE=0x%04X [4026]=0x%04X DF_SZ=%d "
                     "1.sor token=0x%02X" % (eline, dfile, word26, dfsz, tok1))
        print("  %-10s hossz=%5d  utolsó 0x80 @%5d  EO levág=%4d  %s"
              % (name, n, last80, cut, info))
    print("  összes levágott bájt:", tot_cut)


if __name__ == "__main__":
    for p in sys.argv[1:]:
        analyze(p)
        print()
