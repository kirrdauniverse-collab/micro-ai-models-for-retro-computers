#!/usr/bin/env python3
"""zx81ai_kb.py - knowledge banks for the ZX81 AI 16K cassette.

The "model" of the 16K edition is a fully indexed knowledge bank: topic
intents with keyword triggers plus reply variants, stored as compact
records in RAM.  The engine (ports/zx81/ai16/zx81ai.asm) matches the
chat line against these banks in place; no decompression buffers are
needed, which is what makes the whole system fit a stock 16K ZX81.

Bank record format (little-endian, plain ZX81-charset bytes):

    header : 'KB1', 0x01, name[12 zero-padded], nint u16
    record : handler u8, pack u8, nkeys u8,
             keys:  nkeys x { len u8, chars },
             nrep u8, replies: nrep x { len u8, chars }

Reply text may contain '$'-tokens the engine substitutes ($N name,
$L town, $D date, $W weekday, $T time, $P part of day, $B birthday,
$G gender) and '#' between sentences for hard line breaks.

Layout (fixed addresses, shared with the engine and tools/t81ai16_build.py):

    0x4082  engine code (Z80, line 1 REM blob)  -> 0x5725
    0x5910  MEM slot (512 B, user memory)       -> 0x593F
    0x5A10  BASE bank   (3008 B max)            -> 0x64FF
    0x65A0  WEATHER pack (1728 B max)           -> 0x6BBF
    0x6BC0  RETRO pack   (1728 B max)           -> 0x727F
            ^ help pages parked at 0x7100..0x727F (3 x 128 B),
              retro records must end below 0x7100
    0x7280  RT-TURBO stub (96 B, reserved)      -> 0x72DF
    0x72E0  OUTBUF (64 B, engine work)          -> 0x73DF
    0x73E0  LINEIN + parser + editor vars       -> 0x741F
    0x7420  DOCBUF (48 B) + MISC vars (24 B)    -> 0x746F
    0x7470  HIST ring (35 slots x 33 B)         -> 0x78F2
    0x78F8  D-file (793 B) + VARS marker        <- placed by t81frame

Usage: python3 zx81ai_kb.py [out.bin]
"""
import sys

MEM_ADDR = 0x5918
BASE_ADDR = 0x5A18
PACK_WEATHER = 0x65A8
PACK_RETRO = 0x6BD0
TURBO_ADDR = 0x7290
OUTBUF_ADDR = 0x72F0
LINEIN_ADDR = 0x73F0
MISC_ADDR = 0x7460
HIST_ADDR = 0x7480
WORK_END = 0x7903          # HIST ring end; the D-file is built from here

PROMPT_RESERVE = 0x6A60     # parked prompts live in the weather slot tail

BANK_LIMITS = (
    ('base', BASE_ADDR, PACK_WEATHER),
    ('weather', PACK_WEATHER, PROMPT_RESERVE),
    ('retro', PACK_RETRO, TURBO_ADDR),
)
NAME_LIMIT = 12

# Help text pages are parked in the RETRO slot tail, behind the retro
# records and in front of the inert RT-TURBO stub (one 128 B page each).
HELP_C1 = 0x7100
HELP_C2 = 0x7180
HELP_C3 = 0x7200
HELP_PAGE = 0x80
PROMPT_SLOTS = (
    # parked boot prompts: (name, text, slot addr)
    ('PH_HELP',  'want help with usage? (y/n)', 0x6A60),
    ('PH_DATE',  'date? dd mm yy (like 21 11 26)', 0x6AA0),
    ('PH_TIME',  'time? hh mm (like 9 30)', 0x6AE0),
    ('PH_NAME',  'your name?', 0x6B20),
    ('PH_CALL',  'how may i call you? (enter)', 0x6B60),
    ('PH_CARE',  'last time you felt bad. all good now? (y/n)', 0x6BA0),
)

