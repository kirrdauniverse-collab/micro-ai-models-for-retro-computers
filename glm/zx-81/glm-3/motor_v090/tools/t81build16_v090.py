#!/usr/bin/env python3
"""t81build16_v090.py - build the v0.9.0 16K cassette set.

Blocks (EO81 container, the v0.6.5/v0.8.x proven layout):
  RTBOOT01   boot: logo + guide + memory-restore Y/N + profile (FULL image)
  RTMEM16    the raw persistent-memory block: [7 name codes][152 zone bytes]
             + one trailing 0x80 (the EO81 trim guard). The ROM LOAD
             command would treat it as a program block - NEVER load it
             from the editor; only the boot's motor-side loader reads it.
  RTBASE16   base: engine + base model + tag + name table (SHORT image)
  RT-TUDOM.. RT-VERSE: the 13 topic packs (SHORT images, models reused
             byte-exact from the v0.8.1 cassette)

Image layout (per chat block, 0x4009..):
  sysvars 116 B | line1 = REM <engine> | line2 = IF USR 16514=1 THEN
  LOAD "<self>" | line3 = IF USR 16514=2 THEN SAVE "RTBASE16" | $76
  | model 1030 B (RTLM) | tag [idx][name 11] | name table [$A1][14]
  [14 x 8 codes][2 pad] | 0x80 (E_LINE-1)  - everything ends BELOW the
  D-file at 0x7B00 so the packed state rows, the ring, the status row
  and the persistent zone (0x7E50) survive every block swap.

The crt0 tail-trap fix (v0.8.1): every engine binary is scanned for
  LD A,(CDFFLAG=$403B) AND $80 JP Z,$02A9
  (3A 3B 40 E6 80 CA A9 02)  ->  the JP is replaced with OUT ($FE); EI
  (D3 FE FB): NMI-off exits turn the generator ON instead of falling
  into the ROM's NMI-wait freeze.

Usage: t81build16_v090.py <motor.bin> <boot.bin> <models-dir> <out-dir>
"""
import os
import sys

Z = 0x4009
PROG = 0x407D
CODE_ORG = 16514
DFILE = 0x7B00
VARS = 0x7AF5               # the working chat blocks' exact value
ELINE = VARS + 1            # 0x7AF6
VARS_BOOT = 0x7E19          # the working boot's value (past the D-file)
ELINE_BOOT = VARS_BOOT + 1
MSIZE = 1030

RT_TOPICS = [
    ("RTBASE16", "rtbase16"),
    ("RT-TUDOM", "rt-tudom"),
    ("RT-MAGYR", "rt-magyr"),
    ("RT-HOBBI", "rt-hobbi"),
    ("RT-EGESZ", "rt-egesz"),
    ("RT-MUNKA", "rt-munka"),
    ("RT-MUVES", "rt-muves"),
    ("RT-TANUL", "rt-tanul"),
    ("RT-IRODA", "rt-iroda"),
    ("RT-FILME", "rt-filme"),
    ("RT-PROGI", "rt-progi"),
    ("RT-ASTRO", "rt-astro"),
    ("RT-ASCII", "rt-ascii"),
    ("RT-VERSE", "rt-verse"),
]

TRAP_OLD = bytes([0x3A, 0x3B, 0x40, 0xE6, 0x80, 0xCA, 0xA9, 0x02])
TRAP_NEW = bytes([0xD3, 0xFE, 0xFB])       # OUT ($FE); EI


def be16(v):
    return bytes(((v >> 8) & 0xFF, v & 0xFF))


def le16(v):
    return bytes((v & 0xFF, (v >> 8) & 0xFF))


def fix_trap(code):
    """v0.8.1 farokcsapda-javitas a frissen forditott binaerben."""
    n = 0
    out = bytearray(code)
    i = 0
    while True:
        j = out.find(TRAP_OLD, i)
        if j < 0:
            break
        out[j + 5:j + 8] = TRAP_NEW
        n += 1
        i = j + 8
    return bytes(out), n


