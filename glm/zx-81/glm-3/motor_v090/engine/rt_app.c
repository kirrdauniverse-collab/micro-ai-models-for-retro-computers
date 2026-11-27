/* rt_app.c - portable chat REPL shared by every port (see rt_app.h).
 *
 * v0.2 flow: a GENERAL base model is loaded at boot. Chat input is
 * routed by keywords: a clear specialist topic loads that pack (disk
 * first, tape as fallback - the tape order is printed on the cassette
 * label by tools/tapewriter.py); an AMBIGUOUS word (star: astronomy or
 * poetry?) triggers a clarifying question first. The machine also asks
 * for the date and time at boot (no RTC back then), knows the weekday,
 * part of day and season, and keeps a dated journal of "little things"
 * the user mentions - saved automatically when the session ends and
 * recalled on the next boot.
 */
#include <string.h>
#include <stddef.h>
#include <stdlib.h>
#include "rt_app.h"
#include "rt_hal.h"
#include "rt_config.h"
#include "rt_charset.h"
#include "rt_model.h"
#include "rt_chat.h"
#include "rt_engine.h"
#include "rt_memory.h"
#include "rt_clock.h"
#include "rt_router.h"
#include "rt_journal.h"
#include "rt_scratch.h"
#if RT_ENABLE_FINETUNE
#include "rt_finetune.h"
#endif

#define TAPE_MANIFEST_MAX 8

/* On machines where the cassette image places the model at a fixed
 * address (ZX81 single-block T81), the app points the buffer there
 * instead of paying RAM for a second copy. */
#ifdef RT_MODEL_BUF_ADDR
static rt_u8    *app_model_buf = (rt_u8 *)RT_MODEL_BUF_ADDR;
#else
static rt_u8     app_model_buf[RT_APP_MODEL_MAX];
#endif
static rt_model  app_model;
static rt_chat   app_chat;
static rt_memory app_mem;
static rt_clock  app_clock;
static rt_journal app_journal;
static int       app_sim_ms;   /* per-letter delay, 0 = instant */
static char      app_base_name[24]; /* how the base model was booted */
static int       app_base_block;    /* -1 = from disk, >=0 = tape block */
static char      app_cur_topic[16]; /* "" = base model */
/* pending clarification: candidate topics + the original question */
static char      app_clarify[RT_ROUTER_MAX_HITS * 16];
static int       app_clarify_n;
static char      app_clarify_q[RT_LINE_MAX];
/* tape manifest cache: block 0 of the topic tape is manifest.cfg */
static char      app_tape_names[TAPE_MANIFEST_MAX * 16];
static int       app_tape_n = -1; /* -1 = not loaded yet */

static void say(const char *s)
{
    while (*s)
        hal_putchar(*s++);
}

static void say_int(long v)
{
    char b[16];
    int i = 0, j;
    if (v < 0) {
        hal_putchar('-');
        v = -v;
    }
    if (v == 0)
        b[i++] = '0';
    while (v > 0 && i < 15) {
        b[i++] = (char)('0' + (v % 10));
        v /= 10;
    }
    for (j = i - 1; j >= 0; j--)
        hal_putchar(b[j]);
}

static void say_int2(long v) /* two digits, zero padded */
{
    if (v < 0)
        v = -v;
    if (v < 10)
        hal_putchar('0');
    say_int(v);
}

static void emit_char(char c, void *user)
{
    (void)user;
    hal_putchar(c);
    hal_flush();
    if (app_sim_ms)
        hal_msleep(app_sim_ms);
}

/* read one line, echo it, return length (-1 on EOF) */
static int read_line(char *line, int maxlen)
{
    int i = 0, c;
    while (i < maxlen - 1) {
        c = hal_getchar();
        if (c < 0)
            return -1;
        if (c == '\n' || c == '\r')
            break;
        hal_putchar((char)c);
        line[i++] = (char)c;
    }
    hal_putchar('\n');
    line[i] = '\0';
    return i;
}

