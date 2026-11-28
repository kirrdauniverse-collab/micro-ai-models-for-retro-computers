/* app16.c - retro-tinyllm 16K ZX81 edition: minimal chat REPL.
 *
 * The 48K build (v0.3.x) carried the full portable app - teachable
 * memory, journal, clock, router, tape manifest - which alone was ~25 KB
 * of Z80. One 16K pack cannot pay that, so this port keeps the neural
 * core (model parse + forward pass + sampling + generation) plus a
 * small command shell, and stores the session state in the D-file
 * scratch tier (rows 0-7, see hal_zx81.c): the rolling context window,
 * the PRNG seed and the active topic survive a topic-cassette swap.
 *
 * Topic switching works per the EO81 convention: every topic .P is a
 * complete image with the SAME engine at the same addresses and its own
 * model at RT_MODEL_BUF_ADDR; the D-file lives ABOVE the image end at a
 * fixed 0x7B00, so loading a topic image leaves the scratch tier - and
 * the machine stack - untouched. /topic prints which cassette to load.
 *
 * Coding style note: sccz80 1.8 emits ~10 bytes per statement and calls
 * the 32-bit library for variable shifts, so this file sticks to 8-bit
 * arithmetic and short strings on purpose.
 */
#include <string.h>
#include <stddef.h>
#include "rt_hal.h"
#include "rt_config.h"
#include "rt_charset.h"
#include "rt_model.h"
#include "rt_chat.h"
#include "rt_engine.h"

/* ---- fixed-address model buffer (same in every cassette block) ---- */
#ifndef RT_MODEL_BUF_ADDR
#define RT_MODEL_BUF_ADDR 0x7000
#endif

/* ---- session state in the D-file scratch tier, rows 6-7 ----
 * 48 payload bytes packed 3 -> 4 into 64 cells of 6 bits (pure 8-bit
 * math below): magic 'R','T','1' + version, hist[RT_MAX_CTX], hist_n,
 * seed(4), topic[8] as charset indices (<=1 = base), xor checksum */
#define ST_ROW   6
#define ST_CELLS 64

static rt_model model;
static rt_chat chat;
static char topic[9];

static void say(const char *s)
{
    while (*s)
        hal_putchar(*s++);
}

