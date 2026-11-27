/* app16.c - retro-tinyllm 16K v0.9.0 (GLM build): the chat REPL.
 *
 * v0.9.0 (the user's spec, all English):
 * - STATUS ROW: D-file row 7 (the free upper-third tier) is a live
 *   status strip: the last 31 emitted characters tick through it and a
 *   spinner glyph spins at the right edge while the model runs (plain
 *   glyphs 0x00-0x3F and inverse 0x80-0xBF only, never 0x0B - the user's
 *   display-safety rules). The silent reasoning pass writes its draft
 *   THERE, so the "thinking bar" shows the thoughts.
 * - PERSISTENT ZONE (zone.c): 152 B of plain RAM at 0x7E50-0x7EEF, above
 *   every image end and below the stack reserve: AI name, owner+guest
 *   profiles, learned facts (key=value), reminders, flag bits. Survives
 *   topic swaps, program saves/reloads and the cold boot. /memsave hands
 *   it to the tape as the raw "RTMEM16" block (ROM OUT-BYTE pulses);
 *   the boot offers to load it back (Y/N) before the base block.
 * - TOPIC SUGGESTION: the input line is scanned against the 13 cassette
 *   packs' keywords; on a hit the motor asks "LOAD THE <NAME> PACK?
 *   (Y/N)" - Y pokes line 2's LOAD name and signals the handoff (the
 *   ROM loads the block), N answers "SORRY, NO MORE INFORMATION IS
 *   AVAILABLE ON THIS." A loaded pack overwrites the previous one,
 *   exactly like the v0.6.5 /topic.
 * - MATH, COLORS, SORT: two-operand arithmetic (plus/minus/times/
 *   divided), a basic color-mixing table (blue+yellow=green ...), and
 *   /sort alphabetizes comma-separated words.
 * - USERS: /user lists or switches the owner+2 guest profiles, each
 *   with name/gender/year; the prompt shows the active user. /name
 *   renames the AI (stored in the zone, default PICO).
 * - REMINDERS: /remind HH MM text stores up to 2; the FRAMES clock
 *   (boot time + elapsed minutes) checks them on every prompt and
 *   prints BEEP! when due. /time HH MM resets the clock.
 * - IDLE: after ~10 minutes without a key the motor asks something.
 * - The session state (72 B: hist/seed/temp/reason/events) still lives
 *   packed in D-file rows 0-2 - identical layout to v0.5.4/v0.6.5, so
 *   topic swaps keep it. Rows 3-6 = the scrollback ring (128 cells).
 *
 * Coding style: sccz80/sdcc-safe C89, 8/16-bit math, short strings.
 */
#include <string.h>
#include <stddef.h>
#include "rt_hal.h"
#include "rt_config.h"
#include "rt_charset.h"
#include "rt_model.h"
#include "rt_chat.h"
#include "rt_engine.h"
#include "zone.h"

/* ---- layout constants ---- */
#define MSIZE 1030              /* the class-G blob: fixed layout */
#define NTOPICS 13              /* chainable topic packs (RT-TUDOM..) */

/* ---- state v2: 72 bytes packed 3 -> 4 into 96 cells (rows 0-2) ---- */
#define ST_CELLS 96
#define ST_BYTES 72
/* app-level key codes the HAL folds shifted keys into */
#define K_PAGEUP   0x1E    /* SHIFT+5 */
#define K_PAGEDOWN 0x1F    /* SHIFT+0 */
#define K_RUBOUT   0x12    /* SHIFT+2: backspace mid-line, temp 2 on empty */
#define K_TEMP1    0x11    /* SHIFT+1 */
#define K_TEMP3    0x13    /* SHIFT+3 */
#define K_TEMP4    0x14    /* SHIFT+4 */
#define K_REASON   '"'     /* SHIFT+9 = the quote key on an empty line */

static rt_model model;
static rt_chat chat;
static rt_u16 model_addr;      /* where the magic scan found the blob */
#define TAG_AT     (model_addr + MSIZE)
#define NAMTAB_AT  (model_addr + MSIZE + 12)
static rt_u16 namtab;          /* handed to the poke asm */
static rt_u8 b[ST_BYTES];

