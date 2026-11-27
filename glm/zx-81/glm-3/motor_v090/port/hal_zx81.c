/* hal_zx81.c - Sinclair ZX81 16K HAL (z88dk 1.8, no stdio chain).
 *
 * 16K edition (v0.4): the engine, ONE class-E model blob and the
 * display file share a single 16K pack (see docs/T81_FORMAT.md):
 *
 *   0x4009   system variables (D_FILE=0x7B00, VARS=0x7E19, 16K RAMTOP)
 *   0x407D   line 1: 1 REM <engine code from 0x4082 = 16514>
 *   line 2   2 RAND USR VAL "16514"
 *   0x6900   model blob (RT_MODEL_BUF_ADDR, injected by t81build16.py)
 *   0x7B00   D-file (ABOVE every image end - topic loads keep it)
 *              rows 0-7  work area / scratch tier (256 x 6 bit cells)
 *                         row 0/1: live context window
 *                         rows 6-7: packed session state
 *              rows 8-23 chat console (own cursor + scroll)
 *   0x7E19   VARS 0x80 marker; stack at the 16K top ($7FFC)
 *
 * The crt0 boots SLOW (display on, FRAMES ticking - see zx81rt_crt0.asm);
 * getk() polls the ROM keyboard scan so typing works while the program
 * runs. No printf anywhere: the text layer writes glyphs straight into
 * the D-file, so the ROM's scroll can never touch our rows 0-7.
 */
#include <stdio.h>   /* getk() lives here in z88dk 1.8 (not in zx81.h!) */
#include <zx81.h>
#include "rt_hal.h"

/* --- console: ZX81 char codes in, ASCII out ---
 * Table-driven on purpose: sccz80 1.8 turns a switch into a long
 * compare chain (~550 bytes for these two maps); the tables cost 160
 * bytes of image data. The input table is the exact inverse of the
 * output table below (the v0.3 input switch had drifted from it:
 * e.g. key 0x05 rendered as '?' but decoded as '('). ZX81 letters are
 * uppercase glyphs; the chat folds them to lowercase. */
static const signed char ZX81_TO_ASCII[64] = {
    /* v0.5: the exact inverse of the corrected ASCII_TO_ZX81 table
     * below - every code from the ROM K-UNSHIFT/K-SHIFT tables
     * ($007E/$00A5). The v0.3-era table had drifted badly: no comma,
     * no slash, no period, '$' sat at 0x10. Keys 0x01-0x0A are the
     * graphics codes (no ASCII), 0x0C is the pound glyph. */
    /* 0x00 */ ' ',  -1,   -1,   -1,   -1,   -1,   -1,   -1,
    /* 0x08 */ -1,   -1,   -1,   '"',  -1,   '$',  ':',  '?',
    /* 0x10 */ '(',  ')',  '>',  '<',  '=',  '+',  '-',  '*',
    /* 0x18 */ '/',  ';',  ',',  '.',  '0', '1', '2', '3',
    /* 0x20 */ '4', '5', '6', '7', '8', '9', 'a', 'b',
    /* 0x28 */ 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j',
    /* 0x30 */ 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r',
    /* 0x38 */ 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
};

static const rt_u8 ASCII_TO_ZX81[64] = {
    /* 0x20-0x5F; the 0x60-0x7F half mirrors it (v0.9.0 mask) */
    0x00, 0x00, 0x0B, 0x00, 0x0D, 0x00, 0x00, 0x00,
    0x10, 0x11, 0x17, 0x15, 0x1A, 0x16, 0x1B, 0x18,
    0x1C, 0x1D, 0x1E, 0x1F, 0x20, 0x21, 0x22, 0x23,
    0x24, 0x25, 0x0E, 0x19, 0x13, 0x14, 0x12, 0x0F,
    0x00, 0x26, 0x27, 0x28, 0x29, 0x2A, 0x2B, 0x2C,
    0x2D, 0x2E, 0x2F, 0x30, 0x31, 0x32, 0x33, 0x34,
    0x35, 0x36, 0x37, 0x38, 0x39, 0x3A, 0x3B, 0x3C,
    0x3D, 0x3E, 0x3F, 0x00, 0x00, 0x00, 0x00, 0x00,
};

