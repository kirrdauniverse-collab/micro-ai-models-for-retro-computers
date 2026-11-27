/* rt_chat.c - rolling-context chat state + generation loop.
 * '\n' (charset index 0) separates turns, exactly like in the training
 * corpus, so the model learns when to stop talking.
 */
#include <stddef.h>
#include "rt_chat.h"
#include "rt_charset.h"
#include "rt_engine.h"

static rt_i32 rt_logits[RT_MAX_VOCAB];

void rt_chat_push_idx(rt_chat *c, rt_u8 idx)
{
    int i;
    if (c->hist_n < RT_MAX_CTX) {
        c->hist[c->hist_n++] = idx;
        return;
    }
    for (i = 1; i < RT_MAX_CTX; i++)
        c->hist[i - 1] = c->hist[i];
    c->hist[RT_MAX_CTX - 1] = idx;
}

void rt_chat_push(rt_chat *c, const char *s)
{
    while (*s)
        rt_chat_push_idx(c, rt_map_char(*s++));
}

int rt_chat_gen(rt_chat *c, const rt_model *m, rt_emit_fn fn, void *user)
{
    rt_u8 win[RT_MAX_CTX];
    int i, n = 0, cap = c->max_new;
    int empty = 3; /* tolerate a few leading newlines: never reply nothing */

    while (n < cap) {
        int idx;
        int ctx = (int)m->hdr.ctx;

        /* right-aligned window; virtual spaces before the first input */
        for (i = 0; i < ctx; i++) {
            int pos = c->hist_n - ctx + i;
            win[i] = (pos < 0) ? (rt_u8)1 : c->hist[pos];
        }

        rt_forward(m, win, rt_logits);
        idx = rt_sample(m, rt_logits, c->temp_sh, c->greedy, &c->seed);
        if (idx == 0) { /* newline ends the turn */
            if (n == 0 && empty > 0) {
                empty--;
                continue; /* sampled "silence": try again */
            }
            break;
        }
        if (fn)
            fn(RT_CHARSET[idx], user);
        rt_chat_push_idx(c, (rt_u8)idx);
        n++;
    }
    return n;
}