/* the status strip (row 7): a rolling ticker + the spinner cell */
static int tick_col;           /* next ticker cell 0..30 */
static int spin_ph;            /* spinner phase */

static rt_u8 topic_idx;        /* 0 = base, 1..13 = topic */
static rt_u8 pending;          /* topic requested via /topic */
static const char *topicnames[NTOPICS + 1] = {
    "BASE", "SCIENC", "HUNGAR", "HOBBY", "HEALTH", "WORK", "ART",
    "LEARNI", "OFFICE", "MOVIES", "PROGRA", "ASTRON",
    "ARTASC", "POETR"
};

/* the FRAMES clock: minutes since boot + the minute-of-day base */
static unsigned int f_last;    /* last FRAMES seen */
static unsigned int acc;       /* pending ticks */
static int elapsed_min;        /* minutes since boot */
static int base_h, base_m;     /* minute-of-day at boot */

/* ---- tiny printers ---- */

static void say(const char *s)
{
    while (*s)
        hal_putchar(*s++);
}

static void say_pad(const char *p, int n)
{
    int i;

    for (i = 0; i < n; i++)
        hal_putchar(p[i] ? p[i] : ' ');
}

static void say_int(int v)
{
    char t[6];
    int n = 0;

    if (v < 0) {
        hal_putchar('-');
        v = -v;
    }
    do {
        t[n++] = (char)('0' + v % 10);
        v /= 10;
    } while (v);
    while (n)
        hal_putchar(t[--n]);
}

/* ---- status strip: ticker + spinner + the upper-third comet ---- */

static void status_tick(char c)
{
    if (c == '\n')
        c = ' ';
    hal_status_char(tick_col, c);
    tick_col = (tick_col + 1) % 31;
    hal_spin_tick(spin_ph++);
}

static void status_spin(void)
{
    hal_spin_tick(spin_ph++);
}

/* ---- state pack/unpack: 72 bytes -> 96 cells of 6 bits ----
 * Hand-written Z80 (the C versions cost ~470 lines). Cells are the
 * D-file work rows 0-2: cell i = D_FILE+1+(i/32)*33+(i%32), every 32
 * cells followed by the row's $76 terminator, which this code SKIPS.
 * All written values are 0x00-0x3F (plain glyph codes only).
 * The b[] and namtab addresses reach the asm through fixed pointer
 * words at $7EF0/$7EF2 (the zone's slack bytes) - so the same inline
 * asm assembles under sccz80 AND zsdcc (no C-symbol references). */
#define BPTR  (*(unsigned int *)0x7EBF)
#define NTPTR (*(unsigned int *)0x7EC1)

static void pack_state(void)
{
#asm
    ld    hl,(0x400C)
    inc   hl              ; HL = the first cell of row 0
    ld    de,(0x7EBF)      ; DE = the source b[0..71]
    ld    a,3             ; 3 work rows
ps_row:
    ld    b,8             ; 8 groups of 3 -> 4 per row
    push  af
ps_grp:
    push  bc              ; the group counter
    ld    a,(de)
    ld    c,a             ; C = b0
    inc   de
    ld    a,(de)
    ld    b,a             ; B = b1
    inc   de
    ld    a,(de)
    inc   de
    push  af              ; b2 for cell2
    push  af              ; b2 for cell3
    ld    a,c             ; cell0 = b0 & 0x3F
    and   0x3F
    ld    (hl),a
    inc   hl
    ld    a,c             ; cell1 = (b0>>6) | ((b1&0F)<<2)
    and   0xC0
    rlca
    rlca
    ld    c,a
    ld    a,b
    and   0x0F
    add   a,a
    add   a,a
    or    c
    ld    (hl),a
    inc   hl
    ld    a,b             ; cell2 = ((b1>>4)&0x0F) | ((b2&3)<<4)
    and   0xF0
    rrca
    rrca
    rrca
    rrca
    ld    c,a
    pop   af              ; b2
    and   0x03
    add   a,a
    add   a,a
    add   a,a
    add   a,a
    or    c
    ld    (hl),a
    inc   hl
    pop   af              ; b2
    srl   a               ; cell3 = b2 >> 2
    srl   a
    ld    (hl),a
    inc   hl
    pop   bc
    djnz  ps_grp
    inc   hl              ; skip the row terminator (0x76)
    pop   af
    dec   a
    jr    nz,ps_row
    ret
#endasm
}

