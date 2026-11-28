#!/usr/bin/env python3
"""Shared charset definition - the single source of truth.

engine/rt_charset.c contains the same string; pack.py embeds it into every
model.bin and rt_model_load() rejects a model whose charset differs, so the
C and Python copies can never silently drift apart.
"""

CHARSET = "\n abcdefghijklmnopqrstuvwxyz,.?!'0123456789:-"
assert len(CHARSET) == 45, len(CHARSET)
assert len(set(CHARSET)) == 45

IDX = {c: i for i, c in enumerate(CHARSET)}
SPACE = IDX[" "]
NEWLINE = IDX["\n"]


def sanitize(text: str) -> str:
    """Fold to the model charset: lowercase A-Z, unknown chars -> space."""
    out = []
    for ch in text:
        if "A" <= ch <= "Z":
            ch = chr(ord(ch) + 32)
        out.append(ch if ch in IDX else " ")
    return "".join(out)


def encode(text: str):
    """Text -> list of charset indices (via sanitize)."""
    t = sanitize(text)
    return [IDX[c] for c in t]


def decode(indices):
    """Indices -> text."""
    return "".join(CHARSET[i] for i in indices)
