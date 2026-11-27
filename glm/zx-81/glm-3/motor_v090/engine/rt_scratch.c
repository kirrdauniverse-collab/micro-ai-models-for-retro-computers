/* rt_scratch.c - see rt_scratch.h */
#include "rt_config.h"
#include "rt_hal.h"
#include "rt_scratch.h"

#define SCRATCH_VERSION 1

/* ---------- 6-bit codec, array form (tests + reference) ----------
 * 3 bytes -> 4 cells, MSB first: c0=b0>>2, c1=((b0&3)<<4)|(b1>>4),
 * c2=((b1&15)<<2)|(b2>>6), c3=b2&63; tails are zero-padded.
 *
 * All arithmetic here is deliberately 16-bit (int/unsigned): the ZX81
 * port's z88dk 1.8 toolchain links the 32-bit shift/and/or library
 * modules badly, and the accumulators only ever hold 14 significant
 * bits anyway. Variable shifts are spelled as switch statements over
 * constant shift counts for the same reason. */

long rt_scratch_pack6(const rt_u8 *data, long n_, rt_u8 *cells,
                      long cellmax_)
{
    int n = (int)n_;
    int cellmax = (int)cellmax_;
    int need = (n * 8 + 5) / 6; /* 6 bits per cell, 8 bits per byte */
    int i, o = 0;
    unsigned acc = 0;
    int avail = 0;

    if (need > cellmax)
        return -1;
    for (i = 0; i < n; i++) {
        acc = (acc << 8) | data[i];
        avail += 8;
        while (avail >= 6) {
            int c;
            avail -= 6;
            switch (avail) { /* (acc >> avail) & 0x3F, constant shifts */
            case 0:  c = acc & 0x3F; break;
            case 1:  c = (acc >> 1) & 0x3F; break;
            case 2:  c = (acc >> 2) & 0x3F; break;
            case 3:  c = (acc >> 3) & 0x3F; break;
            case 4:  c = (acc >> 4) & 0x3F; break;
            case 5:  c = (acc >> 5) & 0x3F; break;
            case 6:  c = (acc >> 6) & 0x3F; break;
            default: c = (acc >> 7) & 0x3F; break; /* avail == 7 */
            }
            cells[o++] = (rt_u8)c;
        }
    }
    if (avail > 0) {
        int c = 0;
        switch (6 - avail) { /* (acc << (6 - avail)) & 0x3F */
        case 1:  c = (acc << 1) & 0x3F; break;
        case 2:  c = (acc << 2) & 0x3F; break;
        case 3:  c = (acc << 3) & 0x3F; break;
        case 4:  c = (acc << 4) & 0x3F; break;
        case 5:  c = (acc << 5) & 0x3F; break;
        default: c = 0; break;
        }
        cells[o++] = (rt_u8)c;
    }
    return o;
}

long rt_scratch_unpack6(const rt_u8 *cells, long ncells_,
                        rt_u8 *out, long outmax_)
{
    int ncells = (int)ncells_;
    int outmax = (int)outmax_;
    int i, o = 0;
    unsigned acc = 0;
    int avail = 0;

    for (i = 0; i < ncells; i++) {
        acc = (acc << 6) | (cells[i] & 0x3F);
        avail += 6;
        if (avail >= 8) {
            int b;
            avail -= 8;
            if (o >= outmax)
                return -1;
            switch (avail) { /* (acc >> avail) & 0xFF, constant shifts */
            case 0:  b = acc & 0xFF; break;
            case 1:  b = (acc >> 1) & 0xFF; break;
            case 2:  b = (acc >> 2) & 0xFF; break;
            case 3:  b = (acc >> 3) & 0xFF; break;
            case 4:  b = (acc >> 4) & 0xFF; break;
            default: b = (acc >> 5) & 0xFF; break; /* avail == 5 */
            }
            out[o++] = (rt_u8)b;
        }
    }
    return o;
}

/* ---------- sequential byte stream over the HAL cells ---------- */

static int      wr_bits;
static int      wr_cell;
static unsigned wr_acc;
static int      wr_avail;
static int      wr_err;

static void wr_begin(int bits)
{
    wr_bits = bits;
    wr_cell = 0;
    wr_acc = 0;
    wr_avail = 0;
    wr_err = 0;
}

static void wr_cell_6(unsigned acc, int avail)
{
    int c;
    switch (avail) { /* (acc >> avail) & 0x3F, constant shifts */
    case 0:  c = acc & 0x3F; break;
    case 1:  c = (acc >> 1) & 0x3F; break;
    case 2:  c = (acc >> 2) & 0x3F; break;
    case 3:  c = (acc >> 3) & 0x3F; break;
    case 4:  c = (acc >> 4) & 0x3F; break;
    case 5:  c = (acc >> 5) & 0x3F; break;
    case 6:  c = (acc >> 6) & 0x3F; break;
    default: c = (acc >> 7) & 0x3F; break; /* avail == 7 */
    }
    hal_scratch_put(wr_cell++, (rt_u8)c);
}

