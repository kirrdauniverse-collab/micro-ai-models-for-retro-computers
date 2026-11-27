/* rt_model.c - v0.9.0 SLIM loader (see rt_model.h).
 *
 * The full-format validator (dims table, charset compare, rt_model_size)
 * cost ~1.3 KB of Z80 - more than any chat feature. The cassette blob is
 * fixed-size (MSIZE), checksummed and self-consistent, so the loader
 * keeps only what protects a bad tape: magic, version, charset length
 * and the additive checksum over the WHOLE passed length. rt_model_size
 * is gone: the caller passes the exact blob length (1030).
 */
#include <stddef.h>
#include <string.h>
#include "rt_model.h"
#include "rt_charset.h"

static rt_u16 rd16(const rt_u8 *p)
{
    return (rt_u16)(p[0] | ((rt_u16)p[1] << 8));
}

int rt_model_load(rt_model *m, const rt_u8 *buf, long len)
{
    const rt_u8 *p = buf;
    rt_u32 sum = 0;
    long i, n;
    rt_u16 vocab, ctx, emb, h1, h2;

    if (len < 94)
        return -1;
    if (p[0] != RT_MAGIC0 || p[1] != RT_MAGIC1 ||
        p[2] != RT_MAGIC2 || p[3] != RT_MAGIC3)
        return -2;
    vocab = rd16(p + 8);
    ctx   = rd16(p + 10);
    emb   = rd16(p + 12);
    h1    = rd16(p + 14);
    h2    = rd16(p + 16);
    if (vocab != RT_CHARSET_LEN || ctx == 0 || ctx > RT_MAX_CTX ||
        emb == 0 || emb > RT_MAX_EMB || h1 == 0 || h1 > RT_MAX_HID)
        return -4;

    n = len - 2;
    for (i = 0; i < n; i++)
        sum = (sum + p[i]) & 0xFFFFUL;
    if ((rt_u16)sum != rd16(p + n))
        return -7;

    m->hdr.version = RT_VERSION;
    m->hdr.vocab = vocab;
    m->hdr.ctx = ctx;
    m->hdr.emb = emb;
    m->hdr.h1 = h1;
    m->hdr.h2 = h2;
    m->raw = buf;
    p = buf + 92;
    m->emb = (rt_i8 *)p;
    p += (long)vocab * emb;
    m->sh1 = (rt_u8 *)p;
    p += h1;
    m->w1 = (rt_i8 *)p;
    p += (long)h1 * ((long)ctx * emb + 1);
    if (h2) {
        m->sh2 = (rt_u8 *)p;
        p += h2;
        m->w2 = (rt_i8 *)p;
        p += (long)h2 * (h1 + 1);
    } else {
        m->sh2 = (rt_u8 *)0;
        m->w2 = (rt_i8 *)0;
    }
    m->sho = (rt_u8 *)p;
    p += vocab;
    m->wo = (rt_i8 *)p;
    return 0;
}