static void unpack_state(void)
{
#asm
    ld    hl,(0x400C)
    inc   hl              ; HL = the first cell of row 0 (the source)
    ld    de,(0x7EBF)      ; DE = the target b[0..71] - NEVER clobbered
    ld    a,3             ; 3 work rows
pu_row:
    ld    b,8             ; 8 groups per row
    push  af
pu_grp:
    push  bc              ; the group counter waits on the stack
    ld    a,(hl)          ; cell0
    inc   hl
    and   0x3F
    ld    c,a             ; C = cell0
    ld    a,(hl)          ; cell1
    inc   hl
    and   0x3F
    ld    b,a             ; B = cell1
    ld    a,(hl)          ; cell2
    inc   hl
    and   0x3F
    push  af              ; cell2 on the stack
    ld    a,(hl)          ; cell3
    inc   hl
    and   0x3F
    push  af              ; cell3 on the stack
    ; b0 = cell0 | (cell1&3)<<6
    ld    a,b
    and   0x03
    rrca
    rrca
    or    c
    ld    (de),a
    inc   de
    ; b1 = (cell1>>2)&0F | (cell2&0F)<<4
    ld    a,b
    and   0x3C
    rrca
    rrca
    ld    c,a
    pop   af              ; cell2
    and   0x0F
    add   a,a
    add   a,a
    add   a,a
    add   a,a
    or    c
    ld    (de),a
    inc   de
    ; b2 = (cell2>>4)&3 | cell3<<2
    pop   af              ; cell2 again
    and   0x30
    rrca
    rrca
    rrca
    rrca
    ld    c,a
    pop   af              ; cell3
    add   a,a
    add   a,a
    or    c
    ld    (de),a
    inc   de
    pop   bc
    djnz  pu_grp
    inc   hl              ; skip the row terminator (0x76)
    pop   af
    dec   a
    jr    nz,pu_row
    ret
#endasm
}

static int state_valid(void)
{
    rt_u8 x = 0;
    int i;

    if (b[0] != 'R' || b[1] != 'T' || b[2] != '2')
        return 0;
    for (i = 0; i < ST_BYTES - 1; i++)
        x = (rt_u8)(x ^ b[i]);
    return x == b[ST_BYTES - 1];
}

static void state_apply(void)
{
    int i;

    for (i = 0; i < RT_MAX_CTX; i++)
        chat.hist[i] = b[18 + i] < RT_CHARSET_LEN ? b[18 + i] : 1;
    chat.hist_n = b[26] > RT_MAX_CTX ? RT_MAX_CTX : b[26];
    chat.seed = (rt_u32)b[27] | ((rt_u32)b[28] << 8);
    chat.temp_sh = b[33] < 1 ? 1 : b[33] > 4 ? 3 : b[33] - 1;
    topic_idx = b[31] > NTOPICS ? 0 : b[31];
    pending = b[32] > NTOPICS ? 0 : b[32];
}

/* ---- model finder: the "RTLM" magic scan + checksum ---- */

static int model_find(void)
{
    rt_u16 a, lo = 0x4090, hi = 0x7AFF;

    for (a = hi; a >= lo; a--) {
        if (*(rt_u8 *)a == 'R' && *(rt_u8 *)(a + 1) == 'T' &&
            *(rt_u8 *)(a + 2) == 'L' && *(rt_u8 *)(a + 3) == 'M') {
            if (rt_model_load(&model, (const rt_u8 *)a,
                              RT_APP_MODEL_MAX) == 0) {
                model_addr = a;
                namtab = a + MSIZE + 12;
                NTPTR = namtab;      /* for the poke asm */
                return 1;
            }
        }
    }
    return 0;
}

/* ---- memory events ---- */

static int match(const char *s, const char *w)
{
    int n = 0, i;

    while (w[n])
        n++;
    for (;;) {
        for (i = 0; i < n; i++)
            if (s[i] != w[i])
                goto next;
        if (!s[n] || s[n] == ' ' || s[n] == ',' || s[n] == '.' ||
            s[n] == '?' || s[n] == '!')
            return 1;
next:
        while (*s && *s != ' ')
            s++;
        if (!*s)
            return 0;
        s++;
    }
}

