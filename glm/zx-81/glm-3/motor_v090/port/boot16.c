/* boot16.c - pico-ai v0.9.0 BOOT block: logo, guide, memory restore,
 * profile. English UI (the user's rule: everything in English).
 *
 * This is a SEPARATE small app (~2.5 KB, no model, no chat engine)
 * that occupies cassette block 1 (RTBOOT01). Flow:
 *
 *   1. draw the PICO-AI logo with plain display-safe characters
 *      (letters, '=', '.', '/' - the D-file holds only codes the ROM
 *      renders as real glyphs; never $76, never >= $40 without bit 7,
 *      never the quote glyph - the user's freeze rules)
 *   2. offer the short guide (Y/N)
 *   3. MEMORY RESTORE: if the persistent zone (0x7E50, see zone.c) is
 *      valid, offer "RESTORE SAVED MEMORY FROM TAPE? (Y/N)". Y runs
 *      zone_tape_load() - the raw RTMEM16 block right after the boot
 *      block on the cassette (the boot is motor-side: the ROM loader
 *      is never asked to load it, and a silent tape aborts cleanly).
 *      The zone holds the AI name, the profiles, the learned facts,
 *      the reminders and the flag bits - everything the user asked to
 *      persist above RAMTOP.
 *   4. PROFILE: asked ONLY when the zone has no owner name (fresh
 *      machine or empty zone): date, time, name, gender - and the AI's
 *      name (ENTER keeps the current one). The profile is stored in
 *      the zone AND packed into the D-file work rows 0-2 (the same
 *      'RT2' format the base block reads back).
 *   5. return 1, so BASIC executes
 *      2 IF USR 16514 = 1 THEN LOAD "RTBASE16"
 *      and the tape hands over to the base block
 *
 * The zone and the packed state survive the block swap because both
 * sit ABOVE every image end (the zone as plain RAM past the VARS-end
 * marker, the D-file at 0x7B00 with all topic images SHORT).
 */
#include <string.h>
#include <stddef.h>
#include "rt_hal.h"
#include "rt_config.h"
#include "zone.h"

/* ---- session state in the D-file work tier, rows 0-2 ----
 * 72 payload bytes packed 3 -> 4 into 96 cells of 6 bits:
 * 'R','T','2' magic, version, name[8], gender, year, stamp(2: days
 * since 2000), hour, min, hist[8], hist_n, seed(2), topic, pending,
 * temp, reason, events[10][2], evcount, save flag, xor checksum.
 * The BASE block unpacks the exact same layout. */
#define ST_CELLS 96
#define ST_BYTES 72

static char bname[9];
static char bgen;        /* 'm' / 'f' / 0 */
static int byear, bmo, bday, bhour, bmin;
static unsigned int bstamp;    /* days since 2000-01-01 */

/* ---- tiny printers ---- */

static void say(const char *s)
{
    while (*s)
        hal_putchar(*s++);
}

static void say_int(int v)
{
    char b[6];
    int n = 0;

    if (v < 0) {
        hal_putchar('-');
        v = -v;
    }
    do {
        b[n++] = (char)('0' + v % 10);
        v /= 10;
    } while (v);
    while (n)
        hal_putchar(b[--n]);
}

/* ---- input: read one line (max max-1 chars) ---- */

static void getline(char *buf, int max)
{
    int n = 0;

    for (;;) {
        int c = hal_getchar();

        if (c == -1)
            continue;
        if (c == '\n') {
            buf[n] = 0;
            return;
        }
        if (c < ' ' || c > 0x7F)
            continue;                 /* shifted keys, graphics */
        if (c >= 'A' && c <= 'Z')
            c += 32;                  /* the chat is lowercase */
        if (n < max - 1)
            buf[n++] = (char)c;
        hal_putchar(c);
    }
}

/* read a decimal number in [lo,hi], re-asking on garbage */
static int getnum(int lo, int hi)
{
    char buf[8];

    for (;;) {
        int v = 0, i;

        getline(buf, 6);
        for (i = 0; buf[i]; i++) {
            if (buf[i] < '0' || buf[i] > '9') {
                v = lo - 1;
                break;
            }
            v = v * 10 + buf[i] - '0';
        }
        if (v >= lo && v <= hi)
            return v;
        say("??? (");
        say_int(lo);
        say("-");
        say_int(hi);
        say(")\n");
    }
}

/* ---- the logo: plain display-safe chars only ---- */