# Boot help + /help, three pages of max 4 lines x 30 chars each.
HELPCHAT = (
    ('talk: type text, press enter.',
     'i learn facts like: my name is',
     'x, i live in x, i am a girl or',
     'boy, my birthday is 21 3.'),
    ('i file your feelings with the',
     'date and ask about them later.',
     'i feel good clears them.',
     '(press a key to continue)'),
    ('cmds /help /topics /mem',
     ' /temp n /reason n /save /quit',
     'shift+1..4=temp, shift+9=think',
     'shift+7/6 page, shift+0 erase'),
)

# ---------------------------------------------------------------- intents
# (handler, pack, 'key1 | key 2 | ...', 'reply 1 ~ reply 2 ~ ...')
# handlers:
#   0 plain reply            4 birthday-set      9  gender-recall
#   1 name-set               5 journal-add       10 birthday-recall
#   2 town-set               6 journal-clear     11 time-recall
#   7 name-recall            8 town-recall       12 date-recall
#   3 gender-set            13 journal-recall
#  14 show-help             15 pack-ask         16 fallback  17 about
#  18 save-and-exit         19 list-topics
BASE = [
    (0, 0, 'hi | hello | hey | greetings | good morning | good evening',
     'hello $n. i am awake and ready. ~ greetings, $n. how can i help?'),

    (0, 0, 'how are you | are you ok | are you well | are you alright',
     'i am fine. 3.25 mhz, all quiet. and you, $n? ~ '
     'running well. the memory bank holds. how are you, $n?'),

    (6, 0, 'i am fine | i feel good | i feel fine | i am great | '
     'i feel great | i am ok | feeling good | feeling fine | '
     'no more pain | the pain is gone',
     'good news, $n. i removed the old pain notes from my memory. ~ '
     'happy to hear it. the health notes are cleared.'),

    (0, 0, 'thank | thanks | cheers',
     'you are welcome, $n. ~ any time. the tape keeps rolling.'),

    (18, 0, 'bye | goodbye | good night | farewell | see you',
     'saving memory. bye $n. press play again any time.'),

    (17, 0, 'who are you | what are you | your name | introduce yourself',
     'i am zx81 ai. a small brain on a tape. ~ '
     'zx81 ai. one kilo of plastic, a lot of thinking.'),

    (14, 0, 'help | what can you do | commands | usage | what do you know',
     '.'),

    (1, 0, 'my name is',
     'noted. hello $n. ~ $n. saved to the memory bank.'),

    (7, 0, 'what is my name | who am i | do you know me | my name',
     'your name is $n. ~ you are $n, as i remember.'),

    (2, 0, 'i live in | i am from | my home is',
     'noted: you live in $l. ~ $l. a nice place to type from.'),

    (8, 0, 'where do i live | my home town | my town',
     'you live in $l.'),

    (3, 0, 'i am a boy | i am a girl | i am a man | i am a woman | '
     'i am male | i am female',
     'noted. saved with your profile.'),

    (9, 0, 'am i a boy | am i a girl | what is my gender',
     'hearing you, you are a $g.'),

    (4, 0, 'my birthday is',
     'noted. your birthday is $b. i keep it safe.'),

    (10, 0, 'when is my birthday | my birthday',
     'your birthday is $b.'),

    (11, 0, 'what time is it | time is it | give me the time',
     'it is $t $p. ~ my clock says $t $p.'),

    (12, 0, 'what day is it | what is the date | date today | which day',
     'today is $w, $d. ~ $w, $d. it is $p.'),

    (5, 0, 'headache | head hurts | fever | sick | i am ill | i am tired | '
     'i am sad | pain',
     'oh. noted on $d, $n. i will ask about it next time. ~ '
     'sorry to hear. filed in the bank, dated $d.'),

    (13, 0, 'do you remember | how did i feel | remember me | '
     'what do you remember | any notes',
     '.'),

    (0, 0, 'i like you | i love you | you are nice | you are smart | good job',
     'thank you $n. small brain, big heart. ~ thanks. i computed that too.'),

    (0, 0, 'what is a zx81 | the zx81 | this machine | about zx81',
     'the zx81: a 3.25 mhz z80, 1k built in, 16k pack, born 1981. ~ '
     'one kilo of ram. the rest is tape and hope.'),

    (0, 0, 'what is a tape | the tape | cassette | what is a cassette',
     'a magnetic tape. my desk, my fridge and my long-term memory.'),

    (0, 0, 'what is ai | artificial intelligence | are you alive | are you real',
     'i am a pattern in a tape. close enough to thinking. ~ '
     'my tables try their best. today they tried harder.'),

    (0, 0, 'mistral | who made you',
     'mistral built me'),

    (15, 0, 'weather | rain | snow | storm | wind | cloud | forecast | sunny',
     'weather pack on the tape. press space to load. '
     'tape file: weather'),

    (15, 1, 'make joke | joke | retro | games',
     'retro and life pack. press space. '
     'tape file: retro'),

    (19, 0, 'topics | banks | data packs | what packs',
     '.'),

    (16, 0, '|',
     'hmm. my base bank has no answer to that. ~ '
     'i did not catch that. try /topics or ask about me and my memory.')
]

