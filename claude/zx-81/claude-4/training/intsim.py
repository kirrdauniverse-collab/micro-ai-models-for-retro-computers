#!/usr/bin/env python3
"""Bit-exact integer simulator of the C engine (engine/rt_engine.c), v2.

Mirrors the C code exactly: Q7 activations everywhere, per-row power-of-two
weight shifts, bias lane input 128, ReLU+clip to [0,127], logits int32.
Integer arithmetic is exact, so numpy int64 accumulation == C long
accumulation for our ranges. pack.py uses it for calibration and golden
vectors; tests/test_golden.c then proves engine == simulator == trainer.
"""
import sys
import os

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from rtcharset import CHARSET, IDX

V = len(CHARSET)

EXP_LUT = np.array([int(round(np.exp(-k / 8.0) * 4096)) for k in range(256)],
                   dtype=np.uint32)


def q_shift(maxabs):
    """Power-of-two shift so max|w|*2^s fits in int8."""
    if maxabs <= 0:
        return 0
    s = int(np.floor(np.log2(127.0 / maxabs)))
    return max(0, min(31, s))


def quantize_rows(W):
    """Per-row quantization: (int8 q, u8 shifts) with q = round(w*2^s)."""
    q = np.zeros(W.shape, dtype=np.int8)
    sh = np.zeros(W.shape[0], dtype=np.uint8)
    for o in range(W.shape[0]):
        mx = float(np.abs(W[o]).max())
        s = q_shift(mx)
        sh[o] = s
        q[o] = np.clip(np.round(W[o] * (1 << s)), -128, 127)
    return q, sh


def xorshift32(x):
    x = np.uint32(x)
    x = np.uint32((x ^ np.uint32((x << np.uint32(13)) & 0xFFFFFFFF)))
    x = np.uint32((x ^ np.uint32(x >> np.uint32(17))))
    x = np.uint32((x ^ np.uint32((x << np.uint32(5)) & 0xFFFFFFFF)))
    return x


