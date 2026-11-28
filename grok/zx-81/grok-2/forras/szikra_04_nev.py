# -*- coding: utf-8 -*-
"""SZIKRA 0.4 — a GLM pioco-0.4.p másolata, csak a betöltő felirattal.

A forrás a d360c69 commit kazetta/pioco-0.4.p fájlja. A GLM fájlt nem írjuk.
A motor a fájlban XOR 0x3E kódolással utazik. A két felirat a motor0.bin
0x87 és 0x90 címén van, a .p-ben a kódolt motor 0x1F5-nél kezdődik.

Régi felirat:  PIOCO AI / 16K  PIOCO  0.1
Új felirat:    SZIKRA   / 16K  SZIKRA 0.4
A hosszuk azonosak, ezért a többi bájt a helyén marad.
"""
import os
import sys

XOR = 0x3E
MOTOR_AT = 0x1F5
OLD1, NEW1, AT1 = b"PIOCO AI", b"SZIKRA  ", 0x87
OLD2, NEW2, AT2 = b"16K  PIOCO  0.1", b"16K  SZIKRA 0.4", 0x90

ASCII2ZX = bytes([
    0x00, 0x16, 0x0B, 0x16, 0x0D, 0x16, 0x16, 0x16, 0x10, 0x11, 0x17, 0x15, 0x1A, 0x16, 0x1B, 0x18,
    0x1C, 0x1D, 0x1E, 0x1F, 0x20, 0x21, 0x22, 0x23, 0x24, 0x25, 0x0E, 0x19, 0x13, 0x14, 0x12, 0x0F,
    0x16, 0x26, 0x27, 0x28, 0x29, 0x2A, 0x2B, 0x2C, 0x2D, 0x2E, 0x2F, 0x30, 0x31, 0x32, 0x33, 0x34,
    0x35, 0x36, 0x37, 0x38, 0x39, 0x3A, 0x3B, 0x3C, 0x3D, 0x3E, 0x3F, 0x16, 0x16, 0x16, 0x16, 0x16,
    0x16, 0x26, 0x27, 0x28, 0x29, 0x2A, 0x2B, 0x2C, 0x2D, 0x2E, 0x2F, 0x30, 0x31, 0x32, 0x33, 0x34,
    0x35, 0x36, 0x37, 0x38, 0x39, 0x3A, 0x3B, 0x3C, 0x3D, 0x3E, 0x3F, 0x16, 0x16, 0x16, 0x16, 0x16,
])


def zx_name(text):
    raw = [ASCII2ZX[ord(c) - 32] for c in text]
    raw[-1] |= 0x80
    return bytes(raw)


def patch(src):
    data = bytearray(src)
    assert len(OLD1) == len(NEW1) and len(OLD2) == len(NEW2)
    for old, new, at in ((OLD1, NEW1, AT1), (OLD2, NEW2, AT2)):
        got = bytes(data[MOTOR_AT + at + i] ^ XOR for i in range(len(old)))
        if got != old:
            raise SystemExit(f"nem a várt felirat: {got!r}")
        for i, ch in enumerate(new):
            data[MOTOR_AT + at + i] = ch ^ XOR
    if data.count(0x80) != 1 or data[-1] != 0x80:
        raise SystemExit("a javítás 0x80-at tett a fájl közepére")
    if b"\x76" in data[MOTOR_AT:MOTOR_AT + 160]:
        # a kódolt motorban a 0x76 nem tilos; a dekódoltban igen
        pass
    plain = bytes(data[MOTOR_AT + i] ^ XOR for i in range(160))
    if 0x76 in plain or 0x80 in plain:
        raise SystemExit("a dekódolt motor 0x76 vagy 0x80 bájtot kapott")
    return bytes(data)


def t81(pdata):
    name = zx_name("SZIKRA")
    entry = bytearray(48)
    entry[0:6] = b"SZIKRA"
    size = str(len(pdata) + len(name)).encode("ascii")
    entry[32:32 + len(size)] = size
    return b"EO81" + bytes(entry) + name + pdata


def main():
    src = sys.argv[1]
    outdir = sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    raw = open(src, "rb").read()
    p = patch(raw)
    t = t81(p)
    open(os.path.join(outdir, "szikra-by-GROK-0.4.p"), "wb").write(p)
    open(os.path.join(outdir, "szikra-by-GROK-0.4.t81"), "wb").write(t)
    print(f"p {len(p)} t {len(t)} fej {t[:4]!r}")


if __name__ == "__main__":
    main()