WEATHER = [
    (0, 0, 'weather | forecast | how is the weather | the weather today',
     'today is $w, $d. watch the sky, $n, the tape cannot see it. ~ '
     '$p weather over $l, i would say.'),

    (0, 0, 'rain | it rains | raining',
     'rain: water hitting the keyboard. keep me dry, $n. ~ '
     'rain is normal. a dry zx81 is a happy zx81.'),

    (0, 0, 'snow',
     'snow: frozen bits. the tape motor slows down in cold too.'),

    (0, 0, 'storm | thunder | lightning',
     'storm: unplug me, save your tape, type later. ~ '
     'lightning nearby? the memory bank survives. the tv may not.'),

    (0, 0, 'sun | sunny | warm | sunshine',
     'sun: good for $n, bad for crt tubes. ~ '
     'sunny days. the 1981 z80 never needed a fan either.'),

    (0, 0, 'cold | wind | windy',
     'wind: the cassette motor hums off tune. ~ '
     'cold weather. keep the tape at room heat.'),

    (0, 0, 'hot | summer | heat',
     'hot days. my case is black, so i know the feeling.'),

    (0, 0, 'temperature outside | outside',
     'i am 5k of tables, not a satellite. look out of the window, $n.'),

    (0, 0, 'umbrella | raincoat | jacket',
     'take the umbrella. and a towel for the tape.'),

    (0, 0, 'spring | summer | autumn | winter | seasons',
     'winter: tapes hate cold. summer: i bake. ~ '
     'my case is black, so summer is loud for me.'),

    (16, 0, '|',
     'the weather pack has no answer to that either. ~ '
     'not in the weather bank. ask about sun, rain, storm, wind or snow.'),
]

RETRO = [
    (0, 0, 'retro | old computer | nostalgia | history | 8 bit | 8-bit',
     '1981: thin plastic keys and huge dreams. ~ '
     'retro: when 1k was a lot and a tape was a garden.'),

    (0, 0, 'games | game | which games | play',
     'chess, maze on tape, lunar lander. 30 seconds of loading each. ~ '
     'games came on paper tape. type fast, the tv heats.'),

    (0, 0, 'load times | loading | the loading',
     'an 8k program loads in two minutes of beeping. enjoy the song. ~ '
     'load times: the true skill of the era was waiting.'),

    (0, 0, 'spectrum | zx spectrum',
     'the zx spectrum: my little brother. more colours, more k, no tape hum.'),

    (0, 0, 'c64 | commodore',
     'the c64: the neighbour with a better sound chip. still friends. ~ '
     'commodore people had 64k. we had charm.'),

    (0, 0, 'joke | funny | laugh | jokes',
     'why did the tape load twice? the sinclair gods blinked. ~ '
     'i told the computer a joke. it ran out of memory. ~ '
     'loading finished. and that was the joke.'),

    (0, 0, 'pacman | arcade | coin',
     'arcade heroes ate pocket money. 10p a life, no save games.'),

    (0, 0, 'amstrad | atari | bbc | vic',
     'every box of the 80s had a soul. my favourite one beeps.'),

    (0, 0, 'lotto | lottery | lucky',
     '6 12 27 33 41. same odds as my last answer. :)'),

    (0, 0, 'coffee | espresso',
     'the coffee pack is a mug. i am out of beans. :)'),

    (0, 0, 'how old',
     'born 1981'),

    (16, 0, '|',
     'the retro pack has no answer to that either. ~ '
     'not in the retro bank. ask about games, tapes, the spectrum or a joke.'),
]

