/* rt_journal.c - dated episodic memory (see rt_journal.h). */
#include <string.h>
#include <stddef.h>
#include "rt_journal.h"
#include "rt_charset.h"

#define RTJ_MAGIC0 'R'
#define RTJ_MAGIC1 'T'
#define RTJ_MAGIC2 'J'
#define RTJ_MAGIC3 '1'

/* Phrases that mark something worth remembering about the user. */
static const char *FEELINGS[] = {
    "my head hurts", "my head aches", "i am tired", "i am sleepy",
    "i am sad", "i am happy", "i am angry", "i am sick", "i am ill",
    "i have a cold", "i have a headache", "i feel bad", "i feel good",
    "i feel great", "i feel ill", "i am hungry", "i am bored",
    "i can not sleep", "i am lonely", "i am nervous", "i am stressed",
    "my back hurts", "my tooth hurts", "i have a fever",
};
#define N_FEELINGS 24 /* the FEELINGS table above */

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

void rt_journal_init(rt_journal *j)
{
    int i;
    for (i = 0; i < RT_JOURNAL_MAX; i++)
        j->e[i].text[0] = '\0';
    j->n = 0;
}

int rt_journal_add(rt_journal *j, const rt_clock *day, const char *text)
{
    char clean[RT_JOURNAL_TEXT];
    int i;
    sanitize(clean, RT_JOURNAL_TEXT, text);
    if (clean[0] == '\0')
        return -2;
    for (i = 0; i < j->n; i++)
        if (strcmp(j->e[i].text, clean) == 0 &&
            j->e[i].yoff == (rt_u8)(day->y - 2000) &&
            j->e[i].mo == (rt_u8)day->mo && j->e[i].d == (rt_u8)day->d)
            return 0; /* same note, same day: keep one */
    if (j->n >= RT_JOURNAL_MAX)
        return -1;
    j->e[j->n].yoff = (rt_u8)(day->y - 2000);
    j->e[j->n].mo = (rt_u8)day->mo;
    j->e[j->n].d = (rt_u8)day->d;
    j->e[j->n].wd = (rt_u8)day->wd;
    strcpy(j->e[j->n].text, clean);
    j->n++;
    return 0;
}

static int contains(const char *hay, const char *needle)
{
    return strstr(hay, needle) != NULL;
}

int rt_journal_scan_feelings(const char *text, char *matched, int maxlen)
{
    char clean[96];
    int i;
    sanitize(clean, sizeof(clean), text);
    for (i = 0; i < (int)N_FEELINGS; i++)
        if (contains(clean, FEELINGS[i])) {
            if (matched && maxlen > 0) {
                strncpy(matched, FEELINGS[i], maxlen - 1);
                matched[maxlen - 1] = '\0';
            }
            return 1;
        }
    return 0;
}

int rt_journal_recent(const rt_journal *j, const rt_clock *today,
                      int maxdays, int idxs[], int max)
{
    int i, n = 0;
    for (i = j->n - 1; i >= 0 && n < max; i--) {
        rt_clock then;
        long diff;
        then.y = j->e[i].yoff + 2000;
        then.mo = j->e[i].mo;
        then.d = j->e[i].d;
        then.h = 12; then.mi = 0; then.wd = j->e[i].wd; then.valid = 1;
        diff = rt_clock_days_diff(&then, today);
        if (diff > 0 && diff <= maxdays)
            idxs[n++] = i;
    }
    return n;
}

long rt_journal_pack(const rt_journal *j, rt_u8 *buf, long maxlen)
{
    long need = 8 + (long)j->n * (4 + RT_JOURNAL_TEXT);
    int i, k;
    if (maxlen < need)
        return -1;
    buf[0] = RTJ_MAGIC0; buf[1] = RTJ_MAGIC1;
    buf[2] = RTJ_MAGIC2; buf[3] = RTJ_MAGIC3;
    buf[4] = (rt_u8)(j->n & 0xFF);
    buf[5] = (rt_u8)((j->n >> 8) & 0xFF);
    buf[6] = 0; buf[7] = 0;
    need = 8;
    for (i = 0; i < j->n; i++) {
        buf[need++] = j->e[i].yoff;
        buf[need++] = j->e[i].mo;
        buf[need++] = j->e[i].d;
        buf[need++] = j->e[i].wd;
        for (k = 0; k < RT_JOURNAL_TEXT; k++)
            buf[need++] = (rt_u8)j->e[i].text[k];
    }
    return need;
}

long rt_journal_unpack(rt_journal *j, const rt_u8 *buf, long len)
{
    int n, i, k;
    long p;
    if (len < 8)
        return -1;
    if (buf[0] != RTJ_MAGIC0 || buf[1] != RTJ_MAGIC1 ||
        buf[2] != RTJ_MAGIC2 || buf[3] != RTJ_MAGIC3)
        return -2;
    n = buf[4] | (buf[5] << 8);
    if (n > RT_JOURNAL_MAX)
        return -3;
    if (len < 8 + (long)n * (4 + RT_JOURNAL_TEXT))
        return -4;
    rt_journal_init(j);
    p = 8;
    for (i = 0; i < n; i++) {
        j->e[i].yoff = buf[p++];
        j->e[i].mo = buf[p++];
        j->e[i].d = buf[p++];
        j->e[i].wd = buf[p++];
        for (k = 0; k < RT_JOURNAL_TEXT; k++)
            j->e[i].text[k] = (char)buf[p++];
        j->e[i].text[RT_JOURNAL_TEXT - 1] = '\0';
    }
    j->n = n;
    return p;
}