/* ---- LOAD-name poke: the table address comes from the finder ---- */

static void poke_load_name(rt_u8 topic)
{
#asm
    ld    hl,2
    add   hl,sp
    ld    a,(hl)          ; topic number
    ld    hl,(0x7EC1)      ; the name table (the C stored the address)
    ld    c,a
    ld    a,(hl)          ; magic
    cp    0xA1
    ret   nz
    inc   hl
    ld    a,(hl)          ; count
    cp    c
    ret   c               ; topic > count: leave line 2 untouched
    dec   c
    ld    b,0x00
    ld    a,c
    add   a,a
    add   a,a
    add   a,a             ; (topic-1)*8
    ld    c,a
    inc   hl              ; first name byte
    add   hl,bc           ; hl = names + (topic-1)*8
    ex    de,hl           ; de = the source
    ld    hl,(0x407F)      ; line-1 body length
    ld    bc,0x4085
    add   hl,bc           ; hl = the first body byte of line 2
    ld    b,0x20
pkn2:
    ld    a,(hl)
    cp    0xEF             ; the LOAD token
    jr    z,pkn3
    inc   hl
    djnz  pkn2
    ret                   ; no LOAD in line 2: leave it untouched
pkn3:
    inc   hl              ; skip the quote: hl = the 8-char slot
    ld    b,0x08
pkn1:
    ld    a,(de)
    ld    (hl),a
    inc   hl
    inc   de
    djnz  pkn1
    ret
#endasm
}

static void emit(char c, void *user)
{
    (void)user;
    hal_putchar(c);
    status_tick(c);
}

/* slash-command compare without the string library: line = "/xyz...",
 * cmd = "xyz" */
static int eq_cmd(const char *line, const char *cmd)
{
    int i = 1;

    while (*cmd) {
        if (line[i] != *cmd)
            return 0;
        i++;
        cmd++;
    }
    return line[i] == 0 || line[i] == ' ';
}

/* typo-tolerant command compare: at most 1 edit inside the word */
static int fuzzy_cmd(const char *s, const char *cmd)
{
    int i;

    if (s[0] != cmd[0])
        return 0;
    for (i = 1; cmd[i]; i++)
        if (s[i] != cmd[i] && s[i] != cmd[i + 1] &&
            cmd[i + 1] != 0)
            return 0;
    return 1;
}

/* the reasoning pass 1: greedy draft, discarded visually, but the
 * draft characters tick through the status strip (the thinking bar) */
static void silent_emit(char c, void *user)
{
    (void)user;
    status_tick(c);
}

/* ---- the clock: FRAMES (0x4034, 50 Hz) -> minutes ---- */

#if !RTV9_SMALL
static void clock_now(int *h, int *m)
{
    unsigned char *f = (unsigned char *)0x4034;
    unsigned v = (unsigned)(f[0] | (f[1] << 8));
    int t;

    acc += (unsigned)(v - f_last);
    f_last = v;
    while (acc >= 3000) {
        acc -= 3000;
        elapsed_min++;
    }
    t = base_h * 60 + base_m + elapsed_min;
    *h = (t / 60) % 24;
    *m = t % 60;
}

static void clock_set(int h, int m)
{
    unsigned char *f = (unsigned char *)0x4034;

    base_h = h;
    base_m = m;
    elapsed_min = 0;
    acc = 0;
    f_last = (unsigned)(f[0] | (f[1] << 8));
}
#endif


/* ---- reminders: checked on every prompt ---- */

#if !RTV9_SMALL
static void reminders(void)
{
    int h, m, i;

    clock_now(&h, &m);
    i = zone_rem_due(h, m);
    if (i >= 0) {
        say("\nbeep! ");
        say_int(h);
        say(":");
        if (m < 10)
            say("0");
        say_int(m);
        say(" - ");
        say(zone_rem_text(i));
        say("\n");
        zone_rem_clear(i);
    }
}
#endif


/* scan the next word starting at p; returns its length (0 = none) */
static int wordlen(const char *p)
{
    int n = 0;

    while (p[n] && p[n] != ' ')
        n++;
    return n;
}