static int zx81_ascii(int k)
{
    if (k == 0x76)
        return '\n'; /* NEWLINE key */
    /* v0.5: the shifted command keys fold to app-level codes so the
     * REPL can implement the temperature/reasoning/scroll keys:
     * SHIFT+1..4 -> 0x11..0x14, SHIFT+5/0 (arrows) -> 0x1E/0x1F,
     * SHIFT+2 (RUBOUT) -> 0x12 = backspace-marker for the app. */
    if (k == 0x70)
        return 0x1E;
    if (k == 0x71)
        return 0x1F;
    if (k == 0x73)
        return 0x14;
    if (k == 0x74)
        return 0x13;
    if (k == 0x75)
        return 0x11;
    if (k == 0x77)
        return 0x12;
    if (k < 0 || k > 63)
        return -1;
    return ZX81_TO_ASCII[k];
}

int hal_getchar(void)
{
    int k = getk();
    return k ? zx81_ascii(k) : -1;
}

int hal_kbhit(void)
{
    return getk() != 0;
}

/* --- text area rows 8-23; rows 0-7 belong to the scratch tier ---
 * Direct D-file output with own cursor and scroll: the ROM would scroll
 * all 24 lines and scramble the stored cells. Only real single-cell
 * glyph codes are written (0x00-0x3F); keyword/control codes and the
 * 0x76 (HALT) line terminator never appear. */
#define ZX81_TEXT_TOP 8
#define ZX81_TEXT_BOT 21  /* rows 22-23 = the ROM's lower screen (DF_SZ=2):
                              never written by us, the ROM owns them */

static int zx81_row = ZX81_TEXT_TOP;
static int zx81_col = 0;

static rt_u8 *zx81_line(int row)
{
    /* D_FILE system variable at 16396 (0x400C) - the REAL ZX81 map,
     * confirmed byte-exact against the z88dk appmake .P reference and
     * the user's memory dump. D_FILE points at the display file's
     * LEADING 0x76 newline byte; the first cell of row 0 is D_FILE+1
     * (= DF_CC right after CLS), then 32 cells + 0x76 per row. */
    return (rt_u8 *)(*(unsigned *)0x400C) + 1 + row * 33;
}

/* ZX81 glyph code for an ASCII char (unknown -> space). Letters and
 * digits map through the table above; 0x20-0x7F only, anything else is
 * a space. */
static rt_u8 zx81_code(int c)
{
    if (c < 0x20 || c > 0x7F)
        return 0x00;
    return ASCII_TO_ZX81[(c - 0x20) & 0x3F];
}

static void zx81_scr_scroll(void)
{
    /* hand-rolled: 11 rows of 33 bytes (cells + terminator together),
     * then the last console row cleared to spaces. ~60 B vs ~250 B of
     * C. Rows are D_FILE+1+33*row; TEXT_TOP=4, TEXT_BOT=15. */
#asm
    ld    hl,(0x400C)
    inc   hl
    ld    b,264
scr1:
    inc   hl
    djnz  scr1              ; HL = the first cell of row 8
    ld    a,13               ; rows 8-20 copy 9-21
scr_row:
    push  af
    push  hl                ; dst
    push  hl
    pop   de                ; DE = dst
    ld    bc,33
    add   hl,bc              ; HL = src = dst+33
    ld    bc,33
    ldir
    pop   hl                 ; restore dst
    ld    bc,33
    add   hl,bc              ; next dst
    pop   af
    dec   a
    jr    nz,scr_row
    ld    b,32               ; clear the last row (32 cells)
scr_cl:
    ld    (hl),0x00
    inc   hl
    djnz  scr_cl
#endasm
}

static void zx81_advance(void)
{
    zx81_col = 0;
    if (++zx81_row > ZX81_TEXT_BOT) {
        zx81_scr_scroll();
        zx81_row = ZX81_TEXT_BOT;
    }
}

void hal_putchar(int c)
{
    if (c == '\n') {
        zx81_advance();
        return;
    }
    if (zx81_col > 31)
        zx81_advance();
    zx81_line(zx81_row)[zx81_col] = zx81_code(c);
    zx81_col++;
}

