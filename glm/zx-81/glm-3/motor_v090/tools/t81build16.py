#!/usr/bin/env python3
"""t81build16.py - build the 16K ZX81 edition cassette set (v0.5).

Outputs (into ports/zx81/16k/):
  rt16boot.p / .t81         BOOT block: logo + manual + profile questions,
                            chains to RT-BASE16 (no model, short image)
  rt16_base.p / .t81        base: engine + everyday-Hungarian model
  rt16_<topic>.p / .t81     13 topic packs (short images)
  rt16_topics.t81           ONE EO81 cassette: all 15 blocks
  rt16_all.p                the base image as a plain .P

Layout (one 16K pack, 0x4000-0x7FFF):
  0x4009-0x407C  system variables (VERSN=$4009, E_PPC=$400A, D_FILE=$400C,
                 VARS=$4010, RAMTOP word=$4026 - verified against the real
                 ROM: it runs LD IY,$4000, so FLAGS=$4001, D_FILE=$400C)
  0x407D         line 1: 1 REM <engine code> <48-byte persist tail>
                 - the tail is INSIDE line 1, so the ROM's own SAVE
                 writes it to tape and it sits BELOW any line-2 edit
                 point (the editor's MAKE-ROOM never shifts it)
  line 2         2 IF USR 16514 = 1 THEN LOAD "RT-XXXX" + 0x76
                 - v0.4.5: BOTH number literals carry the $7E + 5-byte
                 FP tail (the ROM's run-time scanner S-STK-DEC skips
                 the digits and hunts $7E; bare digits = report B/2)
                 - v0.4.4: the LOAD carries a NAME; the ROM matches it
                 byte-for-byte (IN-NAME/MATCHING, inverted-last-char
                 termination), so the cassette order is free
  line 3         3 IF USR 16514 = 2 THEN SAVE "RT-BASE16"
                 - the /save handoff: the engine returns 2, BASIC
                 executes the ROM's own SAVE command; the user rewinds
                 the tape to the RT-BASE16 block position and records
                 over it - the memories ride inside line 1's REM
  M              model blob (class G, 1970 B, "RTLM" magic) placed at
                 the CHAIN END - the engine finds it by the magic scan,
                 so the exact address is free
  M+1970         topic tag: [index][ascii name, NUL padded, 11 B]
  M+1982         LOAD-name table: [$A1][count=14][14 x 8 display-code
                 names][2 pad] - slot 0 = RT-BASE16, 1..13 = the topics
  0x7B00         D-file: 0x76 + 24 x (32 cells + 0x76) = 793 bytes
                 rows 0-2 = the packed state ('RT2' v2: profile +
                 context + seed + temp + reason + 10 memory events)
  0x7E19         VARS 0x80 marker (base image end)
  0x7FFC         machine stack (16K RAMTOP)

The engine keeps the scrollback ring at RAMTOP-445 (plain RAM above
STKBOT) and reads the state from the D-file work rows.

EO81 container: 4-byte magic, then per block: name[32] + len[16]
(ASCII decimal, NUL padded) + data. Data = the plain .P image bytes
VERBATIM - a RAM image starting at $4009 (VERSN byte first; the user's
demo.T81 decodes exactly this way). v0.4.1's invented 2-byte "FF 00
prefix" shifted the image so the loader read D_FILE=$0001 (ROM
garbage) -> the vertical-bars / rolling-screen freeze.

Usage: t81build16.py <rtchat16.bin> <boot16.bin> <models16_v05-dir> <out-dir>
"""
import os
import sys