#if !RTV9_SMALL
static int scan_int(const char *s, int *len)
{
    int v = 0, n = 0;

    while (s[n] >= '0' && s[n] <= '9') {
        v = v * 10 + s[n] - '0';
        n++;
    }
    *len = n;
    return n ? v : -1;
}

/* /remind hh:mm text   (or /remind hh mm text) */
static void do_remind(const char *s)
{
    int hh, mm, n1, n2 = 0;
    const char *p = s;
    const char *text;

    while (*p == ' ')
        p++;
    hh = scan_int(p, &n1);
    if (n1 == 0) {
        say("usage: /remind hh:mm text\n");
        return;
    }
    p += n1;
    if (*p == ':')
        p++;
    else if (*p == ' ')
        p++;
    mm = scan_int(p, &n2);
    if (mm < 0) {
        say("usage: /remind hh:mm text\n");
        return;
    }
    p += n2;
    while (*p == ' ')
        p++;
    text = p;
    if (hh > 23 || mm > 59 || !*text) {
        say("usage: /remind hh:mm text\n");
        return;
    }
    if (zone_rem_add(hh, mm, text) == 0)
        say("reminder stored.\n");
    else
        say("no free reminder slot.\n");
}
#endif


/* ---- input line with the empty-line switches + idle check ---- */

static char line[44];
static int lastkey_min;        /* the minute the last key arrived */

static int getline(void)
{
    int n = 0, c;
#if !RTV9_SMALL
    int hd, md;
#endif

    for (;;) {
        c = hal_getchar();
#if !RTV9_SMALL
        clock_now(&hd, &md);
        if (c < 0) {
            if (elapsed_min - lastkey_min >= 10) {
                say("\nstill there?\n");
                lastkey_min = elapsed_min;
            }
            continue;
        }
        lastkey_min = elapsed_min;
#endif
        if (c < 0)
            continue;
        if (c == '\n' || c == '\r') {
            line[n] = 0;
            return n;
        }
        if (n == 0) {
            if (c >= K_TEMP1 && c <= K_TEMP4) {
                b[33] = (rt_u8)(c - K_TEMP1 + 1);
                if (b[33] > 4)
                    b[33] = 4;
                chat.temp_sh = b[33] - 1;
                say("temperature: ");
                say_int(b[33]);
                say("\n");
                continue;
            }
            if (c == K_REASON) {
                b[34] = b[34] ? 0 : 1;
                say(b[34] ? "thinking mode on\n" : "quick replies\n");
                continue;
            }
        }
        if (c == K_RUBOUT) {
            if (n) {
                n--;
                hal_putchar(8);
            }
            continue;
        }
        if (c < ' ' || c > 0x7F)
            continue;
        if (c >= 'A' && c <= 'Z')
            c += 32;
        if (n < 40)
            line[n++] = (char)c;
        hal_putchar(c);
    }
}

/* ---- the generation: optional greedy draft, then the reply ---- */

static void gen_reply(void)
{
    tick_col = 0;
    if (b[34]) {
        chat.greedy = 1;          /* pass 1: the silent greedy draft */
        rt_chat_gen(&chat, &model, silent_emit, (void *)0);
        chat.greedy = 0;          /* pass 2: the visible sampled reply */
    }
    rt_chat_gen(&chat, &model, emit, (void *)0);
}

/* ---- topic suggestion: 1 = handoff armed, 0 = keep chatting ---- */

static const char *topic_keys[NTOPICS] = {
    "science atom lab",
    "hungarian hungary budapest",
    "hobby music game",
    "health doctor sick",
    "work job boss",
    "art paint drawing museum",
    "learn school exam",
    "letter email document paper",
    "movie film cinema actor",
    "program code basic",
    "star moon planet",
    "ascii smile face",
    "poem verse rhyme"
};

static int topic_hit(const char *s)
{
    int t;

    for (t = 0; t < NTOPICS; t++) {
        const char *k = topic_keys[t];

        while (*k) {
            char word[16];
            int wl = 0;

            while (*k == ' ')
                k++;
            while (*k && *k != ' ' && wl < 15)
                word[wl++] = *k++;
            word[wl] = 0;
            if (wl >= 4 && match(s, word))
                return t + 1;
        }
    }
    return 0;
}

