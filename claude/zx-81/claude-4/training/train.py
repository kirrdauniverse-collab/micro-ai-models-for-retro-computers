#!/usr/bin/env python3
"""Tiny char-level MLP language model trainer (numpy only, CPU friendly).

Architecture (Bengio-style NPLM, fully int8-deployable):
    one-hot(ctx) -> emb[vocab][emb]  (shared lookup, concatenated)
    -> h1 = relu(x @ W1.T + b1)
    [-> h2 = relu(h1 @ W2.T + b2)]
    -> logits = h_last @ Wo.T + bo

Biases are folded into each weight matrix as an extra input lane of 1.0
(the C engine feeds the constant 127 = Q7 one; pack.py compensates).

Presets (see README "Model classes"):
    A  Amiga 500     ctx 12 emb 48 h1 448 h2 192  ~356k params
    B  64KB machines ctx 10 emb 32 h1 160 h2  96   ~73k params
    C  C64 / ZX 48K  ctx 10 emb 24 h1  96 h2   0   ~29k params
    D  ZX81 16K      ctx  8 emb 16 h1  40 h2   0   ~7.7k params

Usage:
    python3 training/train.py --class C --data training/data/base.txt \
        --out runs/base_c --steps 4000
"""
import argparse
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from rtcharset import CHARSET, IDX, encode, decode

V = len(CHARSET)

PRESETS = {
    "A": dict(ctx=12, emb=48, h1=448, h2=192),
    "B": dict(ctx=10, emb=32, h1=160, h2=96),
    "C": dict(ctx=10, emb=24, h1=96, h2=0),
    "D": dict(ctx=8, emb=16, h1=40, h2=0),
    # 16K ZX81 edition: engine + model + display file share one 16K pack;
    # ~4.0k params, 4156-byte blob (see docs/T81_FORMAT.md "16K edition")
    "E": dict(ctx=8, emb=12, h1=24, h2=0),
    # 16K ZX81 final fit (v0.4): the sccz80 engine core is ~11 KB, so the
    # model must stay under ~2.7 KB; 2165 params, 2666-byte blob
    "F": dict(ctx=8, emb=10, h1=16, h2=0),
}


class MLP:
    def __init__(self, ctx, emb, h1, h2, seed=1234):
        rng = np.random.default_rng(seed)
        self.ctx, self.emb, self.h1, self.h2 = ctx, emb, h1, h2
        self.E = (rng.standard_normal((V, emb)) * 0.4).astype(np.float32)
        in1 = ctx * emb + 1
        self.W1 = (rng.standard_normal((h1, in1)) * (1.0 / in1 ** 0.5)).astype(np.float32)
        if h2:
            in2 = h1 + 1
            self.W2 = (rng.standard_normal((h2, in2)) * (1.0 / in2 ** 0.5)).astype(np.float32)
        else:
            self.W2 = None
        out_in = (h2 or h1) + 1
        self.Wo = (rng.standard_normal((V, out_in)) * (1.0 / out_in ** 0.5)).astype(np.float32)

    def params(self):
        n = self.E.size + self.W1.size + self.Wo.size
        if self.W2 is not None:
            n += self.W2.size
        return n

    def forward(self, idx):
        """idx: (B, ctx) int array -> logits (B, V)."""
        B = idx.shape[0]
        x = self.E[idx].reshape(B, -1)                     # (B, ctx*emb)
        one = np.ones((B, 1), dtype=np.float32)
        h = np.maximum(np.hstack([x, one]) @ self.W1.T, 0) # (B, h1)
        if self.W2 is not None:
            h = np.maximum(np.hstack([h, one]) @ self.W2.T, 0)
        return np.hstack([h, one]) @ self.Wo.T             # (B, V)

    def loss(self, logits, target):
        z = logits - logits.max(axis=1, keepdims=True)
        p = np.exp(z)
        p /= p.sum(axis=1, keepdims=True)
        return -np.log(np.maximum(p[np.arange(len(target)), target], 1e-9)).mean()


class Adam:
    def __init__(self, model, lr):
        self.lr = lr
        self.m = {k: np.zeros_like(v) for k, v in vars(model).items()
                  if isinstance(v, np.ndarray)}
        self.v = {k: np.zeros_like(vv) for k, vv in self.m.items()}

    def step(self, model, grads):
        b1, b2, eps = 0.9, 0.999, 1e-8
        t = self.t = getattr(self, "t", 0) + 1
        for k, g in grads.items():
            self.m[k] = b1 * self.m[k] + (1 - b1) * g
            self.v[k] = b2 * self.v[k] + (1 - b2) * g * g
            mh = self.m[k] / (1 - b1 ** t)
            vh = self.v[k] / (1 - b2 ** t)
            setattr(model, k, vars(model)[k] - self.lr * mh / (np.sqrt(vh) + eps))


