#!/usr/bin/env python3
"""Pack a trained .npz into an int8 model.bin + golden test vectors.

Also reports float-vs-int8 next-character agreement (argmax match on a
validation sample) and writes golden.txt consumed by tests/test_golden.c:
every line is "ctx-ids|argmax|argmax-logit|sampled-index".

Usage:
    python3 training/pack.py --npz runs/base_c.npz --bin models/base_c.bin \
        --golden tests/golden_c.txt --val training/data/val.txt
"""
import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from rtcharset import CHARSET, IDX, encode
from train import MLP, PRESETS
import intsim


def build_blob(im):
    """IntModel -> (bytes, header dict), model.bin v2 layout."""
    h = dict(version=2, flags=im.flags, vocab=len(CHARSET), ctx=im.ctx,
             emb=im.emb, h1=im.h1, h2=im.h2, sh_e=7, sh1=0, sh2=0, sh_o=0,
             temp_sh=im.temp_sh)
    hdr = bytearray()
    hdr += b"RTLM"
    for k in ("version", "flags", "vocab", "ctx", "emb", "h1", "h2",
              "sh_e", "sh1", "sh2", "sh_o", "temp_sh"):
        hdr += int(h[k]).to_bytes(2, "little")
    cs = CHARSET.encode("ascii")
    hdr += cs + b"\x00" * (64 - len(cs))
    assert len(hdr) == 92, len(hdr)

    body = bytearray()
    body += im.E.astype(np.int8).tobytes()
    body += im.sh1.astype(np.uint8).tobytes()
    body += im.W1.astype(np.int8).tobytes()
    if im.h2:
        body += im.sh2.astype(np.uint8).tobytes()
        body += im.W2.astype(np.int8).tobytes()
    body += im.sho.astype(np.uint8).tobytes()
    body += im.Wo.astype(np.int8).tobytes()

    blob = bytes(hdr) + bytes(body)
    cksum = sum(blob) & 0xFFFF
    return blob + cksum.to_bytes(2, "little"), h


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--npz", required=True)
    ap.add_argument("--bin", required=True)
    ap.add_argument("--golden")
    ap.add_argument("--val", default="training/data/val.txt")
    ap.add_argument("--stats")
    ap.add_argument("--finetune-ok", action="store_true",
                    help="set the fine-tune-allowed header flag")
    args = ap.parse_args()

    d = np.load(args.npz)
    W2 = d["W2"] if d["W2"].shape != (1, 1) else None
    # rebuild a float model from the npz
    m = MLP.__new__(MLP)
    m.E = d["E"].astype(np.float32)
    m.W1 = d["W1"].astype(np.float32)
    m.W2 = None if W2 is None else W2.astype(np.float32)
    m.Wo = d["Wo"].astype(np.float32)
    m.h1 = m.W1.shape[0]
    m.h2 = 0 if m.W2 is None else m.W2.shape[0]
    m.ctx = (m.W1.shape[1] - 1) // m.E.shape[1]
    m.emb = m.E.shape[1]

    # calibration + validation contexts
    if os.path.exists(args.val):
        with open(args.val) as f:
            val_ids = np.array(encode(f.read()), dtype=np.int64)
    else:
        val_ids = np.random.default_rng(7).integers(0, len(CHARSET), 200000)
    pos = np.arange(0, len(val_ids) - m.ctx - 1, m.ctx + 1)[:400]
    calib = np.stack([val_ids[p:p + m.ctx] for p in pos[:256]])
    ctx_rows = np.stack([val_ids[p:p + m.ctx] for p in pos])

    im = intsim.IntModel.from_float(m, temp_sh=2, calib=calib)
    if args.finetune_ok:
        im.flags = 1

    blob, h = build_blob(im)
    os.makedirs(os.path.dirname(args.bin) or ".", exist_ok=True)
    with open(args.bin, "wb") as f:
        f.write(blob)

    # float vs int8 agreement + perplexity-ish loss
    def float_logits(rows):
        B = len(rows)
        x = m.E[rows].reshape(B, -1)
        one = np.ones((B, 1), dtype=np.float32)
        hh = np.maximum(np.hstack([x, one]) @ m.W1.T, 0)
        if m.W2 is not None:
            hh = np.maximum(np.hstack([hh, one]) @ m.W2.T, 0)
        return np.hstack([hh, one]) @ m.Wo.T

    tgt = val_ids[pos + m.ctx]
    fl = float_logits(ctx_rows)
    il = im.forward(ctx_rows)
    agree = float((fl.argmax(1) == il.argmax(1)).mean())
    flp = fl - fl.max(1, keepdims=True)
    flp = np.exp(flp); flp /= flp.sum(1, keepdims=True)
    fl_loss = -np.log(np.maximum(flp[np.arange(len(tgt)), tgt], 1e-9)).mean()
    ilp = il - il.max(1, keepdims=True)
    ilp = np.exp(ilp.astype(np.float64)); ilp /= ilp.sum(1, keepdims=True)
    int_loss = -np.log(np.maximum(ilp[np.arange(len(tgt)), tgt], 1e-9)).mean()

    nparams = int(m.E.size + m.W1.size + m.Wo.size +
                  (0 if m.W2 is None else m.W2.size))
    stats = dict(cls_dims=dict(ctx=m.ctx, emb=m.emb, h1=m.h1, h2=m.h2),
                 params=nparams, bin_bytes=len(blob),
                 agreement=agree, float_loss=float(fl_loss),
                 int_loss=float(int_loss))
    print(json.dumps(stats, indent=1))
    if args.stats:
        with open(args.stats, "w") as f:
            json.dump(stats, f, indent=1)

    # golden vectors: fixed contexts, greedy argmax + one sampled char
    if args.golden:
        rng = np.random.default_rng(99)
        rows = rng.integers(0, len(CHARSET), size=(100, m.ctx))
        with open(args.golden, "w") as f:
            for r in rows:
                lg = im.forward(r[None, :])[0]
                am = int(np.argmax(lg))
                seed = 1234
                samp, seed = im.sample(lg, 2, 0, seed)
                f.write(" ".join(str(int(x)) for x in r) + "|" +
                        str(am) + "|" + str(int(lg[am])) + "|" + str(samp) + "\n")
        print("golden:", args.golden)


if __name__ == "__main__":
    main()