static void wr_byte(rt_u8 b)
{
    if (wr_err)
        return;
    if (wr_bits == 8) {
        hal_scratch_put(wr_cell++, b);
        return;
    }
    wr_acc = (wr_acc << 8) | b;
    wr_avail += 8;
    while (wr_avail >= 6) {
        wr_avail -= 6;
        wr_cell_6(wr_acc, wr_avail);
    }
}

static void wr_flush(void)
{
    if (wr_err || wr_bits != 6)
        return;
    if (wr_avail > 0) {
        int c = 0;
        switch (6 - wr_avail) { /* (acc << (6 - avail)) & 0x3F */
        case 1:  c = (wr_acc << 1) & 0x3F; break;
        case 2:  c = (wr_acc << 2) & 0x3F; break;
        case 3:  c = (wr_acc << 3) & 0x3F; break;
        case 4:  c = (wr_acc << 4) & 0x3F; break;
        case 5:  c = (wr_acc << 5) & 0x3F; break;
        default: c = 0; break;
        }
        hal_scratch_put(wr_cell++, (rt_u8)c);
        wr_avail = 0;
    }
}

static int      rd_bits;
static int      rd_cell;
static unsigned rd_acc;
static int      rd_avail;
static int      rd_err;

static void rd_begin(int bits)
{
    rd_bits = bits;
    rd_cell = 0;
    rd_acc = 0;
    rd_avail = 0;
    rd_err = 0;
}

static rt_u8 rd_byte(void)
{
    if (rd_err)
        return 0;
    if (rd_bits == 8)
        return hal_scratch_get(rd_cell++);
    while (rd_avail < 8) {
        rd_acc = (rd_acc << 6) | (hal_scratch_get(rd_cell++) & 0x3F);
        rd_avail += 6;
    }
    {
        int b;
        rd_avail -= 8;
        switch (rd_avail) { /* (acc >> avail) & 0xFF, constant shifts */
        case 0:  b = rd_acc & 0xFF; break;
        case 1:  b = (rd_acc >> 1) & 0xFF; break;
        case 2:  b = (rd_acc >> 2) & 0xFF; break;
        case 3:  b = (rd_acc >> 3) & 0xFF; break;
        case 4:  b = (rd_acc >> 4) & 0xFF; break;
        default: b = (rd_acc >> 5) & 0xFF; break; /* avail == 5 */
        }
        return (rt_u8)b;
    }
}

/* ---------- capacity + planning ---------- */

long rt_scratch_capacity(void)
{
    int cells = (int)hal_scratch_cells();
    int bits;

    if (cells <= 0)
        return -1;
    bits = hal_scratch_bits();
    if (bits != 6 && bits != 8)
        return -1;
    return (long)((cells * bits) / 8); /* <= 2048*8: fits 16-bit */
}

void rt_scratch_plan(long cap_, int n_facts, int n_journal,
                     int *kf, int *kj)
{
    int cap = (int)cap_;
    int room = cap - RT_SCRATCH_HDR;
    int tot, x, kf_bytes;

    *kf = 0;
    *kj = 0;
    if (n_facts < 0)
        n_facts = 0;
    if (n_journal < 0)
        n_journal = 0;
    if (room <= 0)
        return;
    tot = n_facts * RT_SCRATCH_REC_FACT + n_journal * RT_SCRATCH_REC_J;
    if (tot <= room) { /* everything fits */
        *kf = n_facts;
        *kj = n_journal;
        return;
    }
    if (tot <= 0)
        return;
    /* proportional split by raw record size; the only 32-bit operation
     * is one multiply + one divide (the long ops the ZX81 toolchain
     * links correctly - unlike 32-bit shifts and bitwise ops) */
    x = n_facts * RT_SCRATCH_REC_FACT;
    kf_bytes = (int)(((long)room * x) / tot);
    *kf = kf_bytes / RT_SCRATCH_REC_FACT;
    if (*kf > n_facts)
        *kf = n_facts;
    *kj = (room - *kf * RT_SCRATCH_REC_FACT) / RT_SCRATCH_REC_J;
    if (*kj > n_journal)
        *kj = n_journal;
    if (*kf < 0)
        *kf = 0;
    if (*kj < 0)
        *kj = 0;
}

/* ---------- store / restore ---------- */

/* Blob: 'R','S','C','1', version, kf (u8), kj (u16 LE), then kf newest
 * facts, then kj newest journal entries, then an xor checksum of the
 * record bytes. 9 bytes of overhead; the checksum sits at the end so
 * the whole stream stays strictly sequential. */

