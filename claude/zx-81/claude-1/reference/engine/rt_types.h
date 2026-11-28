/* rt_types.h - C89-friendly integer types.
 *
 * Target compilers:
 *   cc65  (C64/C16, 6502):  int 16 bit, long 32 bit
 *   z88dk (Z80 targets):    int 16 bit, long 32 bit
 *   vbcc  (Amiga, 68000):   int 16/32, long 32 bit
 *   host gcc x86-64:        int 32 bit, long 64 bit
 *
 * Accumulators use the widest integer (long). Where an exact 32-bit width
 * matters (PRNG, checksums) code masks explicitly with RT_U32_MASK, so
 * results are identical on every port.
 */
#ifndef RT_TYPES_H
#define RT_TYPES_H

typedef signed char        rt_i8;
typedef unsigned char      rt_u8;
typedef short              rt_i16;
typedef unsigned short     rt_u16;
typedef long               rt_i32;
typedef unsigned long      rt_u32;

#define RT_U32_MASK 0xFFFFFFFFUL

#endif /* RT_TYPES_H */