class IntModel:
    """Tensors exactly as model.bin v2 stores them."""

    def __init__(self, ctx, emb, h1, h2, E, sh1, W1, sh2, W2, sho, Wo,
                 temp_sh=2, flags=0):
        self.ctx, self.emb, self.h1, self.h2 = ctx, emb, h1, h2
        self.E, self.sh1, self.W1 = E, sh1, W1
        self.sh2, self.W2 = sh2, W2
        self.sho, self.Wo = sho, Wo
        self.temp_sh, self.flags = temp_sh, flags

    # ---- float -> int conversion (used by pack.py) ----
    @classmethod
    def from_float(cls, m, temp_sh=2, calib=None):
        """Quantize an MLP from train.py. calib: (N, ctx) charset indices
        used to calibrate per-row scales (real text contexts work best)."""
        if calib is None:
            calib = np.random.default_rng(0).integers(0, V, size=(256, m.ctx))

        # 1. embeddings -> Q7 (scaled so the max uses the int8 range)
        emax = float(np.abs(m.E).max())
        a_e = 0.99 / emax if emax > 0.99 else min(4.0, 0.99 / max(emax, 1e-4))
        E = np.clip(np.round(m.E * a_e * 128.0), -128, 127).astype(np.int8)

        X = E[calib].reshape(len(calib), -1)          # (N, ctx*emb) int8
        Xr = np.hstack([X.astype(np.float64) / 128.0,
                        np.ones((len(X), 1))])        # == [a_e * x, 1.0]

        # 2. layer 1. The embeddings already carry a_e, so the weights stay
        #    as they are; only the bias lane (input 1.0) needs pre-scaling
        #    by a_e, making the int pre-activation exactly a_e * z1. Then
        #    each row o is scaled by alpha_o so activations peak ~0.94
        #    (Q7 headroom); relu(a*z) = a*relu(z) keeps the function.
        W1e = m.W1.astype(np.float64).copy()
        W1e[:, -1] *= a_e
        acc_f = Xr @ W1e.T                            # == a_e * z1
        W1q, sh1, h1, alpha1 = cls._quant_hidden(W1e, acc_f, X)

        # 3. layer 2 (optional). Inputs are h1_int = Q7(alpha1 * a_e * h1):
        #    - weight column j divided by alpha1[j]
        #    - bias column multiplied by a_e
        #    so z2_int == a_e * z2 exactly; then row-alpha as above.
        if m.W2 is not None:
            W2e = m.W2.astype(np.float64).copy()
            W2e[:, :-1] = W2e[:, :-1] / alpha1[None, :]
            W2e[:, -1] = W2e[:, -1] * a_e
            h1r = np.hstack([h1.astype(np.float64) / 128.0,
                             np.ones((len(h1), 1))])
            acc2_f = h1r @ W2e.T                       # == a_e * z2
            W2q, sh2, h2, alpha2 = cls._quant_hidden(W2e, acc2_f, h1)
        else:
            W2q, sh2, h2, alpha2 = None, None, None, None

        # 4. output layer. Inputs are Q7(alpha * a_e * h_last); weight
        #    column j divided by (alpha_j * a_e), bias kept, so the int
        #    logits equal the float logits exactly (before rounding).
        Wo = m.Wo.astype(np.float64).copy()
        alpha_last = alpha2 if m.W2 is not None else alpha1
        Wo[:, :-1] = Wo[:, :-1] / (alpha_last[None, :] * a_e)
        Woq, sho = quantize_rows(Wo)
        hlast = h2 if m.W2 is not None else h1
        logits = cls._matmul(hlast, Woq, sho)

        return cls(m.ctx, m.emb, m.h1, m.h2, E, sh1, W1q, sh2, W2q, sho, Woq,
                   temp_sh)

    @staticmethod
    def _matmul(x_int, Wq, sh):
        """x_int: (N, n) int; Wq: (out, n+1); sh: (out,) -> (N, out)."""
        acc = x_int.astype(np.int64) @ Wq[:, :-1].T.astype(np.int64)
        acc += 128 * Wq[:, -1].astype(np.int64)[None, :]
        return acc >> sh.astype(np.int64)[None, :]

    @classmethod
    def _quant_hidden(cls, W, acc_f, x_int):
        """Scale rows so the calibration peak lands at ~0.94 real (120/128),
        then quantize per row. Returns (Wq, sh, h_int, alpha)."""
        rmax = np.maximum(acc_f.max(axis=0), 0.0)     # (out,)
        alpha = np.where(rmax > 0.94, 0.94 / np.maximum(rmax, 1e-9),
                         np.minimum(4.0, 0.94 / np.maximum(rmax, 1e-4)))
        alpha = np.where(rmax <= 0, 1.0, alpha)
        Wq, sh = quantize_rows(W * alpha[:, None])
        h = cls._matmul(x_int, Wq, sh)
        # safety: if more than 2% of activations clip at 127, soften once
        if (h == 127).mean() > 0.02:
            alpha = alpha * 0.8
            Wq, sh = quantize_rows(W * alpha[:, None])
            h = cls._matmul(x_int, Wq, sh)
        h = np.clip(h, 0, 127)
        return Wq, sh, h, alpha

    # ---- forward pass identical to rt_forward ----
    def forward(self, ctx_rows):
        """ctx_rows: (N, ctx) int -> logits (N, V) int64 (Q7 scale)."""
        x = self.E[ctx_rows].reshape(len(ctx_rows), -1).astype(np.int64)
        h1 = np.clip(self._matmul(x, self.W1, self.sh1), 0, 127)
        if self.h2:
            h2 = np.clip(self._matmul(h1, self.W2, self.sh2), 0, 127)
            hlast = h2
        else:
            hlast = h1
        return self._matmul(hlast, self.Wo, self.sho)

    # ---- sampling identical to rt_sample ----
    def sample(self, logits, temp_sh, greedy, seed):
        mx = int(logits.max())
        if greedy:
            return int(np.argmax(logits)), seed
        w = []
        total = 0
        for l in logits:
            d = (mx - int(l)) >> temp_sh
            k = min(int(d) >> 3, 255)
            wi = int(EXP_LUT[k])
            w.append(wi)
            total += wi
        if total == 0:
            return int(np.argmax(logits)), seed
        seed = int(xorshift32(seed))   # one advance, like rt_rand in C
        r = int(seed % total)
        acc = 0
        for i, wi in enumerate(w):
            acc += wi
            if r < acc:
                return i, seed
        return int(np.argmax(logits)), seed
