#ifndef RT_JOURNAL_H
#define RT_JOURNAL_H

#include "rt_types.h"
#include "rt_config.h"
#include "rt_clock.h"

/* Dated episodic memory: the "little things" the user mentions in chat
 * ("my head hurts") are stored with the day they were said, saved to
 * journal.bin at the end of the session, and recalled on the next boot
 * ("on monday you said: my head hurts"). Complements the key=value fact
 * memory in rt_memory.h. */

#ifndef RT_JOURNAL_MAX
#define RT_JOURNAL_MAX 24
#endif

#define RT_JOURNAL_TEXT 80

typedef struct {
    rt_u8 yoff;  /* year - 2000 */
    rt_u8 mo;    /* 1..12 */
    rt_u8 d;     /* 1..31 */
    rt_u8 wd;    /* weekday 0=Sun..6=Sat (as entered) */
    char text[RT_JOURNAL_TEXT];
} rt_jentry;

typedef struct {
    rt_jentry e[RT_JOURNAL_MAX];
    int n;
} rt_journal;

void rt_journal_init(rt_journal *j);

/* Remember `text` under the given day. 0 ok, -1 full, -2 empty.
 * Same note on the same day is kept once (0 ok). */
int  rt_journal_add(rt_journal *j, const rt_clock *day, const char *text);

/* Does the input mention a feeling/state worth remembering? Returns 1
 * and copies the matched phrase (optional out param). */
int  rt_journal_scan_feelings(const char *text, char *matched, int maxlen);

/* Indices of entries from EARLIER days, newest first, within `maxdays`
 * of `today`. Returns count. */
int  rt_journal_recent(const rt_journal *j, const rt_clock *today,
                       int maxdays, int idxs[], int max);

/* Serialize ("RTJ1"): magic, count, 4-byte date + text per entry. */
long rt_journal_pack(const rt_journal *j, rt_u8 *buf, long maxlen);
long rt_journal_unpack(rt_journal *j, const rt_u8 *buf, long len);

#endif /* RT_JOURNAL_H */
