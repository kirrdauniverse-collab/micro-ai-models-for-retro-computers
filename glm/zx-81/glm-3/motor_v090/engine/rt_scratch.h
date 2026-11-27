#ifndef RT_SCRATCH_H
#define RT_SCRATCH_H

#include "rt_types.h"
#include "rt_memory.h"
#include "rt_journal.h"

/* Screen-RAM scratch tier - "borrowed" storage in display memory.
 *
 * Classic 8-bit trick (ZX Spectrum disk-copy utilities lived in the top
 * third of the screen): the bytes of screen lines the app does not print
 * to are real RAM - use them as a small non-volatile store for learned
 * facts and journal entries when disk and tape are unavailable, instead
 * of paying BSS for them. The screen area shows harmless garbage there;
 * the trade is documented in docs/SCRATCH.md.
 *
 * Storage capacities (v0.2.2):
 *   ZX Spectrum  top third of pixel RAM          2048 cells x 8 bits
 *   C64          old screen area after VIC move  1016 cells x 8 bits
 *   C16/Plus4    top 5 rows of the TED screen     200 cells x 8 bits
 *   ZX81         top 8 rows of the D-file         256 cells x 6 bits
 *
 * The 6-bit case is the ZX81's: the ROM display routine renders every
 * D-file cell, so only real glyph codes (0x00-0x3F, single-cell) may be
 * stored - keyword/control codes and the 0x76 (HALT) line terminator are
 * forbidden. Everything is packed 3 bytes -> 4 cells, 6 bits each.
 *
 * Blob layout (byte stream): 'R','S','C','1', version, fact count (u8),
 * journal count (u16 LE), xor checksum, spare; then newest-first facts
 * (key+val) and the newest journal entries (date+text) that fit,
 * chronological within each. Counts and
 * lengths are planned by rt_scratch_plan() so the tier fits what fits.
 */

/* Capacity in bytes for a given cell count / bits-per-cell. */
#define RT_SCRATCH_CAP(cells, bits) (((cells) * (long)(bits)) / 8)

/* Blob overhead: 4 magic + 1 version + 1 fact count + 2 journal count,
 * plus the xor checksum and nothing else stored after the records; the
 * checksum byte itself brings the minimum footprint to 9. */
#define RT_SCRATCH_HDR 9

/* One stored record: key+value, or date+text. */
#define RT_SCRATCH_REC_FACT (RT_MEM_KEY + RT_MEM_VAL)
#define RT_SCRATCH_REC_J    (4 + RT_JOURNAL_TEXT)

/* How many facts / journal entries fit into `cap` bytes?  If everything
 * fits, all of it; otherwise a proportional split by raw record size,
 * newest-first within each kind (facts that fit are the most recently
 * taught, journal entries the most recent). */
void rt_scratch_plan(long cap, int n_facts, int n_journal,
                     int *kf, int *kj);

/* 3 bytes -> 4 glyph-safe cells (0x00-0x3F each), MSB first. Returns
 * cells written (ceil(n*3/4)), or negative if cellmax is too small. */
long rt_scratch_pack6(const rt_u8 *data, long n, rt_u8 *cells, long cellmax);

/* Inverse of rt_scratch_pack6. Returns bytes recovered. */
long rt_scratch_unpack6(const rt_u8 *cells, long ncells,
                        rt_u8 *out, long outmax);

/* Capacity of the current machine's tier in bytes, or -1 if the HAL
 * reports no scratch area. */
long rt_scratch_capacity(void);

/* Store facts + journal into the scratch tier. Returns bytes stored,
 * or negative (unsupported / nothing stored / did not fit). */
long rt_scratch_store(const rt_memory *mem, const rt_journal *j);

/* Restore from the scratch tier. Fields the caller already has (nonzero
 * fact count / journal entries) are left alone; only missing state is
 * filled. Returns 0 restored something, negative if absent or broken. */
long rt_scratch_restore(rt_memory *mem, rt_journal *j);

#endif /* RT_SCRATCH_H */