def sysvars(eline, ch_add):
    """116 bytes = RAM $4009-0x407C — the WORKING v0.8.1 blocks' exact
    recipe (byte-dumped from the proven cassette):
      $400A E_PPC=1  $400C D_FILE=0x7B00  $400E DF_CC=0x7B01
      $4010 VARS=0x7AF5 (BELOW the D-file: chat-block swaps keep it)
      $4012 DEST=0  $4014 E_LINE  $4016 CH_ADD  $4018 X_PTR=0
      $401A STKBOT = STKEND = E_LINE+5
      $401E BREG=0  $401F MEM=$405D  $4022 DF_SZ=2
      $4026 RAMTOP-hi=0xFD (the 16K stack top; the ROM reads the word
      at $4004 — that lives in the 8-byte name prefix area? NO: the
      name prefix is TAPE-side only, $4004 is part of the image's own
      area BEFORE $4009 — see name_prefix() below)
      $4029 D_FILE copy
    """
    s = bytearray(116)
    s[1:3] = le16(1)            # E_PPC = 1
    s[3:5] = le16(DFILE)        # D_FILE
    s[5:7] = le16(DFILE + 1)    # DF_CC
    s[7:9] = le16(VARS)         # VARS (below the D-file!)
    s[9:11] = le16(0)           # DEST
    s[11:13] = le16(eline)      # E_LINE
    s[13:15] = le16(ch_add)     # CH_ADD (line 3's SAVE tail in the boot)
    s[15:17] = le16(0)          # X_PTR
    s[17:19] = le16(eline + 5)  # STKBOT
    s[19:21] = le16(eline + 5)  # STKEND
    s[21] = 0                   # BREG
    s[22:24] = le16(0x405D)     # MEM
    s[29:31] = le16(0x7FFD)     # $4026 = the 16K stack top
    s[31] = 0                   # $4028
    s[25] = 2                   # DF_SZ = 2 (offset 25 = $4022!)
    s[32:34] = le16(DFILE)      # $4029 = D_FILE copy
    return bytes(s)


def zx_digits(n):
    return bytes(0x1C + int(ch) for ch in str(n))


def zx_name(s):
    """ASCII block name -> ZX81 display codes (the ROM LOAD compares
    the tape bytes with the line-2 slot byte-for-byte)."""
    assert len(s) == 8, f"block name must be 8 chars: {s!r}"
    out = []
    for ch in s:
        if "A" <= ch <= "Z":
            out.append(0x26 + ord(ch) - 65)
        elif "0" <= ch <= "9":
            out.append(0x1C + int(ch))
        elif ch == "-":
            out.append(0x16)
        else:
            raise ValueError(f"bad block-name char {ch!r}")
    return bytes(out)


def zx_fp(n):
    """ZX81 5-byte floating point tail (S-STK-DEC requirement)."""
    e = n.bit_length()
    m = round(n / (1 << e) * (1 << 32))
    assert 1 << 31 <= m < 1 << 32, f"zx_fp({n}) not normalized"
    return bytes([0x80 + e, (m >> 24) & 0x7F, (m >> 16) & 0xFF,
                  (m >> 8) & 0xFF, m & 0xFF])


def dfile_blank():
    # leading 0x76 + 24 rows of (32 spaces + 0x76) = 793 bytes
    return b"\x76" + (b"\x00" * 32 + b"\x76") * 24


def name_prefix(name):
    """The 8 tape-name code bytes the working blocks carry BEFORE the
    image: display codes, LAST byte with bit7 set (the ROM's
    inverted-name terminator — IN-NAME/MATCHING matches them against
    the line-2 LOAD slot). Without this prefix the ROM eats the first
    image bytes as the name and the whole picture shifts by 8 -> the
    '0/0 rows too high + dark square' boot corruption."""
    codes = zx_name(name)
    return codes[:-1] + bytes([codes[-1] | 0x80])


def usrlines(load_name, with_save):
    """Lines 2 (and 3) with $7E+FP tails after EVERY number literal.
    Token table (ROM 0x0111, the 8. menet correction): IF=$FA USR=$D4
    THEN=$DE LOAD=$EF SAVE=$F8; '='=$14; digits=$1C+n; quotes=$0B."""
    l2 = (b"\xFA\xD4" +
          zx_digits(CODE_ORG) + b"\x7E" + zx_fp(CODE_ORG) +
          b"\x14\x1D" +
          b"\x7E" + zx_fp(1) +
          b"\xDE\xEF\x0B" +
          zx_name(load_name) + b"\x0B")
    assert len(l2) == 33
    lines = [be16(2) + le16(len(l2) + 1) + l2 + b"\x76"]
    if with_save:
        l3 = (b"\xFA\xD4" +
              zx_digits(CODE_ORG) + b"\x7E" + zx_fp(CODE_ORG) +
              b"\x14\x1E" +
              b"\x7E" + zx_fp(2) +
              b"\xDE\xF8\x0B" +
              zx_name("RTBASE16") + b"\x0B")
        assert len(l3) == 33
        lines.append(be16(3) + le16(len(l3) + 1) + l3 + b"\x76")
    return b"".join(lines)


