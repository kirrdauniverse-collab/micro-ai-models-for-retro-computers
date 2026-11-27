#ifndef RT_APP_H
#define RT_APP_H

#include "rt_types.h"

/* Portable chat application used by EVERY port (host, Amiga, C64, ZX...).
 * The port implements rt_hal.h, calls rt_app_boot() once and then
 * rt_app_run() which contains the full REPL loop and never returns.
 *
 * Commands (a '/' plus a word, lowercase):
 *   /help              command list
 *   /info              model dims, parameters, memory use
 *   /teach key = val   store a fact (learning, mechanism 1)
 *   /mem               list taught facts
 *   /forget n          delete fact n
 *   /save              write memory.bin (and the model after /finetune)
 *   /topics            list topic packs on disk/tape
 *   /load name         load a topic pack (name without .bin)
 *   /temp n            sampling temperature shift 0..6
 *   /greedy on|off     argmax decoding on/off
 *   /finetune          nudge output weights with the taught facts
 *                      (learning, mechanism 2; needs RT_ENABLE_FINETUNE)
 *   /sim off|amiga|c64|zx81  per-letter delay to feel target speed
 *   /quit              leave (host)
 * Anything else is chat input.
 */

int  rt_app_boot(const char *model_name); /* 0 ok, negative error */
int  rt_app_boot_tape(int block);         /* boot from the n-th tape block */
void rt_app_run(void);                    /* REPL loop, never returns */

#endif /* RT_APP_H */