static void model_rechecksum(void)
{
    rt_u32 sum = 0;
    long n = rt_model_size(&app_model.hdr) - 2;
    long i;
    rt_u8 *raw = (rt_u8 *)app_model.raw; /* we own the blob buffer */
    for (i = 0; i < n; i++)
        sum = (sum + raw[i]) & 0xFFFFUL;
    raw[n] = (rt_u8)(sum & 0xFF);
    raw[n + 1] = (rt_u8)((sum >> 8) & 0xFF);
}

static int load_model_blob(const rt_u8 *buf, long len)
{
    int greedy = app_chat.greedy;   /* user prefs survive model swaps */
    int temp_sh = app_chat.temp_sh;
    if (rt_model_load(&app_model, buf, len) != 0)
        return -1;
    if (app_model.hdr.ctx > RT_MAX_CTX || app_model.hdr.h1 > RT_MAX_HID ||
        app_model.hdr.h2 > RT_MAX_HID)
        return -2;
    rt_chat_init(&app_chat, hal_entropy());
    app_chat.greedy = greedy;
    app_chat.temp_sh = temp_sh;
    return 0;
}

/* ---------- tape manifest (block 0 = manifest.cfg text) ---------- */

static void load_tape_manifest(void)
{
    static rt_u8 buf[1024];
    long n;
    char *p, *end;

    if (app_tape_n >= 0)
        return;
    app_tape_n = 0;
    n = hal_tape_load(0, buf, (long)sizeof(buf) - 1);
    if (n <= 0)
        return;
    buf[n] = '\0';
    p = (char *)buf;
    end = (char *)buf + n;
    while (p < end && app_tape_n < TAPE_MANIFEST_MAX) {
        char *line = p;
        char *tok;
        /* find end of line */
        while (p < end && *p != '\n')
            p++;
        *p++ = '\0';
        if (line[0] == '\0' || line[0] == '#')
            continue;
        /* first token = pack name */
        tok = line;
        while (*tok == ' ' || *tok == '\t')
            tok++;
        {
            char *e = tok;
            while (*e && *e != ' ' && *e != '\t')
                e++;
            *e = '\0';
        }
        if (strncmp(tok, "topic_", 6) != 0)
            continue; /* base models are not on the topic tape */
        tok += 6;
        if (tok[0] >= 'a' && tok[0] <= 'z') {
            strncpy(app_tape_names + app_tape_n * 16, tok, 15);
            app_tape_names[app_tape_n * 16 + 15] = 0;
            app_tape_n++;
        }
    }
}

static int find_tape_block(const char *topic)
{
    int i;
    load_tape_manifest();
    for (i = 0; i < app_tape_n; i++)
        if (strcmp(app_tape_names + i * 16, topic) == 0)
            return i + 1; /* block 0 is the manifest itself */
    return -1;
}

/* ---------- topic loading: disk first, tape fallback ---------- */

static int load_topic(const char *topic)
{
    char fname[24];
    long n;

    if (strncmp(topic, "topic_", 6) == 0)
        topic += 6;
    strcpy(fname, "topic_");
    strncat(fname, topic, 14);
    strcat(fname, ".bin");

    n = hal_load_file(fname, app_model_buf, RT_APP_MODEL_MAX);
    if (n >= 0 && load_model_blob(app_model_buf, n) == 0) {
        strncpy(app_cur_topic, topic, 15);
        app_cur_topic[15] = '\0';
        return 0;
    }

    /* tape fallback: ask the human to wind the cassette */
    {
        int blk = find_tape_block(topic);
        char dummy[8];
        if (blk < 0) {
            say("no ");
            say(topic);
            say(" pack on disk or tape.\n");
            return -1;
        }
        say("not on disk. insert the topic tape and wind it to the ");
        say(topic);
        say("\nblock (counter is on the cassette label), then press enter.\n");
        if (read_line(dummy, sizeof(dummy)) < 0)
            return -1;
        n = hal_tape_load(blk, app_model_buf, RT_APP_MODEL_MAX);
        if (n < 0 || load_model_blob(app_model_buf, n) != 0) {
            say("tape read failed.\n");
            return -1;
        }
        strncpy(app_cur_topic, topic, 15);
        app_cur_topic[15] = '\0';
        return 0;
    }
}

