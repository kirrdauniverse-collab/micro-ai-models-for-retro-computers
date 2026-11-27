#!/usr/bin/env python3
"""memmerge.py - merge a saved RTMEM16 memory block into the cassette.

The flow on the emulator:
  1. in the chat: /memsave  (the motor pulses out the raw RTMEM16 block)
  2. in EightyOne: record the tape output to a file (the emulator's
     tape window saves the recorded block)
  3. here: python3 memmerge.py <cassette.T81> <recorded-file> [out.T81]
     - finds the RTMEM16 block in the recorded file (EO81 container OR
       raw [name-codes][152 bytes][0x80] form)
     - validates the zone checksum
     - rewrites the cassette's RTMEM16 block with the saved zone

The next boot then offers "restore saved memory from tape? (y/n)" and
the boot's motor-side loader reads exactly this block.
"""
import sys

NAME = b"RTMEM16"
NAMECODES = bytes([0x37, 0x39, 0x32, 0x2A, 0x32, 0x1D]) + bytes([0x1C + 6 | 0x80])
ZONE_LEN = 152


def parse_eo81(raw):
    """EO81 container -> [(name, data)] or None if no magic."""
    if raw[:4] != b"EO81":
        return None
    blocks = []
    pos = 4
    while pos + 48 <= len(raw):
        name = raw[pos:pos + 32].rstrip(b"\0").decode(errors="replace")
        ln = int(raw[pos + 32:pos + 48].rstrip(b"\0") or 0)
        data = raw[pos + 48:pos + 48 + ln]
        blocks.append((name, data))
        pos += 48 + ln
    return blocks


def extract_zone(raw):
    """-> 152 zone bytes from a recorded block, or None."""
    blocks = parse_eo81(raw)
    if blocks:
        for name, data in blocks:
            if name.strip().upper() == NAME:
                raw = data
                break
        else:
            return None
    # raw form: [7 name codes][152 zone][0x80 tail]
    if len(raw) < 7 + ZONE_LEN:
        return None
    if raw[:7] != NAMECODES:
        # a ROM-style program image would start with 0x00/0x01/0xFF:
        # refuse anything that is not our raw form
        return None
    zone = raw[7:7 + ZONE_LEN]
    x = 0
    for b in zone[:-1]:
        x ^= b
    if x != zone[-1]:
        print("FIGYELEM: a zona XOR-ellenorzese NEM stimmel - "
              "a mentett adat sérülhetett (mégis beírom).")
    return bytes(zone)


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    cas = sys.argv[1]
    rec = sys.argv[2]
    out = sys.argv[3] if len(sys.argv) > 3 else cas

    raw = open(cas, "rb").read()
    zone = extract_zone(open(rec, "rb").read())
    if zone is None:
        print("HIBA: a recorded fajlban nincs ertelmezheto RTMEM16 blokk.")
        sys.exit(2)

    blocks = parse_eo81(raw)
    assert blocks, "a kazetta nem EO81 kontener"
    pos = 4
    outb = bytearray(raw)
    for name, data in blocks:
        if name.strip().upper() == NAME:
            start = pos + 48
            newdata = NAMECODES + zone + b"\x80"
            assert len(newdata) == len(data), \
                f"hossz eltér: {len(newdata)} != {len(data)}"
            outb[start:start + len(data)] = newdata
            print(f"RTMEM16 blokk frissitve: {len(zone)} B zona.")
            break
        pos += 48 + len(data)
    else:
        print("HIBA: a kazettaban nincs RTMEM16 blokk.")
        sys.exit(3)

    open(out, "wb").write(bytes(outb))
    print("kesz:", out)


if __name__ == "__main__":
    main()
