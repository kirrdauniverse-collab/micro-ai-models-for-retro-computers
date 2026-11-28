/* rt_model.c - see rt_model.h */
#include <stddef.h>
#include <string.h>
#include "rt_model.h"
#include "rt_charset.h"

static rt_u16 rd16(const rt_u8 *p)
{
    return (rt_u16)(p[0] | ((rt_u16)p[1] << 8));
}

long rt_model_size(const rt_hdr *h)
{
    long n;
    n = 92;
    n += (long)h->vocab * h->emb;
    n += h->h1 + (long)h->h1 * ((long)h->ctx * h->emb + 1);
    if (h->h2)
        n += h->h2 + (long)h->h2 * (h->h1 + 1);
    n += h->vocab + (long)h->vocab * ((h->h2 ? h->h2 : h->h1) + 1);
    n += 2; /* checksum */
    return n;
}

int rt_model_load(rt_model *m, const rt_u8 *buf, long len)
{
    const rt_u8 *p = buf;
    rt_hdr h;
    long need, i;

    if (len < 94)
        return -1;
    if (p[0] != RT_MAGIC0 || p[1] != RT_MAGIC1 ||
        p[2] != RT_MAGIC2 || p[3] != RT_MAGIC3)
        return -2;

    h.version = rd16(p + 4);
    if (h.version != RT_VERSION)
        return -3;
    h.flags   = rd16(p + 6);
    h.vocab   = rd16(p + 8);
    h.ctx     = rd16(p + 10);
    h.emb     = rd16(p + 12);
    h.h1      = rd16(p + 14);
    h.h2      = rd16(p + 16);
    h.sh_e    = rd16(p + 18);
    h.sh1     = rd16(p + 20);
    h.sh2     = rd16(p + 22);
    h.sh_o    = rd16(p + 24);
    h.temp_sh = rd16(p + 26);

    if (h.vocab == 0 || h.vocab > RT_MAX_VOCAB ||
        h.ctx == 0 || h.ctx > RT_MAX_CTX ||
        h.emb == 0 || h.emb > RT_MAX_EMB ||
        h.h1 == 0 || h.h1 > RT_MAX_HID ||
        h.h2 > RT_MAX_HID)
        return -4;
    if (h.vocab != RT_CHARSET_LEN)
        return -5;

    for (i = 0; i < RT_CHARSET_LEN; i++)
        if (p[28 + i] != (rt_u8)RT_CHARSET[i])
            return -6;

    { /* additive checksum over everything before the last two bytes */
        rt_u32 sum = 0;
        long n = len - 2;
        for (i = 0; i < n; i++)
            sum = (sum + p[i]) & 0xFFFFUL;
        if ((rt_u16)sum != rd16(p + n))
            return -7;
    }

    need = rt_model_size(&h);
    if (need > len)
        return -8;

    memcpy(&m->hdr, &h, sizeof(rt_hdr));
    m->raw = buf;
    p = buf + 92;
    m->emb = (rt_i8 *)p;
    p += (long)h.vocab * h.emb;

    m->sh1 = (rt_u8 *)p;
    p += h.h1;
    m->w1 = (rt_i8 *)p;
    p += (long)h.h1 * ((long)h.ctx * h.emb + 1);

    if (h.h2) {
        m->sh2 = (rt_u8 *)p;
        p += h.h2;
        m->w2 = (rt_i8 *)p;
        p += (long)h.h2 * (h.h1 + 1);
    } else {
        m->sh2 = (rt_u8 *)0;
        m->w2 = (rt_i8 *)0;
    }

    m->sho = (rt_u8 *)p;
    p += h.vocab;
    m->wo = (rt_i8 *)p;
    return 0;
}