static int suggest_topic(const char *s)
{
    int t, c;

    if (!(zone_flags() & Z_F_SUGGEST) || pending)
        return 0;
    t = topic_hit(s);
    if (!t || t == topic_idx)
        return 0;
    say("i also have the ");
    say(topicnames[t]);
    say(" pack? y/n\n");
    for (;;) {
        c = hal_getchar();
        if (c >= 'A' && c <= 'Z')
            c += 32;
        if (c == 'y' || c == 'n')
            break;
    }
    hal_putchar(c);
    hal_putchar('\n');
    if (c == 'n') {
        say("sorry, no more information is available on this.\n");
        return 0;
    }
    pending = (rt_u8)t;
    poke_load_name((rt_u8)t);
    pack_state();
    say("rewind to ");
    say(topicnames[t]);
    say(" + enter\n");
    return 1;
}

/* ---- math: [num] [op-word] [num] ---- */

static int tonum(const char *s, int *len)
{
    int v = 0, n = 0;

    while (s[n] >= '0' && s[n] <= '9') {
        v = v * 10 + s[n] - '0';
        if (v > 9999)
            v = 9999;
        n++;
    }
    *len = n;
    return n ? v : -1;
}

static int do_math(const char *s)
{
    int a = -1, c = -1, op = 0, n;
    const char *p = s;

    while (*p && (a < 0 || !op || c < 0)) {
        if (*p >= '0' && *p <= '9') {
            int v = tonum(p, &n);

            if (a < 0)
                a = v;
            else
                c = v;
            p += n;
            continue;
        }
        if (*p == '+')
            op = 1;
        else if (*p == '-')
            op = 2;
        else if (*p == '*' || *p == 'x')
            op = 3;
        else if (*p == '/')
            op = 4;
        else if (match(p, "plus"))
            op = 1;
        else if (match(p, "minus"))
            op = 2;
        else if (match(p, "times") || match(p, "multiply"))
            op = 3;
        else if (match(p, "divide") || match(p, "over"))
            op = 4;
        p++;
    }
    if (a < 0 || c < 0 || !op)
        return 0;
    say_int(a);
    hal_putchar(' ');
    if (op == 1) {
        say("plus ");
        say_int(a + c);
    } else if (op == 2) {
        say("minus ");
        say_int(a - c);
    } else if (op == 3) {
        long r = (long)a * (long)c;

        say("times ");
        if (r > 32767)
            say("too big");
        else
            say_int((int)r);
    } else {
        say("div ");
        if (c == 0)
            say("?0");
        else
            say_int(a / c);
    }
    say("\n");
    return 1;
}

/* ---- color mixing: blue+yellow=green and friends ---- */

static const char *colnames[6] = {"red", "blue", "yellow",
                                  "green", "white", "black"};
/* unordered pairs: {color a, color b, result} */
static const char *mixres[8] = {"purple", "green", "orange", "pink",
                                "cyan", "grey", "brown", "lime"};
static const rt_u8 mixpair[16] = {
    0, 1,   /* red+blue    = purple */
    1, 2,   /* blue+yellow = green */
    0, 2,   /* red+yellow  = orange */
    0, 4,   /* red+white   = pink */
    1, 3,   /* blue+green  = cyan */
    5, 4,   /* black+white = grey */
    0, 3,   /* red+green   = brown */
    2, 3    /* yellow+green= lime */
};

static int do_colors(const char *s)
{
    int got[6], n = 0, i, j, k;

    if (!match(s, "mix") && !match(s, "combine") &&
        !match(s, "together") && !match(s, "make"))
        return 0;
    for (i = 0; i < 6; i++) {
        got[i] = match(s, colnames[i]) ? 1 : 0;
        if (got[i])
            n++;
    }
    if (n != 2)
        return 0;
    for (k = 0; k < 16; k += 2) {
        i = mixpair[k];
        j = mixpair[k + 1];
        if (got[i] && got[j]) {
            say(colnames[i]);
            say(" and ");
            say(colnames[j]);
            say(" make ");
            say(mixres[k / 2]);
            say("\n");
            return 1;
        }
    }
    say("i only know a few mixes - try red, blue, yellow,\n");
    say("green, white or black.\n");
    return 1;
}

/* ---- /user: owner + guests ---- */