static int back_to_base(void)
{
    long n;
    if (app_base_block >= 0) {
        n = hal_tape_load(app_base_block, app_model_buf, RT_APP_MODEL_MAX);
        if (n >= 0 && load_model_blob(app_model_buf, n) == 0) {
            app_cur_topic[0] = '\0';
            return 0;
        }
        return -1;
    }
    n = hal_load_file(app_base_name, app_model_buf, RT_APP_MODEL_MAX);
    if (n >= 0 && load_model_blob(app_model_buf, n) == 0) {
        app_cur_topic[0] = '\0';
        return 0;
    }
    return -1;
}

/* ---------- date/time ---------- */

/* parse up to max integers from a line; returns how many were found */
static int parse_ints(const char *s, int *out, int max)
{
    int n = 0;
    while (*s && n < max) {
        char *end;
        while (*s == ' ' || *s == '\t' || *s == '-')
            s++;
        if (*s < '0' || *s > '9')
            break;
        out[n++] = (int)strtol(s, &end, 10);
        s = end;
    }
    return n;
}

static void ask_clock(void)
{
    char line[RT_LINE_MAX];
    int v[5];

    say("this machine has no clock, please tell me:\n");
    say("date today (yyyy mm dd, or just enter to skip)? ");
    hal_flush();
    if (read_line(line, sizeof(line)) < 0)
        return;
    if (line[0] == '\0') {
        say("(clock unset - /date set retries)\n");
        return;
    }
    if (parse_ints(line, v, 3) < 3) {
        say("i need yyyy mm dd - clock unset, /date set retries.\n");
        return;
    }
    say("time now (hh mm)? ");
    hal_flush();
    if (read_line(line, sizeof(line)) < 0)
        return;
    if (parse_ints(line, v + 3, 2) < 2) {
        v[3] = 12;
        v[4] = 0;
    }
    if (rt_clock_set(&app_clock, v[0], v[1], v[2], v[3], v[4]) != 0) {
        say("that is not a valid date or time - clock unset, /date retries.\n");
        return;
    }
    say("thanks! so it is ");
    say(rt_clock_dayname(app_clock.wd));
    say(", ");
    say_int(app_clock.y); hal_putchar('-');
    say_int2(app_clock.mo); hal_putchar('-');
    say_int2(app_clock.d);
    say(" ");
    say_int2(app_clock.h); hal_putchar(':');
    say_int2(app_clock.mi);
    say(" - a fine ");
    say(rt_clock_part_of_day(app_clock.h));
    say(" in ");
    say(rt_clock_season(app_clock.mo));
    say(".\n");
}

static void print_when(void)
{
    if (!app_clock.valid) {
        say("clock is unset, use /date\n");
        return;
    }
    say(rt_clock_dayname(app_clock.wd));
    say(" ");
    say_int(app_clock.y); hal_putchar('-');
    say_int2(app_clock.mo); hal_putchar('-');
    say_int2(app_clock.d);
    say(" ");
    say_int2(app_clock.h); hal_putchar(':');
    say_int2(app_clock.mi);
    say(", ");
    say(rt_clock_part_of_day(app_clock.h));
    say(", ");
    say(rt_clock_season(app_clock.mo));
    say(" (northern hemisphere)\n");
}

/* ---------- boot greeting: part of day + journal recall ---------- */

static int app_scratch_used; /* state came back from screen RAM */

