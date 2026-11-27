/* scratch_stub.c - ZX81: no screen-RAM scratch tier.
 *
 * The 48K cassette image is tight (the engine alone is ~30 KB of Z80
 * code), and the full rt_scratch.c codec costs another ~10 KB, so this
 * port ships without it: facts and journal live in RAM for the session
 * (that part is plain engine state) and /save reports that nothing
 * could be written - the same behaviour as the other tape-only ports.
 * The screen-RAM tier itself (docs/SCRATCH.md) stays available to the
 * ports where code size allows it (ZX Spectrum, C64, C16).
 */
#include "rt_scratch.h"

long rt_scratch_capacity(void)
{
    return -1;
}

long rt_scratch_store(const rt_memory *mem, const rt_journal *j)
{
    (void)mem;
    (void)j;
    return -1;
}

long rt_scratch_restore(rt_memory *mem, rt_journal *j)
{
    (void)mem;
    (void)j;
    return -1;
}