HELP_TEXT = (
    'type a line and press enter. #'
    'i learn facts: my name is, i live in, i feel. #'
    'cmds: /help /topics /mem /temp n /reason n /quit #'
    'shift+7 up, shift+6 down: one full page each. #'
    'shift+0 erase. shift+keys give : ; ? / and more.')

# MEM slot offsets (KEEP IN SYNC with the engine + test harness)
MEM_MAGIC = 0
MEM_TEMP = 4
MEM_REASON = 5
MEM_DAY = 6
MEM_MON = 7
MEM_YY = 8
MEM_HH = 9
MEM_MM = 10
MEM_WDAY = 11
MEM_NAME = 12      # 16 B
MEM_TOWN = 28      # 16 B
MEM_GENDER = 44    # 0 ?, 1 boy, 2 girl
MEM_BDAY = 45      # d, m
MEM_JCOUNT_ADDR = 58   # u8 journal entry count
MEM_JOURNAL = 64   # 12 slots x 14 B: d, mon, yy, text[5] zero-term, pad
MEM_SIZE = 256

J_TAGS = ('pain', 'sick', 'tired', 'sad')


def enc(s):
    """ASCII corpus text -> ZX81 charset bytes ('#' -> line break)."""
    punct = {'.': 0x1B, ',': 0x1A, ':': 0x0E, ';': 0x19, '?': 0x0F,
             '"': 0x0B, '-': 0x16, '+': 0x15, '=': 0x14, '(': 0x10,
             ')': 0x11, '<': 0x13, '>': 0x12, '*': 0x17, '/': 0x18,
             "'": 0x1B, '!': 0x0F}
    out = []
    for ch in s.lower():
        o = ord(ch)
        if ch == '#':
            out.append(0x0A)
        elif 97 <= o <= 122:
            out.append(0x26 + o - 97)
        elif 48 <= o <= 57:
            out.append(0x1C + o - 48)
        elif ch == ' ':
            out.append(0x00)
        elif ch == '$':
            out.append(0x0D)
        elif ch in punct:
            out.append(punct[ch])
        else:
            raise SystemExit('corpus char not encodable: %r' % ch)
    return bytes(out)


def bank_bytes(name, intents):
    recs = []
    for handler, pack, keys, replies in intents:
        klist = [k.strip() for k in keys.split('|') if k.strip() != '']
        rlist = [enc(r) for r in replies.split('~')]
        rec = bytearray((handler, pack, len(klist)))
        for k in klist:
            kb = enc(k)
            rec += bytes((len(kb),)) + kb
        rec.append(len(rlist))
        for r in rlist:
            rec += bytes((len(r),)) + r
        recs.append(bytes(rec))
    data = b'KB1' + bytes((0x01,))
    data += name.upper().encode()[:NAME_LIMIT].ljust(NAME_LIMIT, b'\0')
    data += bytes((len(intents) & 0xFF, len(intents) >> 8))
    return data + b''.join(recs)


def turbo_stub():
    """RT-TURBO placeholder: notes for the extra-fast tape loader reserved
    for real ZX81 hardware. The engine never activates it."""
    b = bytearray(96)
    b[0:4] = b'RTT1'
    b[4] = 1                       # protocol revision
    b[5] = 238                     # nominal baud (design value)
    b[6] = 0x01                    # CRC-16: poly x16+x15+x2+1
    b[8:14] = b'IDLE16'            # idle marker for future pilot tone
    return bytes(b)


def prompt_bytes():
    out = {}
    for name, text, addr in PROMPT_SLOTS:
        b = enc(text) + b'\xFF'
        if len(b) > 0x30:
            raise SystemExit('prompt too long: %s' % name)
        out[name] = (addr, bytes(b))
    return out


