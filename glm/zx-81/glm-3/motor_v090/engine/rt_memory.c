/* rt_memory.c - teachable fact memory (the "learning" layer).
 *
 * Two learning mechanisms live in this project:
 *  1. retrieval  (this file): taught facts are stored and answered
 *     deterministically - works on every machine, survives reboots via
 *     memory.bin on disk or tape;
 *  2. fine-tuning (rt_finetune.c): the output layer weights are nudged
 *     so the MODEL itself starts reproducing the taught text.
 */
#include <stddef.h>
#include "rt_memory.h"
#include "rt_charset.h"

static void sanitize(char *dst, int dstlen, const char *src)
{
    int i;
    for (i = 0; i < dstlen - 1; i++) {
        char c = src[i];
        if (c == '\0')
            break;
        if (c == '\n')
            c = ' ';
        dst[i] = (char)RT_CHARSET[rt_map_char(c)];
    }
    dst[i] = '\0';
}

static int streq(const char *a, const char *b)
{
    while (*a && *a == *b) {
        a++;
        b++;
    }
    return *a == '\0' && *b == '\0';
}

void rt_mem_init(rt_memory *mem)
{
    int i;
    for (i = 0; i < RT_MEM_MAX; i++) {
        mem->rec[i].key[0] = '\0';
        mem->rec[i].val[0] = '\0';
    }
    mem->n = 0;
}

int rt_mem_teach(rt_memory *mem, const char *key, const char *val)
{
    int i, slot;
    char k[RT_MEM_KEY], v[RT_MEM_VAL];

    sanitize(k, RT_MEM_KEY, key);
    sanitize(v, RT_MEM_VAL, val);
    if (k[0] == '\0' || v[0] == '\0')
        return -2;

    /* re-teaching an existing key overwrites it */
    for (i = 0; i < mem->n; i++)
        if (streq(mem->rec[i].key, k)) {
            for (slot = 0; slot < RT_MEM_VAL; slot++)
                mem->rec[i].val[slot] = v[slot];
            return 0;
        }

    if (mem->n >= RT_MEM_MAX)
        return -1;
    slot = mem->n;
    for (i = 0; i < RT_MEM_KEY; i++)
        mem->rec[slot].key[i] = k[i];
    for (i = 0; i < RT_MEM_VAL; i++)
        mem->rec[slot].val[i] = v[i];
    mem->n++;
    return 0;
}

void rt_mem_forget(rt_memory *mem, int idx)
{
    int i;
    if (idx < 0 || idx >= mem->n)
        return;
    for (i = idx; i < mem->n - 1; i++)
        mem->rec[i] = mem->rec[i + 1];
    mem->n--;
    mem->rec[mem->n].key[0] = '\0';
    mem->rec[mem->n].val[0] = '\0';
}

/* does the question contain this word? (word = run of chars; a word edge
 * is anything that is not a lowercase letter or digit) */
static int has_word(const char *question, const char *word)
{
    int qi, wi, match;
    for (qi = 0; question[qi]; qi++) {
        char after;
        if (qi > 0) {
            char prev = question[qi - 1];
            if ((prev >= 'a' && prev <= 'z') || (prev >= '0' && prev <= '9'))
                continue; /* not the start of a word */
        }
        match = 1;
        for (wi = 0; word[wi]; wi++) {
            if (question[qi + wi] != word[wi]) {
                match = 0;
                break;
            }
        }
        after = question[qi + wi];
        if (match && !((after >= 'a' && after <= 'z') ||
                       (after >= '0' && after <= '9')))
            return 1;
    }
    return 0;
}

int rt_mem_match(const rt_memory *mem, const char *question)
{
    int i, best = -1, best_score = 0;
    char q[80];

    sanitize(q, sizeof(q), question);
    for (i = 0; i < mem->n; i++) {
        int score = 0;
        const char *k = mem->rec[i].key;
        int wi = 0;
        while (k[wi]) {
            char word[RT_MEM_KEY + 1];
            int wl = 0;
            while (k[wi] == ' ')
                wi++;
            while (k[wi] && k[wi] != ' ' && wl < RT_MEM_KEY)
                word[wl++] = k[wi++];
            word[wl] = '\0';
            if (wl >= 3 && has_word(q, word))
                score++;
        }
        if (score > best_score) {
            best_score = score;
            best = i;
        }
    }
    return best;
}

void rt_mem_answer(const rt_mem_rec *r, char *out, int maxlen)
{
    int i, o = 0;
    const char *pre = "my ";
    const char *k = r->key;

    /* "my name" -> "your name is X." ; everything else -> "my K is X." */
    if (k[0] == 'm' && k[1] == 'y' && k[2] == ' ') {
        pre = "your ";
        k += 3;
    }
    while (*pre && o < maxlen - 1)
        out[o++] = *pre++;
    while (*k && o < maxlen - 1)
        out[o++] = *k++;
    {
        const char *is = " is ";
        const char *p = is;
        while (*p && o < maxlen - 1)
            out[o++] = *p++;
    }
    for (i = 0; r->val[i] && o < maxlen - 1; i++)
        out[o++] = r->val[i];
    if (o < maxlen - 1)
        out[o++] = '.';
    out[o] = '\0';
}

long rt_mem_pack(const rt_memory *mem, rt_u8 *buf, long maxlen)
{
    long need = 8 + (long)mem->n * (RT_MEM_KEY + RT_MEM_VAL);
    int i, j;
    if (maxlen < need)
        return -1;
    buf[0] = RT_MEM_MAGIC0;
    buf[1] = RT_MEM_MAGIC1;
    buf[2] = RT_MEM_MAGIC2;
    buf[3] = RT_MEM_MAGIC3;
    buf[4] = (rt_u8)(mem->n & 0xFF);
    buf[5] = (rt_u8)((mem->n >> 8) & 0xFF);
    buf[6] = 0;
    buf[7] = 0;
    need = 8;
    for (i = 0; i < mem->n; i++) {
        for (j = 0; j < RT_MEM_KEY; j++)
            buf[need++] = (rt_u8)mem->rec[i].key[j];
        for (j = 0; j < RT_MEM_VAL; j++)
            buf[need++] = (rt_u8)mem->rec[i].val[j];
    }
    return need;
}

long rt_mem_unpack(rt_memory *mem, const rt_u8 *buf, long len)
{
    int n, i, j;
    long p;
    if (len < 8)
        return -1;
    if (buf[0] != RT_MEM_MAGIC0 || buf[1] != RT_MEM_MAGIC1 ||
        buf[2] != RT_MEM_MAGIC2 || buf[3] != RT_MEM_MAGIC3)
        return -2;
    n = buf[4] | (buf[5] << 8);
    if (n > RT_MEM_MAX)
        return -3;
    if (len < 8 + (long)n * (RT_MEM_KEY + RT_MEM_VAL))
        return -4;
    rt_mem_init(mem);
    p = 8;
    for (i = 0; i < n; i++) {
        for (j = 0; j < RT_MEM_KEY; j++)
            mem->rec[i].key[j] = (char)buf[p++];
        for (j = 0; j < RT_MEM_VAL; j++)
            mem->rec[i].val[j] = (char)buf[p++];
        mem->rec[i].key[RT_MEM_KEY - 1] = '\0';
        mem->rec[i].val[RT_MEM_VAL - 1] = '\0';
    }
    mem->n = n;
    return p;
}
