#ifndef RT_TAPE_H
#define RT_TAPE_H

#include "rt_types.h"

/* RT-turbo tape protocol - a portable, timing-driven block format used on
 * every tape machine. One "pulse" is one half-wave: the time in
 * MICROSECONDS between two flux transitions. The HAL measures/produces
 * pulses; this module turns them into bytes.
 *
 *   pilot : >= 24 pulses of 1500us +-25%   (band 1125..1875)
 *   sync  : TWO pulses of 900us +-20%     (band  720..1080)
 *   header: u16 payload length, value-MSB-first bits
 *   data  : payload bytes, MSB first: 0 = 350us +-25% (262..437),
 *                                    1 = 700us +-25% (525..875)
 *   crc   : u16 CRC-16/CCITT (poly 0x1021, init 0xFFFF) of payload,
 *           value-MSB-first bits
 *   end   : optional pulse > 2100us (decoder ignores it)
 *
 * The pilot and sync bands are disjoint, and so are the two bit bands, so
 * no single pulse can be mistaken for another kind at any drift the
 * tolerances allow. pulse() == 0 means "no edge within timeout" and aborts
 * every state.
 *
 * Throughput: one bit per pulse, average ~525us -> ~1900 bit/s (~238 B/s),
 * roughly 2-4x the ZX Spectrum ROM loader and ~4x the C64 kernal.
 * A 28KB Class C model loads in ~2 minutes; the 7.5KB Class D in ~30s.
 */
#define RT_T_PILOT_US 1500
#define RT_T_SYNC_US   900
#define RT_T_ZERO_US   350
#define RT_T_ONE_US    700
#define RT_T_PILOT_MIN 24 /* decoder: need this many pilot pulses */

/* fn: wait edge, return us - no param list: sccz80 1.8 limitation */
typedef rt_u16 (*rt_pulse_fn)();
/* fn: emit one half-wave (u16 us) - no param list: sccz80 1.8 */
typedef void (*rt_pulse_out_fn)();

/* Read one block (after >=1 pilot). Returns payload length or negative:
 *  -1 no block / line noise, -2 overflow, -3 CRC error. */
long rt_tape_read_block(rt_u8 *buf, long maxlen, rt_pulse_fn pulse);

/* Write one block. Returns 0 or -1. */
int rt_tape_write_block(const rt_u8 *buf, long len, rt_pulse_out_fn out);

rt_u16 rt_crc16(const rt_u8 *p, long n);

#endif /* RT_TAPE_H */
