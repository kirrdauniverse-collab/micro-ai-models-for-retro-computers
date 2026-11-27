#ifndef RT_CHARSET_H
#define RT_CHARSET_H

#include "rt_types.h"

/* Single source of truth: training/rtcharset.py defines the same string.
 * pack.py embeds the charset into every model.bin and rt_model_load()
 * refuses a model whose charset differs, so the copies cannot drift.
 *
 * Layout: newline, space, a-z, , . ? ! ', 0-9, :, -   (45 chars)
 * Input folding: A-Z -> a-z, anything unknown -> space.
 */
#define RT_CHARSET_LEN 48

extern const char RT_CHARSET[RT_CHARSET_LEN + 1];
extern rt_u8 RT_CHAR_TO_IDX[128];

void rt_charset_init(void); /* call once at startup */
rt_u8 rt_map_char(char c);  /* map any input byte to a charset index */

#endif /* RT_CHARSET_H */