static const char *logo[5] = {
    ".---. .---. .===. .---. .---.",
    ".=--. .---.  ===  .---. .---.",
    ".=--. .---.  ===  .---. .---.",
    ".--=. .---. ===   .---. .---.",
    ".=--.  ===  .===.  ===.  ===."
};

static void logo_draw(void)
{
    int i;

    for (i = 0; i < 3; i++)
        say("\n");
    for (i = 0; i < 5; i++) {
        say(logo[i]);
        say("\n");
    }
    say("      pico-ai 16k  v0.9.0\n");
    say("==============================\n");
}

/* ---- date helpers ---- */

static const char mdays[12] = {31, 28, 31, 30, 31, 30,
                               31, 31, 30, 31, 30, 31};

static int doy_calc(int y, int m, int d)
{
    int i, n = d;

    for (i = 0; i < m - 1; i++)
        n += mdays[i];
    if (m > 2 && ((y % 4 == 0 && y % 100 != 0) || y % 400 == 0))
        n++;
    return n;
}

/* ---- the guide ---- */

static void guide(void)
{
    say("\nHOW I WORK:\n");
    say("- type lowercase, press enter\n");
    say("- /help: all commands\n");
    say("- /topic N: load a knowledge pack from tape\n");
    say("- when a word hints at a pack, i ask: load it? (y/n)\n");
    say("- /memsave: my memory (your profile, new words,\n");
    say("  reminders) to tape as the RTMEM16 block\n");
    say("- /save: the whole program to tape (slow)\n");
    say("- /learn key is value: i remember facts\n");
    say("- /name /user /sort /remind /time /info\n");
    say("- the top rows are my context + a thinking bar\n\n");
}

/* ---- the profile pack: 3 bytes -> 4 cells of 6 bits ----
 * state[0..71]; cell2 carries b1 bits 4-7 (the same group packing
 * the base block's unpack_state uses). */

static rt_u8 buf[ST_BYTES];

static void pack_profile(void)
{
    int c;
    rt_u8 x = 0;

    for (c = 0; c < ST_BYTES; c++)
        buf[c] = 0;
    buf[0] = 'R';
    buf[1] = 'T';
    buf[2] = '2';
    buf[3] = 1;
    for (c = 0; c < 8 && bname[c]; c++)
        buf[4 + c] = (rt_u8)bname[c];
    buf[12] = (rt_u8)bgen;
    buf[13] = (rt_u8)(byear - 2000);
    buf[14] = (rt_u8)(bstamp >> 8);
    buf[15] = (rt_u8)(bstamp & 255);
    buf[16] = (rt_u8)bhour;
    buf[17] = (rt_u8)bmin;
    /* hist/seed/topic stay zero: the base block starts fresh */
    buf[55] = 0;                  /* evcount */
    buf[56] = 0;                  /* save flag */
    for (c = 0; c < ST_BYTES - 1; c++)
        x = (rt_u8)(x ^ buf[c]);
    buf[ST_BYTES - 1] = x;

    /* the SAME 3->4 group packing the base block uses (24 groups,
     * cells 0-95 = D-file work rows 0-2) */
    for (c = 0; c < 24; c++) {
        rt_u8 b0 = buf[c * 3], b1 = buf[c * 3 + 1], b2 = buf[c * 3 + 2];

        hal_scratch_put(c * 4 + 0, b0 & 0x3F);
        hal_scratch_put(c * 4 + 1,
                        (rt_u8)((b0 >> 6) | ((b1 & 0x0F) << 2)));
        hal_scratch_put(c * 4 + 2,
                        (rt_u8)(((b1 >> 4) & 0x0F) | ((b2 & 0x03) << 4)));
        hal_scratch_put(c * 4 + 3, b2 >> 2);
    }
}

/* ---- the zone profile (owner slot, 24 bytes: see zone.h) ---- */

static void zone_store_profile(void)
{
    rt_u8 p[24];
    const char *ain = zone_ainame();
    int i;

    for (i = 0; i < 24; i++)
        p[i] = 0;
    for (i = 0; i < 8 && bname[i]; i++)
        p[i] = (rt_u8)bname[i];
    p[8] = (rt_u8)bgen;
    p[9] = (rt_u8)(byear - 2000);
    p[10] = (rt_u8)(bstamp >> 8);
    p[11] = (rt_u8)(bstamp & 255);
    p[12] = (rt_u8)bhour;
    p[13] = (rt_u8)bmin;
    p[14] = (rt_u8)bmo;
    p[15] = (rt_u8)bday;
    /* keep the AI name the zone already carries (or PICO on first run) */
    for (i = 0; i < 8; i++)
        p[16 + i] = (rt_u8)ain[i];
    zone_profile_set(p);
}

