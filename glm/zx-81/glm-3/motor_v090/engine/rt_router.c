/* rt_router.c - keyword topic routing (see rt_router.h). */
#include <string.h>
#include <stddef.h>
#include "rt_router.h"
#include "rt_charset.h"

/* The standard topic packs shipped with the project. Keep in sync with
 * models/manifest.cfg and tools/build_tape.sh. "star"/"moon"/"sky" are
 * deliberately shared between space and poems - that is the ambiguity
 * the clarifying question resolves. */
static const char *DEF_NAMES[] = {
    "retro", "weather", "animals", "numbers", "jokes", "space", "poems"
};
static const char *DEF_KEYS[] = {
    /* retro */     "computer amiga commodore spectrum zx zx81 c64 tape "
                    "disk floppy cpu ram byte program basic code coding "
                    "programmer datasette retro int8 quant model machine "
                    "keyboard monitor joystick enterprise tvc",
    /* weather */   "weather rain rainy sunny sun cloud cloudy wind windy "
                    "snow snowy fog storm cold hot warm temperature sky "
                    "umbrella wet dry",
    /* animals */   "animal cat dog mouse rabbit parrot hamster turtle "
                    "pet fish bird horse snake zoo",
    /* numbers */   "number math plus minus times count calculate sum "
                    "digit multiply add",
    /* jokes */     "joke funny laugh humor pun silly",
    /* space */     "star stars planet planets moon galaxy mars venus "
                    "saturn jupiter space astronomy astronomer telescope "
                    "comet orbit sky universe neptune mercury",
    /* poems */     "poem poetry poet verse rhyme star stars love heart "
                    "moon night verse sky"
};

static const char *t_names[RT_TOPIC_MAX];
static const char *t_keys[RT_TOPIC_MAX];
static int t_n = 7; /* DEF_NAMES entries: retro weather animals numbers jokes space poems */
static int t_ready;

#ifndef RT_ROUTER_NO_SET
/* sccz80 1.8 cannot parse const char *const * parameters, so ports that
 * cannot take this function define RT_ROUTER_NO_SET (no engine code
 * calls it - the defaults are always live). Ports that do use it get a
 * shallow copy into the tables above. */
void rt_router_set(const char *const *names, const char *const *keys, int n)
{
    int i;
    if (n > 0 && n <= RT_TOPIC_MAX) {
        for (i = 0; i < n; i++) {
            t_names[i] = names[i];
            t_keys[i] = keys[i];
        }
        t_n = n;
        t_ready = 1;
    }
}
#endif

/* whole-word containment on sanitized lowercase text */
static int has_word(const char *text, const char *word)
{
    int ti, wi;
    for (ti = 0; text[ti]; ti++) {
        char before = ti ? text[ti - 1] : ' ';
        char after;
        if (before >= 'a' && before <= 'z')
            continue; /* not a word start */
        for (wi = 0; word[wi]; wi++)
            if (text[ti + wi] != word[wi])
                break;
        if (word[wi] != '\0')
            continue;
        after = text[ti + wi];
        if (!((after >= 'a' && after <= 'z') ||
              (after >= '0' && after <= '9')))
            return 1; /* word edge after the match */
    }
    return 0;
}

int rt_router_scan(const char *text, char *hits, int max_hits)
{
    char clean[96];
    int i, j, n = 0;

    if (!t_ready) { /* install the default table (pointer arrays) */
        for (i = 0; i < t_n; i++) {
            t_names[i] = DEF_NAMES[i];
            t_keys[i] = DEF_KEYS[i];
        }
        t_ready = 1;
    }

    /* map to the model charset so "Stars!" matches too */
    for (i = 0; text[i] && i < (int)sizeof(clean) - 1; i++)
        clean[i] = (char)RT_CHARSET[rt_map_char(text[i])];
    clean[i] = '\0';

    for (i = 0; i < t_n && n < max_hits; i++) {
        const char *k = t_keys[i];
        while (*k) {
            char word[16];
            int wl = 0;
            while (*k == ' ')
                k++;
            while (*k && *k != ' ' && wl < 15)
                word[wl++] = *k++;
            word[wl] = '\0';
            if (wl >= 3 && has_word(clean, word)) {
                /* deduplicate: first hit wins */
                for (j = 0; j < n; j++)
                    if (strncmp(hits + j * 16, t_names[i], 15) == 0)
                        break;
                if (j == n) {
                    strncpy(hits + n * 16, t_names[i], 15);
                    hits[n * 16 + 15] = 0;
                    n++;
                }
                break; /* one keyword is enough for this topic */
            }
        }
    }
    return n;
}