def backprop(model, idx, target):
    """Manual gradients for the 3-matrix MLP. Returns (loss, grads)."""
    B = idx.shape[0]
    x = model.E[idx].reshape(B, -1)
    one = np.ones((B, 1), dtype=np.float32)
    x1 = np.hstack([x, one])
    z1 = x1 @ model.W1.T
    h1 = np.maximum(z1, 0)
    if model.W2 is not None:
        h1b = np.hstack([h1, one])
        z2 = h1b @ model.W2.T
        h2 = np.maximum(z2, 0)
        hb = np.hstack([h2, one])
    else:
        hb = np.hstack([h1, one])
    logits = hb @ model.Wo.T

    z = logits - logits.max(axis=1, keepdims=True)
    ez = np.exp(z)
    p = ez / ez.sum(axis=1, keepdims=True)
    loss = -np.log(np.maximum(p[np.arange(B), target], 1e-9)).mean()

    dlog = p.copy()
    dlog[np.arange(B), target] -= 1.0
    dlog /= B

    grads = {}
    grads["Wo"] = dlog.T @ hb
    dhb = dlog @ model.Wo
    if model.W2 is not None:
        dh2 = dhb[:, :-1] * (z2 > 0)
        grads["W2"] = dh2.T @ h1b
        dh1b = dh2 @ model.W2
        dh1 = dh1b[:, :-1] * (z1 > 0)
    else:
        dh1 = dhb[:, :-1] * (z1 > 0)
    grads["W1"] = dh1.T @ x1
    dx1 = dh1 @ model.W1
    gE = np.zeros_like(model.E)
    dx = dx1[:, :-1].reshape(B, model.ctx, model.emb)
    np.add.at(gE, idx, dx)
    grads["E"] = gE
    return loss, grads


def load_data(path):
    with open(path) as f:
        raw = f.read()
    return np.array(encode(raw), dtype=np.int64)


def sample_batch(data, ctx, B, rng):
    pos = rng.integers(0, len(data) - ctx - 1, size=B)
    idx = np.stack([data[p:p + ctx] for p in pos])
    tgt = data[pos + ctx]
    return idx, tgt


def preview(model, prompt, n=40):
    ids = encode(prompt)[-model.ctx:]
    ids = [IDX[" "]] * (model.ctx - len(ids)) + ids
    out = []
    for _ in range(n):
        logits = model.forward(np.array([ids], dtype=np.int64))
        nxt = int(np.argmax(logits[0]))
        if nxt == IDX["\n"]:
            break
        out.append(nxt)
        ids = ids[1:] + [nxt]
    return decode(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--class", dest="cls", default="C", choices=PRESETS)
    ap.add_argument("--data", default="training/data/base.txt")
    ap.add_argument("--val", default="training/data/val.txt")
    ap.add_argument("--out", required=True)
    ap.add_argument("--steps", type=int, default=4000)
    ap.add_argument("--batch", type=int, default=128)
    ap.add_argument("--lr", type=float, default=3e-3)
    ap.add_argument("--seed", type=int, default=1234)
    args = ap.parse_args()

    cfg = PRESETS[args.cls]
    model = MLP(seed=args.seed, **cfg)
    print(f"class {args.cls}: ctx={cfg['ctx']} emb={cfg['emb']} "
          f"h1={cfg['h1']} h2={cfg['h2']} params={model.params()}")

    data = load_data(args.data)
    val = load_data(args.val) if os.path.exists(args.val) else None
    rng = np.random.default_rng(args.seed + 1)
    opt = Adam(model, args.lr)

    t0 = time.time()
    for step in range(1, args.steps + 1):
        idx, tgt = sample_batch(data, model.ctx, args.batch, rng)
        loss, grads = backprop(model, idx, tgt)
        opt.step(model, grads)
        if step % 200 == 0 or step == 1:
            msg = f"step {step:5d} loss {loss:.4f}"
            if val is not None:
                vi, vt = sample_batch(val, model.ctx, 512, rng)
                msg += f" val {model.loss(model.forward(vi), vt):.4f}"
            msg += f" [{time.time()-t0:.0f}s]"
            print(msg, flush=True)
        if step % 1000 == 0:
            print("  preview:", preview(model, "hello! how are"), flush=True)

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    np.savez_compressed(
        args.out + ".npz",
        E=model.E, W1=model.W1, W2=model.W2 if model.W2 is not None
        else np.zeros((1, 1), dtype=np.float32),
        Wo=model.Wo,
    )
    meta = dict(cls=args.cls, **cfg, params=int(model.params()),
                steps=args.steps, final_loss=float(loss), seed=args.seed)
    with open(args.out + ".json", "w") as f:
        json.dump(meta, f, indent=1)
    print("saved", args.out + ".npz")
    print("final preview:", preview(model, "hello! how are"))


if __name__ == "__main__":
    main()