long rt_scratch_store(const rt_memory *mem, const rt_journal *j)
{
    int cells = (int)hal_scratch_cells();
    int bits, kf, kj, i;
    int cap, stored = 0;
    rt_u8 xsum = 0;

    if (cells <= 0)
        return -1;
    bits = hal_scratch_bits();
    if (bits != 6 && bits != 8)
        return -1;
    cap = (int)((cells * bits) / 8);
    rt_scratch_plan(cap, mem->n, j->n, &kf, &kj);
    if (kf <= 0 && kj <= 0)
        return -2;

    wr_begin(bits);
    wr_byte('R');
    wr_byte('S');
    wr_byte('C');
    wr_byte('1');
    wr_byte(SCRATCH_VERSION);
    wr_byte((rt_u8)kf);
    wr_byte((rt_u8)(kj & 0xFF));
    wr_byte((rt_u8)((kj >> 8) & 0xFF));
    for (i = mem->n - kf; i < mem->n; i++) { /* newest facts, chronological */
        const rt_mem_rec *r = &mem->rec[i];
        int k;
        for (k = 0; k < RT_MEM_KEY; k++) {
            wr_byte((rt_u8)r->key[k]);
            xsum ^= (rt_u8)r->key[k];
        }
        for (k = 0; k < RT_MEM_VAL; k++) {
            wr_byte((rt_u8)r->val[k]);
            xsum ^= (rt_u8)r->val[k];
        }
        stored += RT_SCRATCH_REC_FACT;
    }
    for (i = j->n - kj; i < j->n; i++) { /* newest entries, chronological */
        const rt_jentry *e = &j->e[i];
        int k;
        wr_byte(e->yoff); xsum ^= e->yoff;
        wr_byte(e->mo);   xsum ^= e->mo;
        wr_byte(e->d);    xsum ^= e->d;
        wr_byte(e->wd);   xsum ^= e->wd;
        for (k = 0; k < RT_JOURNAL_TEXT; k++) {
            wr_byte((rt_u8)e->text[k]);
            xsum ^= (rt_u8)e->text[k];
        }
        stored += RT_SCRATCH_REC_J;
    }
    wr_byte(xsum);
    wr_flush();
    if (wr_err)
        return -3;
    return RT_SCRATCH_HDR + stored;
}

static int rd_records(rt_memory *mem, rt_journal *j, int kf, int kj,
                      int want_facts, int want_journal)
{
    rt_u8 xsum = 0, x, b;
    int i, k;

    for (i = 0; i < kf; i++) {
        rt_mem_rec *r = want_facts ? &mem->rec[i] : 0;
        for (k = 0; k < RT_MEM_KEY; k++) {
            b = rd_byte();
            xsum ^= b;
            if (r)
                r->key[k] = (char)b;
        }
        for (k = 0; k < RT_MEM_VAL; k++) {
            b = rd_byte();
            xsum ^= b;
            if (r)
                r->val[k] = (char)b;
        }
    }
    for (i = 0; i < kj; i++) {
        rt_jentry *e = want_journal ? &j->e[i] : 0; /* chronological */
        rt_u8 f[4];
        f[0] = rd_byte(); xsum ^= f[0];
        f[1] = rd_byte(); xsum ^= f[1];
        f[2] = rd_byte(); xsum ^= f[2];
        f[3] = rd_byte(); xsum ^= f[3];
        for (k = 0; k < RT_JOURNAL_TEXT; k++) {
            b = rd_byte();
            xsum ^= b;
            if (e)
                e->text[k] = (char)b;
        }
        if (e) {
            e->yoff = f[0]; e->mo = f[1]; e->d = f[2]; e->wd = f[3];
        }
    }
    x = rd_byte(); /* stored checksum */
    return (x == xsum && !rd_err) ? 0 : -1;
}

long rt_scratch_restore(rt_memory *mem, rt_journal *j)
{
    int cells = (int)hal_scratch_cells();
    int bits, kf, kj;
    int want_facts, want_journal;

    if (cells <= 0)
        return -1;
    bits = hal_scratch_bits();
    if (bits != 6 && bits != 8)
        return -1;
    rd_begin(bits);
    if (rd_byte() != 'R' || rd_byte() != 'S' || rd_byte() != 'C'
        || rd_byte() != '1')
        return -2;
    if (rd_byte() != SCRATCH_VERSION)
        return -2;
    kf = rd_byte();
    kj = rd_byte() | (rd_byte() << 8);
    if (rd_err || kf < 0 || kf > RT_MEM_MAX || kj > RT_JOURNAL_MAX
        || (kf == 0 && kj == 0))
        return -2;
    want_facts = (mem->n == 0 && kf > 0);
    want_journal = (j->n == 0 && kj > 0);
    if (rd_records(mem, j, kf, kj, want_facts, want_journal) != 0)
        return -3;
    if (want_facts)
        mem->n = kf;
    if (want_journal)
        j->n = kj;
    return 0;
}