Z = 0x4009
PROG = 0x407D
CODE_ORG = 16514
DFILE = 0x7B00
VARS = DFILE + 793
ELINE = VARS + 1
MSIZE = 1030
TAIL_B = 48
RT_TOPICS = [
    ("RTBASE16", "base_g"),
    ("RT-TUDOM", "topic_science"),
    ("RT-ELETV", "topic_lifestyle"),
    ("RT-HOBBI", "topic_hobby"),
    ("RT-EGESZ", "topic_health"),
    ("RT-MUNKA", "topic_work"),
    ("RT-MUVES", "topic_art"),
    ("RT-TANUL", "topic_learning"),
    ("RT-IRODA", "topic_literature"),
    ("RT-FILME", "topic_movies"),
    ("RT-PROGI", "topic_programming"),
    ("RT-ASTRO", "topic_astronomy"),
    ("RT-ASCII", "topic_asciiart"),
    ("RT-VERSE", "topic_verse"),
]


def be16(v):
    return bytes(((v >> 8) & 0xFF, v & 0xFF))


def le16(v):
    return bytes((v & 0xFF, (v >> 8) & 0xFF))


def sysvars():
    """116 bytes = RAM $4009-0x407C (the .P/T81 image starts at $4009;
    the user's demo cassette proves the loader writes it there).
    Layout proven THREE ways: the z88dk appmake +zx81 reference .P, the
    user's WORKING v0.4.5 rt16_base.p, and the emulator-written
    demo.T81 - all three agree on every byte position used here:
      $400A E_PPC=1   $400C D_FILE   $400E DF_CC=D_FILE+1
      $4010 VARS      $4012 DEST=0   $4014 E_LINE   $4016 CH_ADD
      $4018 X_PTR=0   $401A STKBOT   $401C STKEND   $401E BREG=0
      $401F MEM=$405D $4021-$4025 zeros (LASTK=0)
      $4026 WORD = $7FFD  <- the 16K stack top; the emulator's quickload
          takes the machine stack pointer from THIS word - v0.5.0 wrote
          it at $4028 and the machine died with SP=$0002 (the instant
          freeze, no error text)
      $4022 DF_SZ = 2  <- the lower screen is TWO rows (the editor's
          input area); appmake AND the emulator-written demo both carry
          02 there, our old files had 0
      $4028 byte = 0   $4029 WORD = D_FILE (the display-file copy,
          $7B00 in the working v0.4.5 and in appmake)
      everything else zero."""
    s = bytearray(116)
    s[1:3] = le16(1)            # E_PPC = 1 (little-endian word!)
    s[3:5] = le16(DFILE)        # D_FILE
    s[5:7] = le16(DFILE + 1)    # DF_CC (home after CLS)
    s[7:9] = le16(VARS)         # VARS
    s[9:11] = le16(0)           # DEST
    s[11:13] = le16(ELINE)      # E_LINE
    s[13:15] = le16(ELINE + 4)  # CH_ADD
    s[15:17] = le16(0)          # X_PTR
    s[17:19] = le16(ELINE + 5)  # STKBOT
    s[19:21] = le16(ELINE + 5)  # STKEND
    s[21] = 0                   # BREG
    s[22:24] = le16(0x405D)     # MEM
    s[29:31] = le16(0x7FFD)     # $4026 = the 16K stack top (SP source!)
    s[31] = 0                   # $4028
    s[25] = 2                   # DF_SZ = 2: rows 22-23 = the ROM's lower screen
    s[32:34] = le16(DFILE)      # $4029 = D_FILE copy
    return bytes(s)


def zx_digits(n):
    return bytes(0x1C + int(ch) for ch in str(n))