static void boot_greeting(void)
{
    int idxs[4];
    int n, i;

    if (app_scratch_used)
        say("\n(facts and journal kept alive in screen ram)\n");
    if (!app_clock.valid)
        return;
    say("\ngood ");
    say(rt_clock_part_of_day(app_clock.h));
    say("! ");
    say(rt_clock_season(app_clock.mo));
    say(" it is. ");
    n = rt_journal_recent(&app_journal, &app_clock, 7, idxs, 4);
    if (n > 0) {
        say("i remember:\n");
        for (i = 0; i < n && i < 2; i++) {
            rt_jentry *e = &app_journal.e[idxs[i]];
            rt_clock then;
            then.y = e->yoff + 2000; then.mo = e->mo; then.d = e->d;
            then.h = 12; then.mi = 0; then.wd = e->wd; then.valid = 1;
            say("  on ");
            say(rt_clock_dayname(e->wd));
            say(" (");
            say_int(then.d);
            say(".");
            say_int(then.mo);
            say(".) you said: ");
            say(e->text);
            say("\n");
        }
        if (n > 2) {
            say("  and ");
            say_int(n - 2);
            say(" more (/journal lists all)\n");
        }
    }
    say("\n");
}

/* ---------- commands ---------- */

static void cmd_info(void)
{
    long params = (long)app_model.hdr.vocab * app_model.hdr.emb
        + (long)app_model.hdr.h1 * ((long)app_model.hdr.ctx * app_model.hdr.emb + 1)
        + (long)app_model.hdr.vocab * ((app_model.hdr.h2 ? app_model.hdr.h2
                                                          : app_model.hdr.h1) + 1);
    if (app_model.hdr.h2)
        params += (long)app_model.hdr.h2 * (app_model.hdr.h1 + 1);
    say("model: ");
    if (app_cur_topic[0]) {
        say("topic_");
        say(app_cur_topic);
        say(" (");
        say(app_base_name);
        say(" is the base, /back returns)\n");
    } else {
        say(app_base_name);
        say(" (general)\n");
    }
    say("vocab ");
    say_int(app_model.hdr.vocab);
    say(" ctx ");
    say_int(app_model.hdr.ctx);
    say(" emb ");
    say_int(app_model.hdr.emb);
    say(" h1 ");
    say_int(app_model.hdr.h1);
    say(" h2 ");
    say_int(app_model.hdr.h2);
    say("\nparams: ");
    say_int(params);
    say(" (int8) blob: ");
    say_int(rt_model_size(&app_model.hdr));
    say(" bytes\nfacts: ");
    say_int(app_mem.n);
    say("/");
    say_int(RT_MEM_MAX);
    say("  journal: ");
    say_int(app_journal.n);
    say("/");
    say_int(RT_JOURNAL_MAX);
    say("\ntemp_sh: ");
    say_int(app_chat.temp_sh);
    say(" greedy: ");
    say(app_chat.greedy ? "on" : "off");
    say("\nclock: ");
    if (app_clock.valid) {
        say("set, ");
        say(rt_clock_part_of_day(app_clock.h));
        say(", ");
        say(rt_clock_season(app_clock.mo));
    } else {
        say("unset (/date)");
    }
    say("\n");
}

static void cmd_teach(char *line)
{
    char *eq = strchr(line, '=');
    char *key, *val;
    int r;
    if (!eq) {
        say("usage: /teach key = value\n");
        return;
    }
    *eq = '\0';
    key = line;
    val = eq + 1;
    while (*key == ' ')
        key++;
    while (*val == ' ')
        val++;
    { /* trim trailing spaces from both sides */
        char *end = key + strlen(key);
        while (end > key && end[-1] == ' ')
            *--end = '\0';
        end = val + strlen(val);
        while (end > val && end[-1] == ' ')
            *--end = '\0';
    }
    r = rt_mem_teach(&app_mem, key, val);
    if (r == 0)
        say("learned.\n");
    else if (r == -1)
        say("memory full, /forget something first.\n");
    else
        say("usage: /teach key = value\n");
}

