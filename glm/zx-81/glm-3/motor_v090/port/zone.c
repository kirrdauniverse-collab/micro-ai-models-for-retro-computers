/* zone.c - the persistent memory zone (see zone.h) + the raw RTMEM16
 * tape block over the ROM's own byte primitives.
 *
 * Tape block format ("RTMEM16"):
 *   ~4 s leader (BREAK-1 ($0F46) calls - the ROM SAVE's header shape;
 *     BREAK-1 only reads the BREAK key row and writes MODE/CDFLAG, it
 *     does NOT emit pulses, so the leader is a quiet gap like the ROM's)
 *   the name bytes as ZX81 display codes, the LAST byte with bit7 set
 *     (the ROM's inverted-name terminator: R T M E M 1 6)
 *   the 152 zone bytes, each via OUT-BYTE ($031E)
 * The load side waits for real pulse activity (~20 s window) BEFORE it
 * ever calls IN-BYTE ($034C), so a silent/stopped tape can not reach the
 * ROM's tape-timeout path (which resets the machine); then it matches
 * the name and copies the payload.
 *
 * Register safety (from the ROM listing):
 *   OUT-BYTE ($031E) clobbers A,B,C,E; HL,D preserved.
 *   IN-BYTE  ($034C) clobbers A,B,C;    HL,D,E preserved (PUSH/POP DE).
 *   BREAK-1  ($0F46) clobbers A,F only.
 *   SET-FAST ($02E7) HALTs until the NMI, then OUT ($FD) + RES 7,CDFLAG.
 *   SLOW     ($0F2B) SET 6,CDFLAG + JP $0207 (restarts the NMI display,
 *                     RETs back to the caller - IY must be $4000 first).
 * Both sides re-enable SLOW + IY=$4000 at the end (the v0.6.5/v0.8.1
 * lesson: never leave the machine in FAST with the NMI generator off).
 *
 * Fixed addresses (NO C symbols inside #asm - the block must assemble
 * under sccz80 and sdcc alike):
 *   0x7EB8..$7EEE  the 7 name-code bytes (written by namebuf_build)
 *   $7EEF         the load-side poll state (written by zone_tape_load)
 */
#include <string.h>
#include "zone.h"
#include "rt_hal.h"

static rt_u8 *z = (rt_u8 *)ZONE_ADDR;
#define NAMEBUF_ADDR 0x7EB8
#define EARPASS_ADDR 0x7EBF

/* ---- helpers ---- */

static void strncpy8(char *dst, const char *src, int len)
{
    int i;

    for (i = 0; i < len; i++)
        dst[i] = src[i] ? src[i] : ' ';
}

static rt_u8 xor_sum(void)
{
    rt_u8 x = 0;
    int i;

    for (i = 0; i < ZONE_LEN - 1; i++)
        x = (rt_u8)(x ^ z[i]);
    return x;
}

int zone_valid(void)
{
    if (z[Z_MAGIC] != 'R' || z[Z_MAGIC + 1] != 'T' || z[Z_MAGIC + 2] != 'Z')
        return 0;
    return xor_sum() == z[Z_XOR];
}

void zone_fix(void)
{
    z[Z_MAGIC] = 'R';
    z[Z_MAGIC + 1] = 'T';
    z[Z_MAGIC + 2] = 'Z';
    z[Z_VER] = 1;
    z[Z_XOR] = xor_sum();
}

void zone_init(const char *ainame)
{
    int i;

    for (i = 0; i < ZONE_LEN; i++)
        z[i] = 0;
    z[Z_FLAGS] = Z_F_SUGGEST;
    strncpy8((char *)z + Z_AINAME, ainame, 8);
    strncpy8((char *)z + Z_PROFILE, "        ", 8);
    strncpy8((char *)z + Z_GUESTS, "        ", 8);
    strncpy8((char *)z + Z_GUESTS + 10, "        ", 8);
    zone_fix();
}

rt_u8 zone_flags(void)
{
    return z[Z_FLAGS];
}

void zone_set_flag(rt_u8 bit, int on)
{
    if (on)
        z[Z_FLAGS] = (rt_u8)(z[Z_FLAGS] | bit);
    else
        z[Z_FLAGS] = (rt_u8)(z[Z_FLAGS] & ~bit);
}

const char *zone_ainame(void)
{
    return (const char *)z + Z_AINAME;
}

void zone_set_ainame(const char *s)
{
    strncpy8((char *)z + Z_AINAME, s, 8);
    zone_fix();
}

void zone_profile_get(rt_u8 *p)
{
    int i;

    for (i = 0; i < 24; i++)
        p[i] = z[Z_PROFILE + i];
}

