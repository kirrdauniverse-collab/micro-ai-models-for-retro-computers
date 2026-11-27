#!/usr/bin/env python3
"""v0.8.0 — a v0.6.5 kazetta képfájl-szintű javítása.

GYÖKÉROK (bájtszinten bizonyítva):
  A v0.5.4/v0.6.5 készítő a program-vég 0x80 jelzője helyett 0x76-ot
  írt a sorok után (a builder forrásában: `prog = lines + b"\\x76"
  # + end-of-program marker` — a komment jó, a bájt hibás). A ROM a
  sorokat walkingálva a 0x76-nál új sorfejet olvas: a modell-blob
  bájtjaiból "sorszám=0x7652, hossz=19508" adódik — a keresés
  kilép a RAM-ból; a lánc-betöltés után ez adja a grafikus
  karaktereket és a videó-generátorba való szaladást (PC 004x,
  fehér kép), amit a felhasználó látott.
  Ráadásul a blokkok CH_ADD-je a munkaterületre (E_LINE+4) mutat,
  ahova a ROM betöltése fel sem ír (E_LINE-1-ig olvas) — az
  értelmező a lánc-betöltés után a régi boot-blokk ottmaradt
  bájtjait pásztázza.

JAVÍTÁS blokkonként (a motor binárisát nem érintjük):
  1. a sorok utáni 0x76 -> 0x80 (program-vég jelző);
  2. CH_ADD := az utolsó sor lezáró 0x76-jának címe — a lánc-betöltés
     után az értelmező azonnal sorvéget lát, és a következő sorra
     (E_PPC=1 -> 2. sor: IF USR ... = a betöltött blokk motorja)
     lép: a lánc a tervezett módon folytatódik.

A konténer (EO81 / [32 név][16 hossz][adat]) hosszmezői változatlanok:
a javítás bájton-belüli csere, a blokkhossz nem változik.
"""
import os
import sys

SRC = "/home/z/my-project/download/GLM_PicoAI_v0.6.5_kazetta.T81"
SRC_DIR = ("/home/z/my-project/GLM/tmp/dl/extracted/reszben_Hasznalhatoak/"
           "GLM-retro-tinyllm-v0.6.5-16k")
OUT_DIR = "/home/z/my-project/download"
ZIP_STAGE = "/home/z/my-project/GLM/tmp/pack_v080"

# képen belüli eltolások (a kép a 0x4009-től)
Z = 0x4009
PROG = 0x407D
OFF_CH_ADD = 0x4016 - Z          # 13


def le16(b):
    return b[0] | (b[1] << 8)


def be16(b):
    return (b[0] << 8) | b[1]


def parse_container(raw):
    """[EO81?] + blokkok: (név32, hossz16-ASCII, adat) listája + offszetek."""
    i = 4 if raw[:4] == b"EO81" else 0
    blocks = []
    while i + 48 <= len(raw):
        name = raw[i:i + 32].rstrip(b"\0")
        lenb = raw[i + 32:i + 48].rstrip(b"\0")
        if not lenb.isdigit():
            raise ValueError("hibás blokkfejléc @%d" % i)
        n = int(lenb)
        blocks.append((i, name, n, i + 48, i + 48 + n))
        i += 48 + n
    if i != len(raw):
        raise ValueError("a konténer nem ért véget a blokkokkal")
    return blocks


def walk_lines(d, data_off):
    """A BASIC-sorok és a sorok utáni bájt pozíciója az adaton belül.
    data_off: a kép eleje az adaton belül (a v0.6.5 blokkokban 8 bájtos
    ZX81-név-előtag a kép előtt)."""
    p = data_off + (PROG - Z)
    lines = []
    while p + 4 <= len(d):
        num = (d[p] << 8) | d[p + 1]
        ln = d[p + 2] | (d[p + 3] << 8)
        if num == 0 or ln == 0 or ln > 16000:
            break
        lines.append((num, ln, p))
        p += 4 + ln
    return lines, p