static void cmd_mem(void)
{
    int i;
    if (app_mem.n == 0) {
        say("nothing taught yet.\n");
        return;
    }
    for (i = 0; i < app_mem.n; i++) {
        say_int(i);
        say(": ");
        say(app_mem.rec[i].key);
        say(" = ");
        say(app_mem.rec[i].val);
        say("\n");
    }
}

static void cmd_journal(void)
{
    int i;
    if (app_journal.n == 0) {
        say("the journal is empty.\n");
        return;
    }
    for (i = 0; i < app_journal.n; i++) {
        rt_jentry *e = &app_journal.e[i];
        say_int(e->yoff + 2000); hal_putchar('-');
        say_int2(e->mo); hal_putchar('-');
        say_int2(e->d);
        say(" ");
        say(rt_clock_dayname(e->wd));
        say(": ");
        say(e->text);
        say("\n");
    }
}

static void save_all(int quiet)
{
    rt_u8 mbuf[8 + RT_MEM_MAX * (RT_MEM_KEY + RT_MEM_VAL)];
    rt_u8 jbuf[8 + RT_JOURNAL_MAX * (4 + RT_JOURNAL_TEXT)];
    long n;
    int ok1 = 0, ok2 = 0;

    n = rt_mem_pack(&app_mem, mbuf, sizeof(mbuf));
    if (n > 0 && hal_save_file("memory.bin", mbuf, n) == 0)
        ok1 = 1;
    else if (n > 0 && hal_tape_save(9, mbuf, n) == 0) /* tape fallback */
        ok1 = 2;
    n = rt_journal_pack(&app_journal, jbuf, sizeof(jbuf));
    if (n > 0 && hal_save_file("journal.bin", jbuf, n) == 0)
        ok2 = 1;
    else if (n > 0 && hal_tape_save(10, jbuf, n) == 0)
        ok2 = 2;
    if (rt_scratch_store(&app_mem, &app_journal) > 0)
        ok2 = ok2 ? ok2 : 3; /* third tier: screen RAM */

    if (!quiet) {
        say(ok1 ? (ok1 == 1 ? "memory.bin saved. " : "memory saved to tape. ")
                : "could not save memory. ");
        say(ok2 ? (ok2 == 1 ? "journal.bin saved.\n"
                            : ok2 == 2 ? "journal saved to tape.\n"
                                       : "state kept in screen ram.\n")
                : "could not save journal.\n");
    }
#if RT_ENABLE_FINETUNE
    if (!quiet && (app_model.hdr.flags & RT_FLAG_FINETUNE_OK) &&
        app_cur_topic[0] == '\0') {
        model_rechecksum();
        if (hal_save_file("model_finetuned.bin", app_model.raw,
                          rt_model_size(&app_model.hdr)) == 0)
            say("model_finetuned.bin saved.\n");
    }
#endif
}

static void cmd_topics(void)
{
    char names[12 * 16];
    int n = hal_list_topics(names, 12);
    int i;

    if (n > 0) {
        say("on disk:\n");
        for (i = 0; i < n; i++) {
            say("  ");
            say(names + i * 16 + 6); /* skip the topic_ prefix */
            say("\n");
        }
    }
    load_tape_manifest();
    if (app_tape_n > 0) {
        say("on tape (block - counter on the cassette label):\n");
        for (i = 0; i < app_tape_n; i++) {
            say("  ");
            say_int(i + 1);
            say(" ");
            say(app_tape_names + i * 16);
            say("\n");
        }
    }
    if (n <= 0 && app_tape_n <= 0)
        say("no topic packs found on disk or tape.\n");
}

static void cmd_load(char *arg)
{
    long n;
    if (*arg >= '0' && *arg <= '9') {
        /* tape-style: load the n-th block */
        n = hal_tape_load((int)(*arg - '0'), app_model_buf,
                          RT_APP_MODEL_MAX);
        if (n < 0) {
            say("tape read failed (");
            say_int(n);
            say(")\n");
            return;
        }
    } else if (load_topic(arg) == 0) {
        say("topic loaded: ");
        say(app_cur_topic);
        say("\n");
        return;
    } else {
        return;
    }
    if (load_model_blob(app_model_buf, n) != 0) {
        say("not a valid model (bad magic/version/dims).\n");
        return;
    }
    app_cur_topic[0] = '\0';
    say("topic loaded from tape block.\n");
}