void zone_profile_set(const rt_u8 *p)
{
    int i;

    for (i = 0; i < 24; i++)
        z[Z_PROFILE + i] = p[i];
    zone_fix();
}

const char *zone_user_name(int i)
{
    if (i == 0)
        return (const char *)z + Z_PROFILE;
    if (i >= 1 && i < Z_USER_MAX)
        return (const char *)z + Z_GUESTS + (i - 1) * 10;
    return 0;
}

#if !RTV9_SMALL
int zone_user_set(int i, const char *name, char gender, int year)
{
    char *slot;

    if (i < 1 || i >= Z_USER_MAX)
        return -1;
    slot = (char *)z + Z_GUESTS + (i - 1) * 10;
    strncpy8(slot, name, 8);
    slot[8] = (gender == 'f') ? 'f' : 'm';
    slot[9] = (rt_u8)(year - 2000);
    zone_fix();
    return 0;
}
#endif

int zone_active(void)
{
    return z[Z_USER] & 3;
}

void zone_set_active(int i)
{
    z[Z_USER] = (rt_u8)(i & 3);
    zone_fix();
}

int zone_rem_count(void)
{
    return z[Z_REM_N];
}

/* ---- facts ---- */

static char *fact_key(int i)
{
    return (char *)z + Z_FACTS + i * 22;
}

static char *fact_val(int i)
{
    return (char *)z + Z_FACTS + i * 22 + 8;
}

static int ci_hit(const char *hay, const char *needle)
{
    int i, j;

    for (i = 0; hay[i]; i++) {
        for (j = 0; needle[j]; j++) {
            char a = hay[i + j], b = needle[j];
            if (a >= 'A' && a <= 'Z')
                a += 32;
            if (b >= 'A' && b <= 'Z')
                b += 32;
            if (a != b)
                break;
        }
        if (!needle[j])
            return 1;
    }
    return 0;
}

int zone_fact_add(const char *key, const char *val)
{
    int i, slot = -1;

    for (i = 0; i < Z_FACT_MAX; i++)
        if (fact_key(i)[0] == 0) {
            slot = i;
            break;
        }
    if (slot < 0) {                /* full: shift out the oldest */
        for (i = 1; i < Z_FACT_MAX; i++) {
            strncpy8(fact_key(i - 1), fact_key(i), 8);
            strncpy8(fact_val(i - 1), fact_val(i), 14);
        }
        slot = Z_FACT_MAX - 1;
    }
    strncpy8(fact_key(slot), key, 8);
    fact_key(slot)[7] = 0;
    strncpy8(fact_val(slot), val, 14);
    fact_val(slot)[13] = 0;
    if (z[Z_FACTS_N] < Z_FACT_MAX)
        z[Z_FACTS_N]++;
    zone_fix();
    return 0;
}

int zone_fact_find(const char *hay)
{
    int i;

    for (i = 0; i < Z_FACT_MAX; i++)
        if (fact_key(i)[0] && ci_hit(hay, fact_key(i)))
            return i;
    return -1;
}

const char *zone_fact_key(int i)
{
    return fact_key(i);
}

const char *zone_fact_val(int i)
{
    return fact_val(i);
}

#if !RTV9_SMALL
void zone_fact_drop(int i)
{
    if (i < 0 || i >= Z_FACT_MAX)
        return;
    fact_key(i)[0] = 0;
    fact_val(i)[0] = 0;
    if (z[Z_FACTS_N])
        z[Z_FACTS_N]--;
    zone_fix();
}
#endif

/* ---- reminders ---- */

static char *rem_slot(int i)
{
    return (char *)z + Z_REMS + i * 11;
}

#if !RTV9_SMALL
int zone_rem_add(int h, int m, const char *text)
{
    int i, slot = -1;
    char *s;

    for (i = 0; i < Z_REM_MAX; i++) {
        if (rem_slot(i)[2] == 0) {
            slot = i;
            break;
        }
    }
    if (slot < 0)
        return -1;
    s = rem_slot(slot);
    s[0] = (rt_u8)h;
    s[1] = (rt_u8)m;
    strncpy8(s + 2, text, 9);
    s[10] = 0;
    z[Z_REM_N]++;
    zone_fix();
    return 0;
}

int zone_rem_due(int h, int m)
{
    int i;
    char *s;

    for (i = 0; i < Z_REM_MAX; i++) {
        s = rem_slot(i);
        if (s[2] && s[0] == h && s[1] == m)
            return i;
    }
    return -1;
}

const char *zone_rem_text(int i)
{
    return rem_slot(i) + 2;
}