static void say_int(int v)
{
    char b[7];
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

/* pack b[0..47] into 64 scratch cells, 3 bytes -> 4 cells */
static void pack_state(const rt_u8 *b)
{
    int c;

    for (c = 0; c < 16; c++) {
        rt_u8 b0 = b[c * 3], b1 = b[c * 3 + 1], b2 = b[c * 3 + 2];
        long base = ST_ROW * 32 + c * 4;

        hal_scratch_put(base, b0 & 0x3F);
        hal_scratch_put(base + 1,
                        (rt_u8)((b0 >> 6) | ((b1 & 0x0F) << 2)));
        hal_scratch_put(base + 2,
                        (rt_u8)(((b1 >> 4) & 0x03) | ((b2 & 0x03) << 4)));
        hal_scratch_put(base + 3, b2 >> 2);
    }
}

static void unpack_state(rt_u8 *b)
{
    int c;

    for (c = 0; c < 16; c++) {
        rt_u8 c0 = hal_scratch_get(ST_ROW * 32 + c * 4);
        rt_u8 c1 = hal_scratch_get(ST_ROW * 32 + c * 4 + 1);
        rt_u8 c2 = hal_scratch_get(ST_ROW * 32 + c * 4 + 2);
        rt_u8 c3 = hal_scratch_get(ST_ROW * 32 + c * 4 + 3);

        b[c * 3] = (rt_u8)((c0 & 0x3F) | (c1 << 6));
        b[c * 3 + 1] = (rt_u8)(((c1 >> 2) & 0x0F) | (c2 << 4));
        b[c * 3 + 2] = (rt_u8)(((c2 >> 4) & 0x03) | (c3 << 2));
    }
}

/* 1 = valid state restored, 0 = cold boot.
 * Primary copy: D-file rows 6-7 (the visible work area). Backup copy:
 * plain RAM at 0x7A80 - ABOVE the topic-image end (0x7A78), BELOW the
 * D-file - so it survives both a topic load and a CLS that the
 * emulator might run after loading. If the visible copy was wiped but
 * the backup is valid, restore from it and repack the visible copy. */
#define ST_BACKUP ((rt_u8 *)0x7A80)

static int state_valid(const rt_u8 *b)
{
    rt_u8 x = 0;
    int i;

    if (b[0] != 'R' || b[1] != 'T' || b[2] != '1')
        return 0;
    for (i = 0; i < 47; i++)
        x = (rt_u8)(x ^ b[i]);
    return x == b[47];
}

static void state_apply(const rt_u8 *b)
{
    int i;

    for (i = 0; i < RT_MAX_CTX; i++)
        chat.hist[i] = b[4 + i] < RT_CHARSET_LEN ? b[4 + i] : 1;
    chat.hist_n = b[12] > RT_MAX_CTX ? RT_MAX_CTX : b[12];
    chat.seed = (rt_u32)b[13] | ((rt_u32)b[14] << 8) |
                ((rt_u32)b[15] << 16) | ((rt_u32)b[16] << 24);
    for (i = 0; i < 8; i++)
        topic[i] = (b[17 + i] > 1 && b[17 + i] < RT_CHARSET_LEN)
                       ? RT_CHARSET[b[17 + i]] : '\0';
    topic[8] = '\0';
}

static int state_restore(void)
{
    rt_u8 b[48];
    int i;

    unpack_state(b);
    if (state_valid(b)) {
        state_apply(b);
        return 1;
    }
    /* visible copy wiped (e.g. CLS after a topic load)? try the backup */
    for (i = 0; i < 48; i++)
        b[i] = ST_BACKUP[i];
    if (state_valid(b)) {
        state_apply(b);
        pack_state(b); /* repack the visible work area */
        return 1;
    }
    return 0;
}

static void state_save(void)
{
    rt_u8 b[48];
    rt_u8 x = 0;
    int i;

    for (i = 0; i < 48; i++)
        b[i] = 0;
    b[0] = 'R';
    b[1] = 'T';
    b[2] = '1';
    b[3] = 1;
    for (i = 0; i < RT_MAX_CTX; i++)
        b[4 + i] = chat.hist[i];
    b[12] = (rt_u8)chat.hist_n;
    b[13] = (rt_u8)(chat.seed & 0xFF);
    b[14] = (rt_u8)((chat.seed >> 8) & 0xFF);
    b[15] = (rt_u8)((chat.seed >> 16) & 0xFF);
    b[16] = (rt_u8)((chat.seed >> 24) & 0xFF);
    for (i = 0; i < 8; i++)
        b[17 + i] = topic[i] ? rt_map_char(topic[i]) : 1;
    for (i = 0; i < 47; i++)
        x = (rt_u8)(x ^ b[i]);
    b[47] = x;
    pack_state(b);
    for (i = 0; i < 48; i++)        /* backup copy: plain RAM at $7A80 */
        ST_BACKUP[i] = b[i];
}

/* live context window in D-file row 1 - the visible work area */
static void show_context(void)
{
    int i;

    for (i = 0; i < RT_MAX_CTX; i++) {
        char c = (i < chat.hist_n) ? RT_CHARSET[chat.hist[i]] : ' ';
        hal_scratch_char(32 + i, c == '\n' ? ' ' : c);
    }
}

static void emit(char c, void *user)
{
    (void)user;
    hal_putchar(c);
    hal_flush();
}

static int read_line(char *line, int maxlen)
{
    int i = 0, c;

    while (i < maxlen - 1) {
        c = hal_getchar();
        if (c < 0)
            continue;
        if (c == '\n' || c == '\r')
            break;
        hal_putchar((char)c);
        line[i++] = (char)c;
    }
    hal_putchar('\n');
    line[i] = '\0';
    return i;
}

/* flat topic table: sccz80 1.8 cannot parse arrays of pointers */
static const char TOPICS[] =
    "greetings\0" "weather\0" "animals\0" "retro\0"
    "numbers\0" "jokes\0";
#define NTOPICS 6

static void say_topic(int i)
{
    const char *p = TOPICS;

    while (i > 0 && *p) {
        while (*p)
            p++;
        p++;
        i--;
    }
    while (*p)
        hal_putchar(*p++);
}

static void cmd_topic(char *arg)
{
    int i;

    if (!*arg) {
        for (i = 0; i < NTOPICS; i++) {
            say_int(i + 1);
            hal_putchar(' ');
            say_topic(i);
            hal_putchar('\n');
        }
        say("which tape to insert:\n");
        return;
    }
    i = 0;
    while (*arg >= '0' && *arg <= '9')
        i = i * 10 + (*arg++ - '0');
    if (i < 1 || i > NTOPICS) {
        say("no such topic\n");
        return;
    }
    say("insert: ");
    say_topic(i - 1);
    say("\nload the .p, then run\n");
}

int main(void)
{
    char line[RT_LINE_MAX];
    int restored;

    rt_charset_init();
    if (rt_model_load(&model, (const rt_u8 *)RT_MODEL_BUF_ADDR,
                      RT_APP_MODEL_MAX) != 0)
        hal_panic("no model - bad cassette");

    rt_chat_init(&chat, hal_entropy());
    restored = state_restore();

    say("retro-tinyllm 16k\n");
    if (restored) {
        say("topic: ");
        say(topic);
    } else {
        say("/help /topic - chat lowercase");
    }
    say("\n");
    show_context();

    for (;;) {
        say("you> ");
        hal_flush();
        read_line(line, sizeof(line));
        if (line[0] == '/') {
            char *cmd = line + 1, *arg = "";
            char *sp = strchr(cmd, ' ');
            if (sp) {
                *sp = '\0';
                arg = sp + 1;
            }
            if (!strcmp(cmd, "help"))
                say("/help /topic /new /quit\n");
            else if (!strcmp(cmd, "topic"))
                cmd_topic(arg);
            else if (!strcmp(cmd, "new")) {
                rt_chat_init(&chat, hal_entropy());
                topic[0] = '\0';
                say("context cleared\n");
            } else if (!strcmp(cmd, "quit"))
                break;
            else
                say("unknown - /help\n");
        } else if (line[0]) {
            rt_chat_push(&chat, line);
            rt_chat_gen(&chat, &model, emit, 0);
            hal_putchar('\n');
        }
        show_context();
        state_save();
    }
    state_save();
    return 0;
}
