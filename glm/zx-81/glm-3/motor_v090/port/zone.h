/* zone.h - the persistent memory zone above the image end (v0.9.0).
 *
 * The user's request: keep the "memory bits", new words, user profiles
 * and reminders in a protected area above RAMTOP, save it at the end of
 * a conversation with a routine that saves ONLY this data, and load it
 * back together with the base knowledge later.
 *
 * The zone is plain RAM at 0x7E50-0x7EEF (152 bytes used):
 *   - ABOVE every image end (E_LINE max 0x7E1A) and above the VARS-end
 *     marker, so NO ROM LOAD/SAVE of program blocks ever touches it;
 *   - BELOW the machine stack reserve (SP starts at 0x7FFC, ROM tape
 *     I/O needs ~100 B of stack), so the stack never walks into it;
 *   - it survives topic block swaps AND whole-program /save reloads,
 *     and even the cold-boot image load (which stops at 0x7E19).
 * Only a power cycle loses it; /memsave puts it on the tape as the
 * raw block "RTMEM16" (ROM OUT-BYTE pulses) to survive that too.
 */
#ifndef ZONE_H
#define ZONE_H

#include "rt_types.h"

#define ZONE_ADDR   0x7E20
#define ZONE_LEN    152        /* payload bytes incl. checksum */

/* offsets inside the zone */
#define Z_MAGIC     0          /* 'R','T','Z' */
#define Z_VER       3          /* = 1 */
#define Z_FLAGS     4          /* bit0: topic suggestion on; bits4-7: users */
#define Z_FACTS_N   5
#define Z_REM_N     6
#define Z_USER      7          /* active user 0..2 */
#define Z_AINAME    8          /* 8 chars, ' '-padded */
#define Z_PROFILE   16         /* owner: name8 gender year stamp2 hour min mo day */
#define Z_GUESTS    40         /* 2 x [name8 gender year] */
#define Z_FACTS     60         /* 4 x [key8 val14] */
#define Z_REMS      148        /* 2 x [hour min text9] */
#define Z_XOR       151

#define Z_FACT_MAX  4
#define Z_REM_MAX   2
#define Z_USER_MAX  3

#define Z_F_SUGGEST 0x01       /* topic suggestion Y/N prompts */
#define Z_F_TURBO   0x02       /* real-hardware turbo tape speed */

/* --- API (zone.c) --- */
int  zone_valid(void);                 /* magic + xor ok */
void zone_init(const char *ainame);    /* defaults, keeps nothing */
void zone_fix(void);                   /* repair magic/xor in place */
rt_u8 zone_flags(void);
void zone_set_flag(rt_u8 bit, int on);

const char *zone_ainame(void);         /* 8-char buffer, not NUL-terminated */
void zone_set_ainame(const char *s);

/* owner/guest profile: name 8, gender 'm'/'f', year 2000-based byte,
 * stamp = days since 2000 (BE), hour/min, month, day */
void zone_profile_get(rt_u8 *p);       /* copies 24 bytes out */
void zone_profile_set(const rt_u8 *p);

const char *zone_user_name(int i);     /* 0 = owner slot */
int  zone_user_set(int i, const char *name, char gender, int year);
int  zone_active(void);                /* the active user index */
void zone_set_active(int i);
int  zone_rem_count(void);

/* learned facts: key IS value */
int  zone_fact_add(const char *key, const char *val);   /* 0 ok, -1 full */
int  zone_fact_find(const char *hay);  /* index or -1; substring match */
const char *zone_fact_key(int i);
const char *zone_fact_val(int i);
void zone_fact_drop(int i);            /* clear slot i */

/* reminders */
int  zone_rem_add(int h, int m, const char *text);      /* 0 ok, -1 full */
int  zone_rem_due(int h, int m);       /* index or -1 */
const char *zone_rem_text(int i);
void zone_rem_clear(int i);

/* the RTMEM16 tape block (ROM OUT-BYTE / IN-BYTE primitives) */
int  zone_tape_save(void);             /* 1 ok, 0 aborted */
int  zone_tape_load(void);             /* 1 ok, 0 no signal / wrong name */

/* real-hardware turbo tape: pokes the ROM's own pulse-width constants
 * (TX $032C/$0335, RX $0387/$0399 - byte-verified against the ROM) to
 * about double speed, and back. OFF by default: the emulator plays
 * T81 blocks at standard timing, and a fast block would then fail. */
void zone_tape_speed(int fast);

#endif /* ZONE_H */
