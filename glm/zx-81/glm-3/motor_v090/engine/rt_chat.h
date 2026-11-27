#ifndef RT_CHAT_H
#define RT_CHAT_H

#include "rt_types.h"
#include "rt_model.h"

typedef struct {
    rt_u8 hist[RT_MAX_CTX]; /* rolling window of charset indices */
    int   hist_n;
    rt_u32 seed;
    int   greedy;   /* 1 = argmax decoding */
    int   temp_sh;  /* temperature as a right shift (0 sharp .. 6 flat) */
    int   max_new;  /* hard cap on one reply */
} rt_chat;

/* Callback receives generated ASCII chars one by one (live typing).
 * v0.9.0: full prototype - z88dk 2.5 (sccz80 AND zsdcc) parses it; the
 * unprototyped K&R form broke the zsdcc build. */
typedef void (*rt_emit_fn)(char c, void *user);

void rt_chat_init(rt_chat *c, rt_u32 seed);
void rt_chat_push_idx(rt_chat *c, rt_u8 idx);
void rt_chat_push(rt_chat *c, const char *s); /* maps via rt_map_char */
int  rt_chat_gen(rt_chat *c, const rt_model *m, rt_emit_fn fn, void *user);
void rt_chat_context(const rt_chat *c, char *out, int maxlen);

#endif /* RT_CHAT_H */
