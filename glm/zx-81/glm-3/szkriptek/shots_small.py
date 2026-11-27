#!/usr/bin/env python3
"""shots_small.py — a feltöltött képernyőképek kicsinyített másolatai
(/home/z/my-project/GLM/tmp/shots/), hogy olvasáskor kevesebb kép-adat
kerüljön a nézetbe. A feltöltött eredetit nem módosítja.

Használat: python3 shots_small.py [max_szélesség=1400]
"""
import os
import sys

from PIL import Image

SRC = "/home/z/my-project/upload"
DST = "/home/z/my-project/GLM/tmp/shots"


def main():
    maxw = int(sys.argv[1]) if len(sys.argv) > 1 else 1400
    os.makedirs(DST, exist_ok=True)
    for fn in sorted(os.listdir(SRC)):
        if not fn.lower().endswith(".png"):
            continue
        im = Image.open(os.path.join(SRC, fn)).convert("RGB")
        w, h = im.size
        if w > maxw:
            im = im.resize((maxw, h * maxw // w), Image.LANCZOS)
        out = os.path.join(DST, os.path.splitext(fn)[0] + ".jpg")
        im.save(out, "JPEG", quality=80)
        print("%s: %dx%d -> %dx%d  %d B" % (fn, w, h, im.size[0], im.size[1],
                                            os.path.getsize(out)))


if __name__ == "__main__":
    main()