void hal_flush(void)
{
}

void hal_msleep(long ms)
{
    /* FRAMES at 16436 (0x4034), 20 ms ticks. Needs SLOW mode: the
     * counter is bumped by the display NMI, which only runs with the
     * display on - in FAST mode this loop would never end. The crt0
     * boots SLOW (see zx81rt_crt0.asm). */
    unsigned char *f = (unsigned char *)0x4034;
    unsigned start = (unsigned)(f[0] | (f[1] << 8));
    unsigned want = (unsigned)(ms / 20);
    while ((unsigned)(f[0] | (f[1] << 8)) - start < want)
        ;
}

rt_u32 hal_entropy(void)
{
    /* FRAMES counter at 0x4034 (16436), 20 ms ticks */
    unsigned char *f = (unsigned char *)0x4034;
    return (rt_u32)f[0] | ((rt_u32)f[1] << 8) | 0x81000000UL;
}

/* v0.9.0: the tier plan (rows are 33 bytes: 32 cells + 0x76)
 *   rows 0-2   packed session state (96 cells, app16 pack_state)
 *   row  3     status row: spinner + thinking ticker
 *   rows 0-2   packed session state (96 cells, app16 pack_state)
 *   rows 4-15  chat console (own cursor + scroll)
 *   rows 16-17 the ROM's lower screen (DF_SZ=2): never written by us
 * v0.9.0 status-row rules (the user's display-safety rules): every byte
 * written must be a real glyph the ROM renders - 0x00-0x3F plain,
 * 0x80-0xBF inverse - never 0x0B (the quote glyph, banned by the user),
 * never 0x40-0x75, 0x76 (HALT!), 0x77-0x7F, 0xC0-0xFF (the freeze rule).
 */
#define ST_ROW0   7               /* the status row */
static rt_u8 status_safe(rt_u8 v)
{
    if (v == 0x0B)                 /* the banned quote glyph */
        return 0x00;
    if (v < 0x40)
        return v;                  /* plain glyphs */
    if (v >= 0x80 && v < 0xC0)
        return v;                  /* inverse glyphs */
    return 0x00;                   /* everything else: blank */
}

void hal_status_put(int i, rt_u8 code)
{
    if (i < 0 || i > 31)
        return;
    zx81_line(ST_ROW0)[i] = status_safe(code);
}

void hal_status_char(int i, char c)
{
    hal_status_put(i, zx81_code(c));
}

/* the spinner: 8 phases mixing plain and inverse glyphs (no quote) */
static const rt_u8 SPIN[8] = {
    0x80, 0x18, 0x00, 0x16, 0x80, 0x11, 0x00, 0x10
};

void hal_spin_tick(int phase)
{
    hal_status_put(31, SPIN[phase & 7]);
}

/* --- screen-RAM scratch tier: D-file rows 0-6, 224 cells x 6 bit ---
 * The ZX81 ROM renders every D-file cell, so only real glyph codes
 * (0x00-0x3F) may be stored; the app packs its session state 3 bytes
 * -> 4 cells. Rows 6-7 hold the packed state, rows 0-1 the live
 * context window (see app16.c). */
rt_u8 hal_scratch_get(long i)
{
    return zx81_line((int)(i / 32))[i % 32];
}

void hal_scratch_put(long i, rt_u8 v)
{
    /* v is a packed 6-bit value: always a legal, single-cell glyph */
    zx81_line((int)(i / 32))[i % 32] = v;
}

/* show one ASCII char in scratch cell i (row 0/1 context display) */
void hal_scratch_char(long i, char c)
{
    zx81_line((int)(i / 32))[i % 32] = zx81_code(c);
}

#if !RTV9_SMALL
void hal_panic(const char *msg)
{
    const char *p = msg;

    zx81_row = ZX81_TEXT_BOT;
    zx81_col = 0;
    while (*p)
        hal_putchar(*p++);
    hal_putchar('\n');
    for (;;) /* stay visible: no way back from a bad cassette */
        ;
}
#endif