def zx_name(s):
    """ASCII block name -> ZX81 display codes. The ROM's LOAD compares
    the tape bytes with the line-2 slot byte-for-byte, so the table
    must hold exactly the codes the tape header will carry (the
    emulator converts the ASCII EO81 name field the same way).
    Keyboard tables at $007E: A-Z = $26-$3F, 0-9 = $1C-$25, '-'=$16."""
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
    """ZX81/Spectrum 5-byte floating point: [exponent][4 mantissa
    bytes] - exponent = e+128 with 0.5 <= n/2^e < 1, the mantissa
    carries the fraction with its leading 1 (bit 31) replaced by the
    sign. VERIFIED against the user's ARTILLER.P (a real ZX81 SAVE):
    16396 -> 8f 00 18 00 00, 500 -> 89 7a 00 00 00.

    Why the tail is not optional: the ROM's run-time scanner
    (S-STK-DEC, $106F) SKIPS the digit characters and loops until it
    finds the $7E number marker, then stacks the 5 hidden bytes. A
    bare digit run in a hand-built line makes it hunt $7E past the end
    of the line - that was the recurring "B/2" (report $0B, Nonsense
    in BASIC). The editor's typing pass (S-DECIMAL) appends the tail
    automatically, which is why the user's re-typed line worked."""
    e = n.bit_length()
    m = round(n / (1 << e) * (1 << 32))
    assert 1 << 31 <= m < 1 << 32, f"zx_fp({n}) not normalized"
    return bytes([0x80 + e, (m >> 24) & 0x7F, (m >> 16) & 0xFF,
                  (m >> 8) & 0xFF, m & 0xFF])


def dfile_blank():
    # leading 0x76 + 24 rows of (32 spaces + 0x76) = 793 bytes
    return b"\x76" + (b"\x00" * 32 + b"\x76") * 24


def usrlines(load_name, with_save):
    """Program lines 2 (and 3) with $7E+FP tails after EVERY number
    literal (16514, 1, 2 - the S-STK-DEC requirement)."""
    l2 = (b"\xFA\xD4" +                                          # IF USR
          zx_digits(CODE_ORG) + b"\x7E" + zx_fp(CODE_ORG) +      # 16514
          b"\x14\x1D" +                                          # = 1
          b"\x7E" + zx_fp(1) +                                   # 1
          b"\xDE\xEF\x0B" +                                      # THEN LOAD "
          zx_name(load_name) + b"\x0B")                          # name "
    assert len(l2) == 33
    lines = [be16(2) + le16(len(l2) + 1) + l2 + b"\x76"]
    if with_save:
        l3 = (b"\xFA\xD4" +
              zx_digits(CODE_ORG) + b"\x7E" + zx_fp(CODE_ORG) +
              b"\x14\x1E" +                                      # = 2 (0x1C+2!)
              b"\x7E" + zx_fp(2) +
              b"\xDE\xF8\x0B" +                                  # THEN SAVE "
              zx_name("RTBASE16") + b"\x0B")
        assert len(l3) == 33
        lines.append(be16(3) + le16(len(l3) + 1) + l3 + b"\x76")
    return b"".join(lines)


def build_image(code, model, tag_idx, tag_name, load_name, with_save):
    """The SHORT core of a chat-block image: sysvars + program lines +
    model + tag + name table, ending right below the D-file zone.
    Everything the ROM's LOAD-chain touches; the display file above
    stays untouched so the packed state rows survive block swaps."""
    body1 = b"\xEA" + code
    l1 = len(body1) + 1
    lines = [be16(1) + le16(l1) + body1 + b"\x76",
             usrlines(load_name, with_save)]
    prog = b"".join(lines) + b"\x76"  # + end-of-program marker

    img = bytearray()
    img += sysvars()                       # 0x4009-0x407C
    assert len(img) == PROG - Z
    img += prog                             # 0x407D .. M
    M = Z + len(img)
    assert M <= DFILE - 17 - 116 - 12 - MSIZE, \
        f"chain too big: model would start at 0x{M:04X}"
    img += model                            # M .. M+MSIZE ("RTLM")
    tag = M + MSIZE
    nm = tag_name.encode()
    img += bytes([tag_idx]) + nm.ljust(11, b"\0")

    tab = tag + 12
    img += b"\xA1" + bytes([len(RT_TOPICS)])
    for nm, _ in RT_TOPICS:
        img += zx_name(nm)
    img += b"\x00\x00"
    tabend = Z + len(img) - 1
    assert tabend <= DFILE - 17, f"name table ends 0x{tabend:04X}, want <= 0x{DFILE-17:04X}"
    assert img[M - Z:M - Z + 4] == b"RTLM"
    slot = PROG + 4 + 1 + len(code) + 4 + 24
    assert 0x4086 <= slot < M - 4, f"LOAD slot at 0x{slot:04X}?"
    return bytes(img), M


