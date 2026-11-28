#!/usr/bin/env python3
"""verify_findings.py - reproduces every factual claim in docs/BUGS.md and
docs/ROM_ROUTINES.md. Standard library only.

usage: verify_findings.py ROM_FILE MODEL_BIN [OLD_48K_IMAGE.p]

ROM_FILE      the ZX81 'standard' v1 ROM (8192 bytes). NOT shipped in this repo.
MODEL_BIN     an RTLM model blob, e.g. models/base_f.bin
OLD_48K_IMAGE optional: the GLM-built 48K .P image (retro_tinyllm.p)
"""
import struct
import sys

PASS, FAIL = "PASS", "FAIL"
results = []


def check(name, ok, detail=""):
    results.append((name, ok))
    print(f"[{PASS if ok else FAIL}] {name}" + (f"  ({detail})" if detail else ""))


def check_rom(rom):
    # FAST = RES 6,(IY+$3B) at $0F23 ; SLOW = SET 6,(IY+$3B) at $0F28
    check("ROM $0F23 is FAST (FD CB 3B B6)", rom[0x0F23:0x0F27] == bytes([0xFD, 0xCB, 0x3B, 0xB6]))
    check("ROM $0F28 is SLOW (FD CB 3B F6)", rom[0x0F28:0x0F2C] == bytes([0xFD, 0xCB, 0x3B, 0xF6]))
    # $0F2B is the LAST byte of the SLOW instruction, not an entry point
    check("ROM $0F2B is mid-instruction (byte F6)", rom[0x0F2B] == 0xF6)
    check("ROM $0A2A is CLS (LD B,$18 ; RES 1,(IY+1))",
          rom[0x0A2A:0x0A2E] == bytes([0x06, 0x18, 0xFD, 0xCB]), "heuristic")
    check("ROM $02BB is KEYBOARD (LD HL,$FFFF ; LD BC,$FEFE)",
          rom[0x02BB:0x02BB + 3] == bytes([0x21, 0xFF, 0xFF]) and rom[0x02BE] == 0x01)
    # KEYBOARD stores its result in LAST_K ($4028): LD (nn),A at $02E3
    check("ROM $02E3 stores key result to LAST_K $4028 (32 28 40)",
          rom[0x02E3:0x02E6] == bytes([0x32, 0x28, 0x40]))
    # LD-BYTES candidate ($0340) starts with CALL $03A8 (tape-setup) - recorded, not behaviour-tested
    check("ROM $0340 is tape block reader entry (CALL $03A8)",
          rom[0x0340:0x0343] == bytes([0xCD, 0xA8, 0x03]), "structural only")
    check("ROM $0010 is PRINT-A entry (AND A ; JP NZ,$07F1)",
          rom[0x0010:0x0014] == bytes([0xA7, 0xC2, 0xF1, 0x07]))


def keyword_tokens(rom):
    """Decode the ROM keyword table (entries start at $0140, token = $D0 + index).
    Returns {keyword: token} for the anchors we need. Symbol entries decode as '?'."""
    letters = {0x26 + i: chr(ord('A') + i) for i in range(26)}
    ents, cur = [], []
    for a in range(0x0140, 0x0230):
        cur.append(rom[a])
        if rom[a] & 0x80:
            ents.append("".join(letters.get(x & 0x7F, "?") for x in cur))
            cur = []
    out = {}
    for name in ("REM", "RAND", "USR", "STOP", "RUN", "SLOW", "FAST"):
        if name in ents:
            out[name] = 0xD0 + ents.index(name)
    return out


def check_tokens(rom):
    tok = keyword_tokens(rom)
    check("ROM keyword table: REM token = $EA", tok.get("REM") == 0xEA, hex(tok.get("REM", 0)))
    check("ROM keyword table: RAND token = $F9", tok.get("RAND") == 0xF9)
    check("ROM keyword table: USR token = $D4", tok.get("USR") == 0xD4)
    check("ROM keyword table: STOP token = $E3 (STOP = error 9)", tok.get("STOP") == 0xE3,
          hex(tok.get("STOP", 0)))


def check_line2_fix():
    """The corrected line 2 as token bytes: RAND USR 16514 <5-byte number> NEWLINE.
    Number 16514 = $4082: integer form 00 00 lo hi 00 after the $7E marker."""
    body = bytes([0xF9, 0xD4]) + bytes([0x1D, 0x22, 0x21, 0x1D, 0x20]) \
        + bytes([0x7E, 0x00, 0x00, 0x82, 0x40, 0x00]) + bytes([0x76])
    check("corrected line 2 body is 14 bytes (RAND USR 16514)", len(body) == 14, len(body))


def check_model(m, buffer_len=None):
    check("model magic RTLM", m[:4] == b"RTLM")
    ver = struct.unpack("<H", m[4:6])[0]
    check("model version == 2", ver == 2, f"got {ver}")
    vocab, ctx, emb, h1, h2 = struct.unpack("<5H", m[8:18])
    check("model dims vocab=45 ctx=8 emb=10 h1=16 h2=0",
          (vocab, ctx, emb, h1, h2) == (45, 8, 10, 16, 0),
          f"{vocab},{ctx},{emb},{h1},{h2}")
    cs = "\n abcdefghijklmnopqrstuvwxyz,.?!'0123456789:-"
    check("model charset table matches engine RT_CHARSET (45 chars)",
          m[28:28 + 45] == cs.encode())
    # the correct checksum: additive sum over the model's OWN bytes (size-2)
    stored = struct.unpack("<H", m[-2:])[0]
    check("checksum over model size (len-2) matches stored", sum(m[:-2]) & 0xFFFF == stored)
    if buffer_len is not None:
        # what rt_model_load does today: len = RT_APP_MODEL_MAX (10240)
        buf = m + bytes(buffer_len - len(m))
        s = sum(buf[:buffer_len - 2]) & 0xFFFF
        stored_at_end = struct.unpack("<H", buf[buffer_len - 2:buffer_len])[0]
        check(f"BUG REPRODUCTION: checksum over buffer len {buffer_len} matches (expected FAIL)",
              s == stored_at_end, f"computed {s:#06x}, read {stored_at_end:#06x}")


def check_old_image(img):
    off = 0x40BE - 0x4009  # the .P file starts at $4009 (standard .P layout)
    check("48K GLM image: CALL $0F2B at $40BE (BUG: SLOW call mid-instruction)",
          img[off:off + 3] == bytes([0xCD, 0x2B, 0x0F]))


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    rom = open(argv[1], "rb").read()
    model = open(argv[2], "rb").read()
    print(f"ROM {len(rom)} bytes, model {len(model)} bytes")
    check_rom(rom)
    check_tokens(rom)
    check_line2_fix()
    check_model(model, buffer_len=10240)
    if len(argv) > 3:
        check_old_image(open(argv[3], "rb").read())
    failed = [n for n, ok in results if not ok]
    # the bug-reproduction line is EXPECTED to FAIL; it is excluded from the count
    real_failed = [n for n in failed if "BUG REPRODUCTION" not in n]
    print(f"\n{len(results) - len(failed)}/{len(results)} checks as expected; "
          f"unexpected failures: {len(real_failed)}")
    return 0 if not real_failed else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