#if !RTV9_SMALL
static void user_show(int active)
{
    int i;

    for (i = 0; i < Z_USER_MAX; i++) {
        const char *p = zone_user_name(i);

        say_int(i);
        say(": ");
        say_pad(p, 8);
        if (i == active)
            say(" *active*");
        say("\n");
    }
}
#endif


/* ---- /info: the available data ---- */

#if !RTV9_SMALL
static void info_show(void)
{
    int h, m, i, nf = 0;

    say("pico-ai v0.9.0\ntopic: ");
    say(topicnames[topic_idx]);
    say(" vocab 48\n");
    for (i = 0; i < Z_FACT_MAX; i++)
        if (zone_fact_key(i)[0])
            nf++;
    say_int(nf);
    say("/4 facts, ");
    say_int(zone_rem_count());
    say("/2 reminders, zone ");
    say(zone_valid() ? "ok" : "bad");
    say("\nsuggestion: ");
    say((zone_flags() & Z_F_SUGGEST) ? "on" : "off");
    say("\n");
    clock_now(&h, &m);
    say("clock: ");
    say_int(h);
    say(":");
    if (m < 10)
        say("0");
    say_int(m);
    say("\n");
}
#endif


/* ---- the main loop ---- */

static void state_default(void)
{
    int i;

    for (i = 0; i < ST_BYTES; i++)
        b[i] = 0;
    b[0] = 'R';
    b[1] = 'T';
    b[2] = '2';
    b[3] = 2;
    b[33] = 2;
}

