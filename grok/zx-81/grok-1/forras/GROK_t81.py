# -*- coding: utf-8 -*-
"""GROK — pioco-by-GROK-0.1 kazetta.

A 2026-11-24-i munkamenet forrása. A sandbox később törlődött,
ez a fájl a GitHubra akkor nem került fel. A bájtokat ez a program
újra előállítja. Nem a GLM fájljait írja.

- kazettak/pioco-by-GROK-0.1.p
- kazettak/pioco-by-GROK-0.1.t81

A 0.1 még nem beszél. A 16514 címen JR $ áll (18 FE).
Nincs adat a BASIC program mögött.

A .t81 az EightyOne borítéka (leiradel/tape2wav etc/t81.cpp):
4 bájt EO81, 48 bájtos bejegyzés, ZX81 kódolású név, nyers .p.
"""
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTDIR = os.path.join(BASE, "kazettak")
VERSION = "0.1"
P_NAME = f"pioco-by-GROK-{VERSION}.p"
T_NAME = f"pioco-by-GROK-{VERSION}.t81"

ASCII2ZX = bytes([
    0x00, 0x16, 0x0B, 0x16, 0x0D, 0x16, 0x16, 0x16, 0x10, 0x11, 0x17, 0x15, 0x1A, 0x16, 0x1B, 0x18,
    0x1C, 0x1D, 0x1E, 0x1F, 0x20, 0x21, 0x22, 0x23, 0x24, 0x25, 0x0E, 0x19, 0x13, 0x14, 0x12, 0x0F,
    0x16, 0x26, 0x27, 0x28, 0x29, 0x2A, 0x2B, 0x2C, 0x2D, 0x2E, 0x2F, 0x30, 0x31, 0x32, 0x33, 0x34,
    0x35, 0x36, 0x37, 0x38, 0x39, 0x3A, 0x3B, 0x3C, 0x3D, 0x3E, 0x3F, 0x16, 0x16, 0x16, 0x16, 0x16,
    0x16, 0x26, 0x27, 0x28, 0x29, 0x2A, 0x2B, 0x2C, 0x2D, 0x2E, 0x2F, 0x30, 0x31, 0x32, 0x33, 0x34,
    0x35, 0x36, 0x37, 0x38, 0x39, 0x3A, 0x3B, 0x3C, 0x3D, 0x3E, 0x3F, 0x16, 0x16, 0x16, 0x16, 0x16,
])

USR = bytes([0xF9, 0xD4, 0x1D, 0x22, 0x21, 0x1D, 0x20, 0x7E, 0x8F, 0x01, 0x04, 0x00, 0x00])


def line(n, body):
    ln = len(body) + 1
    return bytes([(n >> 8) & 0xFF, n & 0xFF, ln & 0xFF, (ln >> 8) & 0xFF]) + body + b"\x76"


def build_p():
    prog = line(1, bytes([0xEA, 0x18, 0xFE])) + line(2, USR)
    assert prog[5:7] == b"\x18\xFE"
    d_file = 0x407D + len(prog)
    screen = b"\x76" * 25
    hd = bytearray(0x74)
    def hw(at, v):
        hd[at] = v & 0xFF
        hd[at + 1] = (v >> 8) & 0xFF
    hw(3, d_file)
    hw(5, d_file + 1)
    hw(7, d_file + 25)
    hw(11, d_file + 26)
    hw(13, d_file + 25)
    hw(17, d_file + 26)
    hw(19, d_file + 26)
    hw(22, 0x405D)
    hd[25] = 2
    hw(26, 1)
    hd[28] = 0xFF
    hw(29, 0xFFFF)
    hd[31] = 55
    hw(32, 0x4085)
    hw(39, 0x0C8D)
    hw(43, 0xFFFF)
    hd[47] = 0xBC
    hd[48], hd[49] = 33, 24
    hd[50] = 0x40
    out = bytes(hd) + prog + screen + b"\x80"
    assert out[-1] == 0x80 and out[:-1].count(0x80) == 0
    return out


def zx_name(text):
    raw = []
    for ch in text.upper():
        o = ord(ch)
        raw.append(ASCII2ZX[o - 32] if 32 <= o <= 127 else 0x16)
    raw[-1] |= 0x80
    return bytes(raw)


def build_t81(pdata):
    name = zx_name("PIOCO")
    entry = bytearray(48)
    entry[0:5] = b"PIOCO"
    size = str(len(pdata) + len(name)).encode("ascii")
    entry[32:32 + len(size)] = size
    return b"EO81" + bytes(entry) + name + pdata


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    p = build_p()
    t = build_t81(p)
    open(os.path.join(OUTDIR, P_NAME), "wb").write(p)
    open(os.path.join(OUTDIR, T_NAME), "wb").write(t)
    assert t[:4] == b"EO81"
    print(f"{P_NAME} {len(p)} B")
    print(f"{T_NAME} {len(t)} B")


if __name__ == "__main__":
    main()