void zone_rem_clear(int i)
{
    if (i < 0 || i >= Z_REM_MAX)
        return;
    rem_slot(i)[2] = 0;
    if (z[Z_REM_N])
        z[Z_REM_N]--;
    zone_fix();
}
#endif

/* ---- the RTMEM16 tape block ---- */

#if !RTV9_SMALL
void zone_tape_speed(int fast)
{
    /* TX: $032C = LD B,+23 (zero-bit pulses), $0335 = LD B,+1E (one-bit)
     * RX: $0387 = LD E,+94 (trailer window),  $0399 = CP +56 (threshold)
     * byte-verified against the ROM listing (see zone.h). */
    *((rt_u8 *)0x032C) = fast ? 0x11 : 0x23;
    *((rt_u8 *)0x0335) = fast ? 0x0D : 0x1E;
    *((rt_u8 *)0x0387) = fast ? 0x48 : 0x94;
    *((rt_u8 *)0x0399) = fast ? 0x2B : 0x56;
}
#endif

int zone_tape_save(void)
{
#asm
    ld     hl,0x7EB8
    ld     (hl),0x37                ; R T M E M 1 6 (display codes),
    inc    hl                      ; built here once - the C side
    ld     (hl),0x39                ; refreshes it too
    inc    hl
    ld     (hl),0x32
    inc    hl
    ld     (hl),0x2A
    inc    hl
    ld     (hl),0x32
    inc    hl
    ld     (hl),0x1D
    inc    hl
    ld     (hl),0xA2                ; last byte: bit7 = the terminator
    call   0x02E7                   ; SET-FAST: display off, FAST timing
    ld     de,0x0400                ; ~4 s leader (BREAK-1 is silent)
zs_head:
    ld     b,0x00
zs_dly:
    call   0x0F46                   ; BREAK-1: break key check only
    jr     nc,zs_break
    djnz   zs_dly
    dec    de
    ld     a,d
    or     e
    jr     nz,zs_head
    ld     hl,0x7EB8                ; the RTMEM16 name codes
    call   0x030B                   ; OUT-NAME: emits until bit7 byte
    ld     hl,0x7E20                ; ZONE_ADDR
    ld     d,152                   ; ZONE_LEN (D survives OUT-BYTE)
zs_data:
    call   0x031E                   ; OUT-BYTE: pulses out (HL)
    inc    hl
    dec    d
    jr     nz,zs_data
    ld     ix,0x4000                ; (-IXIY swap) IY = the sysvar base
    call   0x0F2B                   ; SLOW: display + NMI back on
    ld     hl,1
    ret
zs_break:
    ld     ix,0x4000
    call   0x0F2B
    ld     hl,0
    ret
#endasm
}

int zone_tape_load(void)
{
#asm
    ld     hl,0x7EB8
    ld     (hl),0x37                ; the name codes again
    inc    hl
    ld     (hl),0x39
    inc    hl
    ld     (hl),0x32
    inc    hl
    ld     (hl),0x2A
    inc    hl
    ld     (hl),0x32
    inc    hl
    ld     (hl),0x1D
    inc    hl
    ld     (hl),0xA2
    call   0x02E7                   ; SET-FAST
    ;; --- pulse pre-check: wait for REAL edge activity before we ever
    ;; call IN-BYTE (whose own timeout resets the machine). Poll the EAR
    ;; bit for changes; B=32 x DE=0xFFFF iterations of ~40T is ~22 s.
    ld     b,32
zl_outer:
    ld     de,0xFFFF
zl_poll:
    in     a,(0xFE)
    and    0x40
    ld     c,a
    in     a,(0xFE)
    and    0x40
    xor    c                       ; level changed = an edge
    jr     nz,zl_found
    dec    de
    ld     a,d
    or     e
    jr     nz,zl_poll
    djnz   zl_outer
    jr     zl_silent               ; 22 s, no edges: nothing on the tape
zl_found:
    ;; --- name match: IN-BYTE returns the byte in C
    ld     hl,0x7EB8
zl_name:
    call   0x034C
    ld     a,c
    xor    (hl)
    jr     nz,zl_wrong
    bit    7,(hl)
    inc    hl
    jr     z,zl_name
    ;; --- payload: 152 bytes into the zone
    ld     hl,0x7E20
    ld     de,152
zl_data:
    call   0x034C
    ld     a,c
    ld     (hl),a
    inc    hl
    dec    de
    ld     a,d
    or     e
    jr     nz,zl_data
    ld     ix,0x4000
    call   0x0F2B
    ld     hl,1
    ret
zl_wrong:
    ld     ix,0x4000
    call   0x0F2B
    ld     hl,0
    ret
zl_silent:
    ld     ix,0x4000
    call   0x0F2B
    ld     hl,0
    ret
#endasm
}
