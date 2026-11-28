/* rt_engine.c - int8 quantized forward pass + sampling.
 *
 * Quantization v2 (chosen by training/pack.py):
 *   - ALL activations are Q7 (real = v / 128); the bias lane input is
 *     the constant 128 (= 1.0), so biases quantize on the same grid as
 *     ordinary weights.
 *   - every weight row carries its own power-of-two shift s (u8 array):
 *     row values are round(w * 2^s), and the matmul does acc >> s.
 *   - hidden activations are ReLU'd and saturated into [0, 127];
 *     logits stay int32 in Q7 scale.
 */
#include "rt_engine.h"
#include "rt_lut.h"

static rt_i8  rt_x[RT_MAX_CTX * RT_MAX_EMB];
static rt_i8  rt_h1[RT_MAX_HID];
static rt_i8  rt_h2[RT_MAX_HID];
static rt_i8 *rt_hlast;
static int    rt_hlast_n;

static void matmul_hid(const rt_i8 *w, const rt_u8 *sh, const rt_i8 *x,
                       int n_in, int n_out, rt_i8 *y)
{
    int o, i;
    for (o = 0; o < n_out; o++) {
        const rt_i8 *wr = w + (long)o * (n_in + 1);
        rt_i32 acc = 0;
        for (i = 0; i < n_in; i++)
            acc += (rt_i32)x[i] * (rt_i32)wr[i];
        acc += (rt_i32)128 * wr[n_in]; /* bias lane: Q7 one */
        acc >>= sh[o];
        if (acc < 0)
            acc = 0;    /* ReLU */
        if (acc > 127)
            acc = 127;  /* saturate to int8 */
        y[o] = (rt_i8)acc;
    }
}

static void matmul_logits(const rt_i8 *w, const rt_u8 *sh, const rt_i8 *x,
                          int n_in, int n_out, rt_i32 *lg)
{
    int o, i;
    for (o = 0; o < n_out; o++) {
        const rt_i8 *wr = w + (long)o * (n_in + 1);
        rt_i32 acc = 0;
        for (i = 0; i < n_in; i++)
            acc += (rt_i32)x[i] * (rt_i32)wr[i];
        acc += (rt_i32)128 * wr[n_in];
        lg[o] = acc >> sh[o];
    }
}

void rt_forward(const rt_model *m, const rt_u8 *ctx, rt_i32 *logits)
{
    int i, j;
    int n_in = (int)m->hdr.ctx * (int)m->hdr.emb;

    for (i = 0; i < (int)m->hdr.ctx; i++) {
        const rt_i8 *e = m->emb + (long)ctx[i] * m->hdr.emb;
        for (j = 0; j < (int)m->hdr.emb; j++)
            rt_x[i * (int)m->hdr.emb + j] = e[j];
    }

    matmul_hid(m->w1, m->sh1, rt_x, n_in, m->hdr.h1, rt_h1);
    if (m->hdr.h2) {
        matmul_hid(m->w2, m->sh2, rt_h1, m->hdr.h1, m->hdr.h2, rt_h2);
        rt_hlast = rt_h2;
        rt_hlast_n = m->hdr.h2;
    } else {
        rt_hlast = rt_h1;
        rt_hlast_n = m->hdr.h1;
    }
    matmul_logits(m->wo, m->sho, rt_hlast, rt_hlast_n, m->hdr.vocab,
                  logits);
}

void rt_last_hidden(const rt_i8 **h, int *n)
{
    *h = rt_hlast;
    *n = rt_hlast_n;
}

rt_u32 rt_rand(rt_u32 *seed)
{
    rt_u32 x = *seed;
    x = (x ^ ((x << 13) & RT_U32_MASK)) & RT_U32_MASK;
    x = (x ^ (x >> 17)) & RT_U32_MASK;
    x = (x ^ ((x << 5) & RT_U32_MASK)) & RT_U32_MASK;
    *seed = x;
    return x;
}

int rt_sample(const rt_model *m, const rt_i32 *lg, int temp_sh, int greedy,
              rt_u32 *seed)
{
    int i, best = 0;
    rt_i32 mx = lg[0];
    rt_u16 w[RT_MAX_VOCAB];
    rt_u32 sum = 0, r, acc = 0;

    for (i = 1; i < (int)m->hdr.vocab; i++)
        if (lg[i] > mx) {
            mx = lg[i];
            best = i;
        }
    if (greedy)
        return best;

    for (i = 0; i < (int)m->hdr.vocab; i++) {
        rt_i32 d = (mx - lg[i]) >> temp_sh; /* >= 0 */
        int k = (int)(d >> 3);
        if (k > 255)
            k = 255;
        w[i] = RT_EXP_LUT[k];
        sum += w[i];
    }
    if (sum == 0)
        return best;

    r = rt_rand(seed) % sum;
    for (i = 0; i < (int)m->hdr.vocab; i++) {
        acc += w[i];
        if (r < acc)
            return i;
    }
    return best;
}