static void cmd_finetune(void)
{
#if RT_ENABLE_FINETUNE
    int i, r, hits = 0, total = 0;
    char text[RT_MEM_MAX * 80 * 3];
    int len = 0;
    if (app_mem.n == 0) {
        say("teach me something first (/teach key = value).\n");
        return;
    }
    if (!(app_model.hdr.flags & RT_FLAG_FINETUNE_OK)) {
        say("this model does not allow fine-tuning.\n");
        return;
    }
    /* repeat every fact 3x: the positive signal must outweigh the
     * "don't predict this letter here" gradient from all other text */
    for (r = 0; r < 3; r++) {
        for (i = 0; i < app_mem.n; i++) {
            if (len > (int)sizeof(text) - 100)
                break;
            strcpy(text + len, app_mem.rec[i].key);
            len += (int)strlen(app_mem.rec[i].key);
            strcpy(text + len, " is ");
            len += 4;
            strcpy(text + len, app_mem.rec[i].val);
            len += (int)strlen(app_mem.rec[i].val);
            strcpy(text + len, ".\n");
            len += 2;
        }
    }
    total = len;
    say("fine-tuning on ");
    say_int(app_mem.n);
    say(" facts...\n");
    hits = rt_finetune_text(&app_model, text, 3, 14);
    say("done: ");
    say_int(hits);
    say("/");
    say_int(total);
    say(" chars predicted correctly on the last sweep.\n");
    say("try asking now, and /save to keep the tuned model.\n");
#else
    say("fine-tuning is disabled in this build.\n");
#endif
}

static void cmd_sim(char *arg)
{
    if (strncmp(arg, "amiga", 5) == 0) {
        app_sim_ms = 900;
        say("simulating amiga 500 pace (~1 s/letter, class A/B)\n");
    } else if (strncmp(arg, "c64", 3) == 0) {
        app_sim_ms = 1800;
        say("simulating c64 pace (~2 s/letter, class C)\n");
    } else if (strncmp(arg, "zx81", 4) == 0) {
        app_sim_ms = 1200;
        say("simulating zx81 pace (~1.2 s/letter, class D)\n");
    } else {
        app_sim_ms = 0;
        say("real-time pace\n");
    }
}

/* ---------- chat with routing ---------- */

static void generate_reply(const char *line)
{
    rt_chat_push(&app_chat, line);
    rt_chat_push_idx(&app_chat, 0); /* newline: my turn */
    say("> ");
    rt_chat_gen(&app_chat, &app_model, emit_char, 0);
    say("\n");
}

static int topic_equals_current(const char *t)
{
    return strcmp(t, app_cur_topic) == 0;
}