def build_image(code, model, tag_idx, tag_name, load_name, with_save):
    """A SHORT chat-block image: the WORKING v0.8.1 recipe.
    The tape block = name_prefix(load_name) + image (see name_prefix);
    the image itself = sysvars + program + model + tag + name table,
    ending at the 0x80 VARS marker (VARS=0x7AF5, E_LINE=0x7AF6)."""
    body1 = b"\xEA" + code
    l1 = len(body1) + 1
    lines = [be16(1) + le16(l1) + body1 + b"\x76",
             usrlines(load_name, with_save)]
    prog = b"".join(lines) + b"\x76"

    img = bytearray(sysvars(VARS, 0))
    assert len(img) == PROG - Z
    img += prog
    M = Z + len(img)
    assert M <= DFILE - 17 - 116 - 12 - MSIZE, \
        f"chain too big: the model would start at 0x{M:04X} " \
        f"(limit 0x{DFILE - 17 - 116 - 12 - MSIZE:04X})"
    img += model
    tag = M + MSIZE
    nm = tag_name.encode()
    img += bytes([tag_idx]) + nm.ljust(11, b"\0")

    tab = tag + 12
    img += b"\xA1" + bytes([len(RT_TOPICS)])
    for nm2, _ in RT_TOPICS:
        img += zx_name(nm2)
    img += b"\x00\x00"
    img += b"\x80"
    el = Z + len(img)          # E_LINE = the 0x80 marker's address
    assert el == VARS + 1, f"E_LINE 0x{el:04X} != VARS+1 0x{VARS+1:04X}"
    assert img[M - Z:M - Z + 4] == b"RTLM"
    return bytes(img), M


def make_full(img):
    out = bytearray(img)
    out += b"\x00" * (DFILE - Z - len(out))
    out += dfile_blank()
    out += b"\x80"
    return bytes(out)


def build_boot(code):
    """The FULL boot image: sysvars + program + blank D-file + 0x80.
    The working boot's VARS sat at 0x7E19 (past the D-file end)."""
    body1 = b"\xEA" + code
    l1 = len(body1) + 1
    lines = [be16(1) + le16(l1) + body1 + b"\x76",
             usrlines("RTBASE16", False)]
    prog = b"".join(lines) + b"\x76"
    img = bytearray()
    img += sysvars(ELINE_BOOT, 0)
    img += prog
    assert Z + len(img) <= DFILE, "boot chain too big"
    out = bytearray(img)
    out += b"\x00" * (DFILE - Z - len(out))
    out += dfile_blank()
    out += b"\x80"
    return bytes(out)


def build_memblock(zone_len=152):
    """The RTMEM16 raw block: name codes + zone bytes + a 0x80 tail
    (the EO81 trim guard). The ROM's own loader must NEVER be pointed
    at this block; only the boot's motor-side loader reads it."""
    name = bytearray()
    for ch in "RTMEM16":
        if "A" <= ch <= "Z":
            name.append(0x26 + ord(ch) - 65)
        elif "0" <= ch <= "9":
            name.append(0x1C + int(ch))
    name[-1] |= 0x80                  # the inverted terminator
    return bytes(name) + b"\x00" * zone_len + b"\x80"


def wrap_eo81(name, data):
    assert len(name) <= 32
    hdr = name.encode().ljust(32, b"\0") + str(len(data)).encode().ljust(16, b"\0")
    return hdr + data


def main():
    code_bin, boot_bin, models_dir, out_dir = sys.argv[1:5]
    code = open(code_bin, "rb").read().rstrip(b"\x00")
    code, nfix = fix_trap(code)
    boot = open(boot_bin, "rb").read().rstrip(b"\x00")
    boot, nbfix = fix_trap(boot)
    os.makedirs(out_dir, exist_ok=True)
    print(f"farokcsapda-javitas: motor {nfix}x, boot {nbfix}x")

    blocks = []
    bootimg = build_boot(boot)
    blocks.append(("RTBOOT01", name_prefix("RTBOOT01") + bootimg))
    print(f"RTBOOT01   boot (FULL)      block {len(bootimg) + 8} B")
    blocks.append(("RTMEM16", build_memblock()))
    print(f"RTMEM16    raw memory block  {len(build_memblock())} B")

    for i, (nm, model_file) in enumerate(RT_TOPICS):
        model = open(f"{models_dir}/{model_file}.bin", "rb").read()
        assert len(model) == MSIZE, f"{model_file}: {len(model)} != {MSIZE}"
        assert model[:4] == b"RTLM", f"{model_file}: no RTLM magic"
        short, M = build_image(code, model, i, nm, nm, True)
        blocks.append((nm, name_prefix(nm) + short))
        print(f"{nm:10} model 0x{M:04X}      block {len(short) + 8} B")

    tape = b"EO81" + b"".join(wrap_eo81(nm, d) for nm, d in blocks)
    open(f"{out_dir}/GLM_PicoAI_v0.9.0_kazetta.T81", "wb").write(tape)
    print(f"kazetta: {len(tape)} B, {len(blocks)} blokk "
          "(BOOT + RTMEM16 + BASE + 13 tema)")


if __name__ == "__main__":
    main()