int main(void)
{
    int i;
    char cmd;

    /* v0.5.4: same display re-assert as the boot (see boot16.c): after
     * the ROM's LOAD (multiload chain) or a quickload entry the NMI
     * display must be re-enabled, else only getk()'s keyboard scans
     * regenerate the picture. */
#asm
    ; -IXIY swap: assembles as LD IY,4000h = the ROM sysvar base
    ld ix, 0x4000
    call 0x0F2B           ; SLOW: enable the continuous NMI display
#endasm

    rt_charset_init();

    BPTR = (unsigned int)b;    /* for the pack/unpack asm */

    unpack_state();
    if (state_valid()) {
        if (b[56] == 2) {
            b[56] = 0;
            pack_state();
            return 2;    /* the /save handoff: ROM SAVEs the program */
        }
        state_apply();
    } else {
        state_default();
    }

    if (model_find() == 0) {
        say("no model! dfile=");
        say_int((int)(*(rt_u16 *)0x400C));
        say("\nbad cassette\n");
        return 0;
    }
    {   /* the block's own tag = which pack is really in the machine */
        rt_u8 tag = *(rt_u8 *)TAG_AT;

        if (tag > NTOPICS)
            tag = 0;
        topic_idx = tag;
        b[31] = tag;
    }

    /* the zone: fresh RAM -> defaults; valid -> keep everything */
    if (!zone_valid())
        zone_init("PICO    ");
    {   /* the clock: the boot stored hour/min in the zone profile */
#if !RTV9_SMALL
        rt_u8 prof[24];

        zone_profile_get(prof);
        clock_set(prof[12], prof[13]);
#endif
    }

    tick_col = 0;
    say("pico-ai v0.9.0  /help\n");

    for (;;) {
        int n, h, m;

#if !RTV9_SMALL
        clock_now(&h, &m);
        reminders();
#endif
        (void)h; (void)m;
        {
            const char *p = zone_user_name(zone_active());

            if (p && p[0] != ' ') {
                say_pad(p, 8);
                say("> ");
            } else {
                say("you> ");
            }
        }
        status_spin();
        n = getline();
        say("\n");
        if (n == 0)
            continue;
        if (line[0] == '/') {
            cmd = line[1];
            if (fuzzy_cmd(line + 1, "help")) {
#if RTV9_SMALL
                say("/topic /save /memsave /new /quit\n");
                say("math: 2 plus 2\n");
#else
                say("/topic /save /memsave /new /quit\n");
                say("/learn /name /user /remind /info /time\n");
                say("shift 1-4 temp, 9 thinking\n");
#endif
            } else if (fuzzy_cmd(line + 1, "topic") &&
                       line[7] >= '1' && line[7] <= '9') {
                rt_u8 t = (rt_u8)(line[7] - '0');

                if (t > NTOPICS)
                    t = NTOPICS;
                pending = t;
                poke_load_name(t);
                pack_state();
                say("rewind to ");
                say(topicnames[t]);
                say(", enter.\n");
#asm
                ld    ix,0x4000
                call  0x0F2B           ; SLOW: display back for the handoff
#endasm
                return 1;
            } else if (fuzzy_cmd(line + 1, "topic")) {
                for (i = 1; i <= NTOPICS; i++) {
                    say_int(i);
                    say(" ");
                    say(topicnames[i]);
                    say("\n");
                }
            } else if (fuzzy_cmd(line + 1, "memsave")) {
                say("record! rtmem16...\n");
                if (zone_tape_save())
                    say("saved.\n");
                else
                    say("aborted\n");
                continue;
            } else if (fuzzy_cmd(line + 1, "save")) {
                pack_state();      /* the rows go to tape with the
                                      ROM's SAVE: the D-file sits
                                      inside $4009..VARS-end */
                b[56] = 2;
                pack_state();
                say("rewind to rtbase16, record.\n");
#asm
                ld    ix,0x4000
                call  0x0F2B
#endasm
                return 2;
            } else if (fuzzy_cmd(line + 1, "new")) {
                chat.hist_n = 0;
                b[26] = 0;
                pack_state();
                say("new chat.\n");
            } else if (fuzzy_cmd(line + 1, "name") && line[5] == ' ' &&
                       line[6] > ' ') {
                zone_set_ainame(line + 6);
                {
                    const char *p = zone_ainame();
                    int k;

                    say("i am ");
                    for (k = 0; k < 8 && p[k] != ' '; k++)
                        hal_putchar(p[k]);
                    say(" now.\n");
                }
            } else if (fuzzy_cmd(line + 1, "name")) {
                say("i am ");
                say_pad(zone_ainame(), 8);
                say(". /name <word> renames me.\n");
#if !RTV9_SMALL
            } else if (fuzzy_cmd(line + 1, "user")) {
                if (line[5] == ' ' && line[6] >= '0' &&
                    line[6] <= '2')
                    zone_set_active(line[6] - '0');
                user_show(zone_active());
            } else if (fuzzy_cmd(line + 1, "learn") && line[7]) {
                char key[9];
                int k;

                for (k = 0; k < 8 && line[7 + k] > ' '; k++)
                    key[k] = line[7 + k];
                key[k] = 0;
                zone_fact_add(key, line + 8 + k);
                say("learned: ");
                say(key);
                say(" = ");
                say(zone_fact_val(zone_fact_find(key)));
                say("\n");
            } else if (fuzzy_cmd(line + 1, "remind")) {
                do_remind(line + 8);
            } else if (fuzzy_cmd(line + 1, "time")) {
                int p = 6;
                int hh, mm, n1, n2;

                hh = scan_int(line + p, &n1);
                mm = -1;
                if (n1 && line[p + n1] == ':')
                    mm = scan_int(line + p + n1 + 1, &n2);
                if (hh >= 0 && mm >= 0 && hh < 24 && mm < 60) {
                    clock_set(hh, mm);
                    say("clock set.\n");
                } else {
                    say("usage: /time hh:mm\n");
                }
            } else if (fuzzy_cmd(line + 1, "info")) {
                info_show();
#endif
            } else if (fuzzy_cmd(line + 1, "quit")) {
                pack_state();
#asm
                ld    ix,0x4000
                call  0x0F2B
#endasm
                return 0;
            } else {
                say("??? /help\n");
            }
            continue;
        }
#if !RTV9_SMALL
        /* learned fact echo */
        i = zone_fact_find(line);
        if (i >= 0) {
            say("fact: ");
            say(zone_fact_key(i));
            say(" = ");
            say(zone_fact_val(i));
            say("\n");
        }
#endif
        if (do_math(line)) {
            pack_state();
            continue;
        }
        if (suggest_topic(line)) {
            /* the handoff is armed; return 1 so the ROM LOADs it */
#asm
            ld    ix,0x4000
            call  0x0F2B
#endasm
            return 1;
        }
        rt_chat_push(&chat, line);
        gen_reply();
        hal_putchar('\n');
        pack_state();
    }
}