static void chat_line(const char *line)
{
    char hits[RT_ROUTER_MAX_HITS * 16];
    char felt[64];
    int n, i, hit;

    /* 1. answer a pending clarification */
    if (app_clarify_n > 0) {
        int pick = -1;
        if (line[0] >= '1' && line[0] <= '9' && line[1] == '\0')
            pick = line[0] - '1';
        else
            for (i = 0; i < app_clarify_n; i++)
                if (strcmp(line, app_clarify + i * 16) == 0)
                    pick = i;
        if ((line[0] == 'n' && strcmp(line, "no") == 0) ||
            strcmp(line, "neither") == 0) {
            say("> ok, staying general.\n");
            app_clarify_n = 0;
            generate_reply(app_clarify_q);
            return;
        }
        if (pick < 0 || pick >= app_clarify_n) {
            say("please answer 1-");
            say_int(app_clarify_n);
            say(", a topic name, or 'neither'.\n");
            return;
        }
        app_clarify_n = 0;
        if (load_topic(app_clarify[pick]) == 0) {
            say("> loaded the ");
            say(app_cur_topic);
            say(" pack. ");
            generate_reply(app_clarify_q);
        } else {
            say("> staying on the general model. ");
            generate_reply(app_clarify_q);
        }
        return;
    }

    /* 2. "little things" -> dated journal */
    if (rt_journal_scan_feelings(line, felt, sizeof(felt)) &&
        rt_journal_add(&app_journal, &app_clock, felt) == 0) {
        say("(noted in my journal");
        if (app_clock.valid) {
            say(": ");
            say(rt_clock_dayname(app_clock.wd));
            say(" ");
            say_int(app_clock.d);
            say(".");
            say_int(app_clock.mo);
            say(".");
        }
        say(" - i will remember.)\n");
    }

    /* 3. taught facts */
    hit = rt_mem_match(&app_mem, line);
    if (hit >= 0) {
        char ans[RT_MEM_KEY + RT_MEM_VAL + 16];
        rt_mem_answer(&app_mem.rec[hit], ans, sizeof(ans));
        rt_chat_push(&app_chat, line);
        rt_chat_push_idx(&app_chat, 0);
        say("> ");
        say(ans);
        say("\n");
        return;
    }

    /* 4. topic routing */
    n = rt_router_scan(line, hits, RT_ROUTER_MAX_HITS);
    if (n >= 2) {
        /* if one candidate is already loaded, stay on it - no need to
         * re-ask a question we have already answered */
        int cur = -1;
        if (app_cur_topic[0]) {
            for (i = 0; i < n; i++)
                if (strcmp(hits + i * 16, app_cur_topic) == 0)
                    cur = i;
        }
        if (cur < 0) {
            say("> interesting - that could be ");
            for (i = 0; i < n; i++) {
                if (i)
                    say(i + 1 == n ? " or " : ", ");
                say_int(i + 1);
                say(") ");
                say(hits + i * 16);
            }
            say(". which one?\n");
            for (i = 0; i < n; i++) {
                const char *s = hits[i];
                int k;
                for (k = 0; k < 15 && s[k]; k++)
                    app_clarify[i * 16 + k] = s[k];
                app_clarify[i * 16 + k] = 0;
            }
            app_clarify_n = n;
            strncpy(app_clarify_q, line, RT_LINE_MAX - 1);
            app_clarify_q[RT_LINE_MAX - 1] = '\0';
            return;
        }
    } else if (n == 1 && !topic_equals_current(hits[0])) {
        say("(sounds like ");
        say(hits[0]);
        say(" - loading the pack...)\n");
        if (load_topic(hits[0]) != 0)
            say("(staying on the general model)\n");
    }

    /* 5. generate */
    generate_reply(line);
}

/* ---------- boot ---------- */

static int boot_common(void)
{
    rt_u8 membuf[8 + RT_MEM_MAX * (RT_MEM_KEY + RT_MEM_VAL)];
    rt_u8 jbuf[8 + RT_JOURNAL_MAX * (4 + RT_JOURNAL_TEXT)];
    long n;

    rt_mem_init(&app_mem);
    n = hal_load_file("memory.bin", membuf, sizeof(membuf));
    if (n > 0)
        rt_mem_unpack(&app_mem, membuf, n);
    rt_journal_init(&app_journal);
    n = hal_load_file("journal.bin", jbuf, sizeof(jbuf));
    if (n > 0)
        rt_journal_unpack(&app_journal, jbuf, n);
    if (app_mem.n == 0 || app_journal.n == 0)
        app_scratch_used = (rt_scratch_restore(&app_mem, &app_journal) == 0);
    rt_clock_init(&app_clock);
    return 0;
}