int main(void)
{
    int i;
    rt_u8 prof[24];

    /* v0.5.4: re-assert the display after ANY entry path. The ROM's
     * tape LOAD (our multiload chain) runs with the display off (the
     * ZX81 loads with FAST), and a quickload may enter with IY unset,
     * so the crt0's early SLOW call alone is not enough: without this
     * the screen is only regenerated during getk()'s keyboard scans -
     * the "picture flashes on keypress" symptom. IY must be $4000 for
     * every ROM sysvar access (incl. the NMI display sweep itself). */
#asm
    ; -IXIY swap: assembles as LD IY,4000h = the ROM sysvar base
    ld ix, 0x4000
    call 0x0F2B           ; SLOW: enable the continuous NMI display
#endasm

    logo_draw();
    say("back again! guide? (y/n)\n");
    for (;;) {
        int c = hal_getchar();

        if (c == -1)
            continue;
        if (c >= 'A' && c <= 'Z')
            c += 32;
        if (c == 'y') {
            guide();
            break;
        }
        if (c == 'n')
            break;
    }

    /* --- the persistent zone: fresh RAM or restored --- */
    if (!zone_valid())
        zone_init("PICO    ");
    say("restore saved memory from tape? (y/n)\n");
    say("(the rtmem16 block, right after this one)\n");
    for (;;) {
        int c = hal_getchar();

        if (c == -1)
            continue;
        if (c >= 'A' && c <= 'Z')
            c += 32;
        if (c == 'y') {
            say("press play on the rtmem16 block...\n");
            if (zone_tape_load())
                say("memory restored.\n");
            else
                say("no rtmem16 on tape (ok, kept ram).\n");
            break;
        }
        if (c == 'n')
            break;
    }

    /* --- the profile: asked only when the zone has no owner --- */
    zone_profile_get(prof);
    if (prof[0] == ' ' || prof[0] == 0) {
        say("first run: lets set you up.\n");
        say("date: year? ");
        byear = getnum(2000, 2099);
        say("month (1-12)? ");
        bmo = getnum(1, 12);
        say("day (1-31)? ");
        bday = getnum(1, 31);
        say("time: hour (0-23)? ");
        bhour = getnum(0, 23);
        say("minute (0-59)? ");
        bmin = getnum(0, 59);
        say("your name? ");
        getline(bname, 9);
        say("gender (m/f)? ");
        for (;;) {
            int c = hal_getchar();

            if (c == -1)
                continue;
            if (c >= 'A' && c <= 'Z')
                c += 32;
            if (c == 'f' || c == 'm') {
                bgen = (char)c;
                hal_putchar(c);
                break;
            }
        }
        say("\nwhat is my name? (enter = pico)\n");
        {
            char an[9];

            getline(an, 9);
            if (an[0])
                zone_set_ainame(an);
        }
        bstamp = (unsigned int)((byear - 2000) * 365 + doy_calc(byear, bmo, bday));
        zone_store_profile();
        say("nice to meet you, ");
        for (i = 0; bname[i]; i++)
            hal_putchar(bname[i]);
        say("!\n");
    } else {
        /* restore the boot-facing fields from the zone profile */
        int y = 2000 + prof[9];
        int doy = 0;

        for (i = 0; i < prof[14] - 1; i++)
            doy += mdays[i];
        doy += prof[15];
        byear = y;
        bmo = prof[14];
        bday = prof[15];
        bgen = prof[8];
        bhour = prof[12];
        bmin = prof[13];
        bstamp = (unsigned int)((byear - 2000) * 365 + doy);
        for (i = 0; i < 8; i++)
            bname[i] = prof[i];
        bname[8] = 0;
        say("hello again, ");
        for (i = 0; bname[i] && bname[i] != ' '; i++)
            hal_putchar(bname[i]);
        say("!\n");
    }

    pack_profile();

    say("settings kept. loading the base now.\n");
    say("rewind the tape to the RTBASE16 block!\n");

    /* leave the D-file rows 0-2 packed; the base block reads them */
    return 1;      /* BASIC runs: 2 IF USR 16514 = 1 THEN LOAD "RTBASE16" */
}
