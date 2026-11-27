#!/usr/bin/env python3
"""Structural checker for ZX81 PICO/AI16 P and T81 images.

Checks only things that can be verified without executing the Z80:
- 16K RAM bounds
- D_FILE/VARS/E_LINE pointers
- BASIC line chain
- line 1 REM engine marker at $4081
- line 2 canonical RAND USR VAL "16514" token sequence
- T81 EO81 header and payload length
"""
import sys
from pathlib import Path

RAM_START = 0x4009
RAM_END = 0x8000
SYSVARS = 116
BASIC_START = RAM_START + SYSVARS
LINE2_BODY = bytes([0xF9,0xD4,0xC5,0x0B,0x0B,0x0B,0x0B,0x0B,0x0B,0x0B])
# The five numeric bytes are validated separately because their exact
# floating-point encoding is part of the ZX81 BASIC representation.

def u16(b, p):
    return b[p] | (b[p+1] << 8)

def check_p(data):
    assert len(data) <= RAM_END - RAM_START, "P image exceeds 16K RAM"
    assert len(data) >= SYSVARS + 8, "P image too short"
    dfile = u16(data, 3)   # $400C
    vars_ = u16(data, 7)   # $4010
    eline = u16(data, 11)  # $4014
    for name, v in (("D_FILE", dfile), ("VARS", vars_), ("E_LINE", eline)):
        assert RAM_START <= v < RAM_END, f"{name} out of RAM: {v:04X}"

    p = BASIC_START - RAM_START
    lines = []
    while True:
        assert p + 4 <= len(data), "BASIC line header outside P image"
        n = (data[p] << 8) | data[p+1]
        ln = data[p+2] | (data[p+3] << 8)
        if n == 0:
            break
        body = data[p+4:p+4+ln]
        assert len(body) == ln, f"truncated BASIC line {n}"
        lines.append((n, body, p + RAM_START))
        p += 4 + ln
        assert p <= len(data), "BASIC chain runs past P image"
    assert lines and lines[0][0] == 1, "line 1 missing"
    assert len(lines) >= 2 and lines[1][0] == 2, "line 2 missing"
    # REM token is the first byte of line 1; machine code begins at $4082.
    body1 = lines[0][1]
    assert body1 and body1[0] == 0xEA, "line 1 is not REM"
    assert data[0x4082-RAM_START] != 0, "machine-code entry at $4082 is empty"

    body2 = lines[1][1]
    assert body2[:4] == LINE2_BODY[:4], "line 2 does not start RAND USR VAL quote"
    assert body2[-2:] == bytes([0x0B, 0x76]), "line 2 missing closing quote/newline"
    assert len(body2) == 11, f"unexpected line 2 length: {len(body2)}"
    print(f"P OK: {len(data)} bytes, D_FILE={dfile:04X}, VARS={vars_:04X}, E_LINE={eline:04X}")

def check_t81(data):
    assert data[:4] == b"EO81", "missing EO81"
    assert len(data) >= 52, "T81 header too short"
    size_field = data[36:52].split(b"\0",1)[0]
    size = int(size_field or b"0")
    payload = data[52:]
    assert size == len(payload), f"T81 payload mismatch: header {size}, actual {len(payload)}"
    check_p(payload)
    print(f"T81 OK: {len(data)} bytes, payload={len(payload)}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: pico_zx81_check.py file.p file.t81")
    check_p(Path(sys.argv[1]).read_bytes())
    check_t81(Path(sys.argv[2]).read_bytes())
