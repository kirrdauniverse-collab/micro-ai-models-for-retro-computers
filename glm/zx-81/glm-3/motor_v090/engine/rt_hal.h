/* rt_hal.h - platform abstraction layer.
 *
 * Every port implements these functions. Disk is the PRIMARY model source
 * ("disk first, tape variant" requirement); tape is used where the machine
 * has one, and always via whole-block loads so the portable engine never
 * deals with pulses itself.
 */
#ifndef RT_HAL_H
#define RT_HAL_H

#include "rt_types.h"

/* Load a whole file into buf. Returns length in bytes, or negative on
 * error. name is lowercase ASCII, at most 15 chars + NUL. */
long hal_load_file(const char *name, rt_u8 *buf, long maxlen);

/* Save a whole file (memory.bin with learned facts). 0 = ok, -1 = error. */
int hal_save_file(const char *name, const rt_u8 *buf, long len);

/* Load the n-th tape block (0-based, skipping earlier ones) into buf.
 * Returns length or negative (-1 unsupported / not found, -2 read error).
 * Blocks are RT-turbo pulses or platform-native format. */
long hal_tape_load(int index, rt_u8 *buf, long maxlen);

/* Write one block to tape. 0 = ok, negative = error / unsupported. */
int hal_tape_save(int index, const rt_u8 *buf, long len);

/* Console. hal_getchar returns -1 when no key is pending.
 * NOTE: on machines with a scratch tier the HAL owns the text area
 * below the reserved screen rows (see docs/SCRATCH.md). */
int  hal_getchar(void);
int  hal_kbhit(void);
void hal_putchar(int c);
void hal_flush(void);
void hal_msleep(long ms);

/* Entropy for the PRNG seed (frame counter, timer, key jitter...). */
rt_u32 hal_entropy(void);

/* List loadable topic packs into names - a FLAT buffer of `max` entries,
 * 16 bytes each (NUL-terminated, lowercase). Returns count, or -1 when
 * listing is unsupported (fixed-order tape). The flat pointer keeps the
 * prototype parseable by strict and old C compilers alike. */
int hal_list_topics(char *names, int max);

/* Screen-RAM scratch tier (see docs/SCRATCH.md): cells of display memory
 * the app does not print to, used as a small store for facts/journal.
 * cells() returns the cell count, or -1 when the machine has none (OS
 * owns the screen, banking makes it unsafe, ...). bits() is 8 for raw
 * screen RAM or 6 for character-cell stores where only glyph codes
 * (0x00-0x3F on the ZX81) are legal. get/put address cell i linearly;
 * in 6-bit mode put() only ever receives a glyph-safe value. */
long  hal_scratch_cells(void);
int   hal_scratch_bits(void);
rt_u8 hal_scratch_get(long i);
void  hal_scratch_put(long i, rt_u8 v);
void  hal_scratch_char(long i, char c);

/* v0.9.0 status strip (the D-file's free upper-third row): every byte
 * written is a ROM-renderable glyph (plain 0x00-0x3F or inverse
 * 0x80-0xBF), never the quote glyph, never a HALT/control code. */
void  hal_status_clear(void);
void  hal_status_put(int i, rt_u8 code);
void  hal_status_char(int i, char c);
void  hal_spin_tick(int phase);

/* Fatal error: print message and stop. */
void hal_panic(const char *msg);

#endif /* RT_HAL_H */