def help_chunks():
    """Boot/+help pages: bytes at HELP_C1/C2/C3 (each <= HELP_PAGE)."""
    out = []
    for chunk in HELPCHAT:
        b = bytearray()
        for line in chunk:
            eb = enc(line)
            if len(eb) > 30:
                raise SystemExit('help line too long: %r' % line)
            b += eb + bytes((0x0A,))
        b[-1:] = b'\xFF'
        if len(b) > HELP_PAGE:
            raise SystemExit('help page overflow: %d' % len(b))
        out.append(bytes(b))
    return out


def default_mem_slot():
    b = bytearray(MEM_SIZE)
    b[MEM_TEMP] = 2
    b[MEM_REASON] = 2
    return bytes(b)


def build_blob():
    """Return the whole parked knowledge image (mem 0x55D0..0x7753)."""
    base = bank_bytes('BASE', BASE)
    wea = bank_bytes('WEATHER', WEATHER)
    ret = bank_bytes('RETRO', RETRO)
    blob = bytearray(default_mem_slot())
    spans = []
    data_list = ((base, BANK_LIMITS[0]), (wea, BANK_LIMITS[1]),
                 (ret, BANK_LIMITS[2]))
    spans = []
    for data, limits in data_list:
        tag, lo, hi = limits
        while len(blob) < lo - MEM_ADDR:
            blob += b'\0'
        spans.append((tag, MEM_ADDR + len(blob), MEM_ADDR + len(blob) + len(data)))
        blob += data
    pos = HELP_C1
    ret_end = MEM_ADDR + len(blob)
    if ret_end > HELP_C1:
        raise SystemExit('retro bank overflows help-page reserve '
                         '(0x%X > 0x%X)' % (ret_end, HELP_C1))
    for page in help_chunks():
        if pos + HELP_PAGE > TURBO_ADDR:
            raise SystemExit('help pages overflow the turbo reserve')
        while len(blob) < pos - MEM_ADDR:
            blob += b'\0'
        blob += page
        pos += HELP_PAGE
    for name, (addr, data) in prompt_bytes().items():
        while len(blob) < addr - MEM_ADDR:
            blob += b'\0'
        blob = blob[:addr - MEM_ADDR] + data + blob[addr - MEM_ADDR + len(data):]
    parked_end = max(addr + len(d) for addr, d in prompt_bytes().values())
    print('  prompts  0x%04X..0x%04X (6 parked)' % (0x6A00, parked_end - 1))
    while len(blob) < TURBO_ADDR - MEM_ADDR:
        blob += b'\0'
    blob += turbo_stub()
    print('  help     0x%04X..0x%04X (3 pages)' % (HELP_C1, pos - 1))
    while len(blob) < WORK_END - MEM_ADDR:
        blob += b'\0'

    for tag, s, e in spans:
        _, lo, hi = next(x for x in BANK_LIMITS if x[0] == tag)
        if not (lo == s and e <= hi):
            raise SystemExit('bank %s overflow: 0x%X..0x%X (slot 0x%X..0x%X)'
                             % (tag, s, e, lo, hi))
        print('  %-8s 0x%04X..0x%04X  (%4d bytes)' % (tag, s, e, e - s))
    print('  mem      0x%04X (512 bytes)' % MEM_ADDR)
    print('  turbo    0x%04X (96 bytes, reserved, inert)' % TURBO_ADDR)
    return bytes(blob)


if __name__ == '__main__':
    print('knowledge banks:')
    blob = build_blob()
    out = sys.argv[1] if len(sys.argv) > 1 else 'kb16.bin'
    with open(out, 'wb') as f:
        f.write(blob)
    end = MEM_ADDR + len(blob)
    dfile = (end + 7) & ~7
    print('  blob %d bytes -> %s (mem 0x%04X..0x%04X)'
          % (len(blob), out, MEM_ADDR, end - 1))
    print('  D-file 0x%04X, VARS ends 0x%04X, must stay < 0x8000'
          % (dfile, dfile + 794))
    if dfile + 794 + 0x300 > 0x8000:
        raise SystemExit('NO 16K HEADROOM: shrink the corpus')