int rt_app_boot(const char *model_name)
{
    long n;

    rt_charset_init();
    n = hal_load_file(model_name, app_model_buf, RT_APP_MODEL_MAX);
    if (n < 0)
        return -1;
    if (load_model_blob(app_model_buf, n) != 0)
        return -2;
    strncpy(app_base_name, model_name, sizeof(app_base_name) - 1);
    app_base_name[sizeof(app_base_name) - 1] = '\0';
    app_base_block = -1;
    app_cur_topic[0] = '\0';
    return boot_common();
}

int rt_app_boot_tape(int block)
{
    long n;

    rt_charset_init();
    n = hal_tape_load(block, app_model_buf, RT_APP_MODEL_MAX);
    if (n < 0)
        return -1;
    if (load_model_blob(app_model_buf, n) != 0)
        return -2;
    strcpy(app_base_name, "tape block");
    app_base_block = block;
    app_cur_topic[0] = '\0';
    return boot_common();
}

void rt_app_run(void)
{
    char line[RT_LINE_MAX];

    say("\nretro-tinyllm v0.2 - tiny int8 chat models on 8/16-bit machines\n");
    say("general model first; special topics load on demand, ambiguous\n");
    say("words get a clarifying question. /help lists the commands.\n");

    ask_clock();
    boot_greeting();

    for (;;) {
        say("you> ");
        hal_flush();
        if (read_line(line, sizeof(line)) < 0)
            break; /* EOF (host) */

        if (line[0] == '/') {
            char *cmd = line + 1, *arg = "";
            char *sp = strchr(cmd, ' ');
            if (sp) {
                *sp = '\0';
                arg = sp + 1;
                while (*arg == ' ')
                    arg++;
            }
            if (strcmp(cmd, "help") == 0) {
                say("commands: /info /teach k=v /mem /journal /forget n\n"
                    "          /save /topics /load name|n /back\n"
                    "          /date /when /temp 0-6 /greedy on|off\n"
                    "          /finetune /sim off|amiga|c64|zx81 /quit\n");
            } else if (strcmp(cmd, "info") == 0) {
                cmd_info();
            } else if (strcmp(cmd, "teach") == 0) {
                cmd_teach(arg);
            } else if (strcmp(cmd, "mem") == 0) {
                cmd_mem();
            } else if (strcmp(cmd, "journal") == 0) {
                cmd_journal();
            } else if (strcmp(cmd, "forget") == 0) {
                rt_mem_forget(&app_mem, atoi(arg));
                say("forgotten.\n");
            } else if (strcmp(cmd, "save") == 0) {
                save_all(0);
            } else if (strcmp(cmd, "topics") == 0) {
                cmd_topics();
            } else if (strcmp(cmd, "load") == 0) {
                cmd_load(arg);
            } else if (strcmp(cmd, "back") == 0) {
                if (back_to_base() == 0)
                    say("back to the general model.\n");
                else
                    say("could not reload the base model.\n");
            } else if (strcmp(cmd, "date") == 0) {
                if (strcmp(arg, "set") == 0)
                    ask_clock();
                else
                    print_when();
            } else if (strcmp(cmd, "when") == 0) {
                print_when();
            } else if (strcmp(cmd, "temp") == 0) {
                app_chat.temp_sh = atoi(arg) & 7;
                say("temp_sh = ");
                say_int(app_chat.temp_sh);
                say("\n");
            } else if (strcmp(cmd, "greedy") == 0) {
                app_chat.greedy = (strncmp(arg, "on", 2) == 0);
                say(app_chat.greedy ? "greedy on\n" : "sampling on\n");
            } else if (strcmp(cmd, "finetune") == 0) {
                cmd_finetune();
            } else if (strcmp(cmd, "sim") == 0) {
                cmd_sim(arg);
            } else if (strcmp(cmd, "quit") == 0) {
                save_all(1);
                say("saved memory and journal. bye!\n");
                return;
            } else {
                say("unknown command, /help lists them.\n");
            }
        } else if (line[0] != '\0') {
            chat_line(line);
        }
    }
    save_all(1); /* EOF on stdin: save too */
}