def make_full(img):
    """Extend a short core to a FULL quickload image: pad to D_FILE,
    append the blank display file and the VARS marker. A fresh machine
    gets a valid display file -> no display-generator runaway."""
    out = bytearray(img)
    out += b"\x00" * (DFILE - Z - len(out))
    out += dfile_blank()
    out += b"\x80"
    return bytes(out)


def build_boot(code):
    """The BOOT block, FULL image: logo + manual + profile questions +
    2 IF USR 16514 = 1 THEN LOAD "RTBASE16", then pad + blank display
    file + VARS marker - on a freshly reset machine this is the first
    thing loaded, so the display file MUST be valid."""
    body1 = b"\xEA" + code
    l1 = len(body1) + 1
    lines = [be16(1) + le16(l1) + body1 + b"\x76",
             usrlines("RTBASE16", False)]
    prog = b"".join(lines) + b"\x76"
    img = bytearray()
    img += sysvars()
    img += prog
    assert Z + len(img) < DFILE - 793, "boot chain too big"
    return make_full(bytes(img))


def wrap_eo81(name, data):
    assert len(name) <= 32
    hdr = name.encode().ljust(32, b"\0") + str(len(data)).encode().ljust(16, b"\0")
    return hdr + data


def main():
    code_bin, boot_bin, models_dir, out_dir = sys.argv[1:5]
    code = open(code_bin, "rb").read()
    boot = open(boot_bin, "rb").read()
    os.makedirs(out_dir, exist_ok=True)

    blocks = []
    bootimg = build_boot(boot)
    # no standalone boot files: a boot-only cassette has no RT-BASE16
    # to chain to, the ROM's LOAD would search forever ("does nothing");
    # the boot lives inside the multiload (block 1)
    blocks.append(("RTBOOT01", bootimg))
    print(f"RTBOOT01   boot (FULL)      image {len(bootimg)} B "
          f"(0x4009-0x{Z + len(bootimg):04X})")

    for i, (nm, model_file) in enumerate(RT_TOPICS):
        model = open(f"{models_dir}/{model_file}.bin", "rb").read()
        assert len(model) == MSIZE, f"{model_file}: {len(model)} != {MSIZE}"
        assert model[:4] == b"RTLM", f"{model_file}: no RTLM magic"
        base = (i == 0)
        short, M = build_image(code, model, i, nm, nm, True)
        stem = "rt16_base" if base else f"rt16_{model_file[len('topic_'):]}"
        # GLM + version in every file name the user asked for
        stem = f"GLM_v054_{stem}"
        full = make_full(short)
        open(f"{out_dir}/{stem}.p", "wb").write(full)
        open(f"{out_dir}/{stem}.t81", "wb").write(wrap_eo81(nm, full))
        # in the multiload tape only the boot is FULL: every later
        # block is SHORT so the packed state rows and the scrollback
        # survive the block swap (the display file above stays as the
        # boot/base established it)
        blocks.append((nm, short if not base else short))
        kind = "base" if base else "topic"
        print(f"{nm:10} {model_file:18} p={len(full)} B (FULL) "
              f"t81={len(short)} B (SHORT), model at 0x{M:04X}")

    tape = b"EO81" + b"".join(wrap_eo81(nm, d) for nm, d in blocks)
    open(f"{out_dir}/GLM_v054_RT16_TOPICS.t81", "wb").write(tape)
    print(f"rt16_topics.t81: {len(tape)} B, {len(blocks)} blocks "
          "(BOOT + BASE + 13 topics)")


if __name__ == "__main__":
    main()