def patch_image_in_data(data, data_off, log):
    """A javítás egy blokk-adaton belül; visszatérési érték az új adat."""
    d = bytearray(data)
    lines, p = walk_lines(d, data_off)
    if not lines:
        raise ValueError("nem találtam BASIC-sorokat")
    marker_pos = p
    if d[marker_pos] not in (0x76, 0x80):
        raise ValueError("a sorok után nem 0x76/0x80 áll: %02X @%d"
                         % (d[marker_pos], marker_pos))
    was = d[marker_pos]
    d[marker_pos] = 0x80                       # 1. javítás
    last76 = marker_pos - 1                     # az utolsó sor 0x76-ja
    addr76 = Z + (last76 - data_off)
    ch_pos = data_off + OFF_CH_ADD
    old_ch = le16(d[ch_pos:ch_pos + 2])
    d[ch_pos:ch_pos + 2] = bytes((addr76 & 0xFF, addr76 >> 8))  # 2. javítás
    log.append("  sorok=%d  marker @0x%04X: %02X->80  CH_ADD: 0x%04X->0x%04X"
               % (len(lines), Z + (marker_pos - data_off), was, old_ch, addr76))
    return bytes(d)


def patch_t81(raw, log):
    blocks = parse_container(raw)
    out = bytearray(raw)
    for (hstart, name, n, dstart, dend) in blocks:
        data = bytes(out[dstart:dend])
        # v0.6.5 elöljárás: 8 bájt ZX81-név (kódok 0x1C-0x3F, az
        # utolsó bájt |0x80), utána a kép 0x00 VERSN-nel
        is_name8 = (8 <= len(data) and 0x1C <= (data[7] & 0x7F) <= 0x3F
                    and (data[7] & 0x80) and data[8] == 0x00)
        data_off = 8 if is_name8 else 0
        # a v0.6.5 blokkok: 8 bájtos ZX81-név-előtag a kép előtt
        img = data[data_off:]
        if img[0] not in (0x00, 0x37) and data_off == 0:
            # .P: nincs előtag
            pass
        log.append("%s (%d B):" % (name.decode("ascii", "replace").strip(), n))
        patched = patch_image_in_data(data, data_off, log)
        out[dstart:dend] = patched
    return bytes(out)


def patch_p(raw, log):
    """Egyszerű .P: a kép maga (név-előtag nélkül)."""
    d = bytearray(raw)
    lines, p = walk_lines(d, 0)
    if not lines:
        raise ValueError(".P: nincsenek sorok")
    log.append("  sorok=%d  marker @0x%04X: %02X->80" %
               (len(lines), Z + p, d[p]))
    d[p] = 0x80
    addr76 = Z + p - 1
    ch = 0x4016 - Z
    d[ch:ch + 2] = bytes((addr76 & 0xFF, addr76 >> 8))
    log.append("  CH_ADD -> 0x%04X" % addr76)
    return bytes(d)


def main():
    os.makedirs(ZIP_STAGE, exist_ok=True)
    log = []

    # 1) a fő kazetta
    raw = open(SRC, "rb").read()
    out = patch_t81(raw, log)
    dst = os.path.join(OUT_DIR, "GLM_PicoAI_v0.8.0_kazetta.T81")
    open(dst, "wb").write(out)
    print("kazetta: %s (%d B, forrás %d B — hossz változatlan: %s)"
          % (dst, len(out), len(raw), len(out) == len(raw)))

    # 2) az egyedi .t81 és .p fájlok (a v0.6.5 készlet)
    singles = os.path.join(ZIP_STAGE, "kazetta")
    os.makedirs(singles, exist_ok=True)
    for fn in sorted(os.listdir(SRC_DIR)):
        src = os.path.join(SRC_DIR, fn)
        if fn.endswith(".t81"):
            r = open(src, "rb").read()
            # a singles egy blokkból állnak (EO81 nélkül is lehet)
            try:
                o = patch_t81(r, log)
            except ValueError:
                continue
            open(os.path.join(singles, fn.replace("v065", "v080")), "wb").write(o)
        elif fn.endswith(".p"):
            r = open(src, "rb").read()
            if len(r) < 200:
                continue
            try:
                o = patch_p(r, log)
            except ValueError:
                continue
            open(os.path.join(singles, fn.replace("v065", "v080")), "wb").write(o)
    print("\n".join(log))
    print("egyedi fájlok: %s" % singles)


if __name__ == "__main__":
    main()
