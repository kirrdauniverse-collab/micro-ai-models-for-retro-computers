/* rt_finetune.c - on-device output-layer fine-tuning (int8 SGD).
 *
 * One sweep = one pass over the text. For every character position we run
 * a normal forward pass and accumulate the softmax error into an int32
 * gradient buffer g[t][j] += (-err[t]) * h[j] (gradient DESCENT:
 * dL/dw[t][j] = err[t] * h[j]). After the sweep every output weight moves
 * by g >> lr_sh, clamped to +-127. Accumulating first keeps the int8
 * rounding error from drowning the signal: per-position updates would
 * mostly round to 0 and occasionally jump by +-3.
 *
 * The bias lane accumulates (-err[t]) * 128, the same constant inference
 * feeds, so what is learned here is exactly what inference reads back.
 */
#include "rt_finetune.h"

#if RT_ENABLE_FINETUNE

#include "rt_engine.h"
#include "rt_charset.h"
#include "rt_lut.h"

static rt_i32 ft_logits[RT_MAX_VOCAB];
static rt_u16 ft_w[RT_MAX_VOCAB];
static rt_i32 ft_g[RT_MAX_VOCAB][RT_MAX_HID + 1];

static void probs_q12(const rt_model *m, rt_u32 *sum_out)
{
    int i;
    rt_i32 mx = ft_logits[0];
    rt_u32 sum = 0;
    for (i = 1; i < (int)m->hdr.vocab; i++)
        if (ft_logits[i] > mx)
            mx = ft_logits[i];
    for (i = 0; i < (int)m->hdr.vocab; i++) {
        rt_i32 d = mx - ft_logits[i];
        int k = (int)(d >> 3);
        if (k > 255)
            k = 255;
        ft_w[i] = RT_EXP_LUT[k];
        sum += ft_w[i];
    }
    *sum_out = sum;
}

int rt_finetune_text(rt_model *m, const char *text, int steps, int lr_sh)
{
    rt_u8 idx[514];
    int n = 0, s, i, t, j, hits = 0, last;
    rt_u8 win[RT_MAX_CTX];

    while (text[n] && n < 512)
        idx[n] = rt_map_char(text[n]), n++;
    if (n < 2)
        return 0;
    idx[n] = 0; /* terminating newline is also a prediction target */

    for (s = 0; s < steps; s++) {
        int hn = 0;
        hits = 0;

        for (t = 0; t < (int)m->hdr.vocab; t++)
            for (j = 0; j <= RT_MAX_HID; j++)
                ft_g[t][j] = 0;

        for (last = 1; last <= n; last++) {
            const rt_i8 *h;
            int target = idx[last];
            rt_u32 sum;
            int err[RT_MAX_VOCAB];
            int ctx = (int)m->hdr.ctx;

            /* window ending at idx[last-1], left-padded with spaces */
            for (i = 0; i < ctx; i++) {
                int pos = last - ctx + i;
                win[i] = (pos < 0) ? (rt_u8)1 : idx[pos];
            }

            rt_forward(m, win, ft_logits);
            rt_last_hidden(&h, &hn);
            probs_q12(m, &sum);
            if (sum == 0)
                continue;

            for (t = 0; t < (int)m->hdr.vocab; t++) {
                int p = (int)((rt_u32)ft_w[t] * 4096UL / sum);
                err[t] = -(p - (t == target ? 4096 : 0));
            }

            { /* argmax check before any update */
                int best = 0;
                for (t = 1; t < (int)m->hdr.vocab; t++)
                    if (ft_logits[t] > ft_logits[best])
                        best = t;
                if (best == target)
                    hits++;
            }

            for (t = 0; t < (int)m->hdr.vocab; t++) {
                int e = err[t];
                if (e == 0)
                    continue;
                for (j = 0; j < hn; j++)
                    ft_g[t][j] += (rt_i32)e * (rt_i32)h[j];
                ft_g[t][hn] += (rt_i32)e * 128;
            }
        }

        /* apply the accumulated gradient once per sweep */
        for (t = 0; t < (int)m->hdr.vocab; t++) {
            rt_i8 *row = m->wo + (long)t * (hn + 1);
            for (j = 0; j <= hn; j++) {
                int dw = (int)(ft_g[t][j] >> lr_sh);
                int v = row[j] + dw;
                if (v > 127) v = 127;
                if (v < -127) v = -127;
                row[j] = (rt_i8)v;
            }
        }
    }
    return hits;
}

#endif /* RT_ENABLE_FINETUNE */
