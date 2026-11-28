#!/usr/bin/env python3
"""MILO_v0.2_ZX81_KB.py - knowledge banks for the ZX81 AI 16K cassette.

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

MEM_ADDR = 0x5EC0
BASE_ADDR = 0x60C0
PACK_WEATHER = 0x68E0
PACK_RETRO = 0x70A0
TURBO_ADDR = 0x7290
OUTBUF_ADDR = 0x72F0
LINEIN_ADDR = 0x73F0
MISC_ADDR = 0x7460
HIST_ADDR = 0x7480
WORK_END = 0x7903          # HIST ring end; the D-file is built from here

PROMPT_RESERVE = 0x6F20     # parked prompts live in the weather slot tail

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
    ('PH_HELP',  'want help with usage? (y/n)', 0x6F20),
    ('PH_DATE',  'date? dd mm yy (like 21 11 26)', 0x6F50),
    ('PH_TIME',  'time? hh mm (like 9 30)', 0x6F80),
    ('PH_NAME',  'your name?', 0x6FB0),
    ('PH_CALL',  'how may i call you? (enter)', 0x6FE0),
    ('PH_CARE',  'last time you felt bad. all good now? (y/n)', 0x7010),
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
    (0, 0, "hi | hello | hey", "hello $n. what shall we explore?"),
    (0, 0, "how are you | are you ok", "i am fine. small machine, busy mind."),
    (17, 0, "who are you | your name | what are you", "i am milo, a micro intelligent language organism for the zx81."),
    (0, 0, "who made you | who built you | mistral", "milo was made and trained by the mistral model, from the design of safar sandor."),
    (0, 0, "who is safar | who is safar sandor", "Magyarorszagon elo buszvezeto, hobbi csillagasz es programozo (safizx81@gmail.com), amator iro (Alexander Steward iroi even)."),
    (0, 0, "who designed you | whose idea", "the idea and plan came from safar sandor. the original model work came through mistral."),
    (0, 0, "what is kirrda | kirrda", "kirrda is a science fiction adventure by safar sandor, written as alexander steward. aliens catch an old earth tv broadcast, then a catastrophe drives survivors toward earth and new friends."),
    (0, 0, "write a short story | tell me a story | story", "a bus rolled through the night. a strange light stopped above the trees. the driver looked up and smiled: at last, someone else was watching.~the old computer woke after midnight. its tape motor clicked once. a message appeared: do not look at the moon. naturally, the owner looked up.~on a quiet planet, a child found a radio signal hidden in the noise. it came from far away. the child kept listening."),
    (0, 0, "teach me | how to teach you", "teach me with simple facts and sentences. general learning is still experimental."),
    (0, 0, "draw | drawing | can you draw", "yes. ask for a zx81 plot or a simple drawing."),
    (0, 0, "program | programming | write code", "yes. ask for a short zx81 basic program."),
    (0, 0, "what time is it | what is the time", "it is $t $p."),
    (0, 0, "set time | change time | time is", "use /time hh mm."),
    (0, 0, "remind me | reminder", "use /remind n. for example /remind 2."),
    (0, 0, "help | commands", "use /help. also /topics, /time hh mm, /remind n, /temp n, /reason n, /mem, /save and /forget."),
    (19, 0, "topics | what topics | subjects", "."),
    (15, 1, "knowledge | knowledge pack", "knowledge pack on tape. press space to load."),
    (15, 2, "games | game pack", "games pack on tape. press space to load."),
    (16, 0, "|", "i do not know that yet. ask /topics or teach me a fact."),
]

WEATHER = [
    (0, 1, "health | medicine | body", "health can cover sleep, exercise, food and basic biology. i am not a doctor."),
    (0, 1, "philosophy | ethics | meaning", "philosophy asks what is true, good and meaningful."),
    (0, 1, "learning | study | school", "learn in steps: question, example, practice, feedback."),
    (0, 1, "elementary school | primary school", "reading, maths, nature, history and simple science."),
    (0, 1, "secondary school | high school", "algebra, physics, chemistry, history, literature and computing."),
    (0, 1, "art | painting | sculpture", "art can represent, question, decorate or surprise."),
    (0, 1, "music | song | melody | rhythm", "melody is pitch in sequence; rhythm is timing; harmony is simultaneous pitch."),
    (0, 1, "astronomy | stars | planets | universe", "stars shine by fusion; planets mostly reflect light."),
    (0, 1, "programming | basic | z80 | assembly", "programming is precise instructions for a machine with no mercy for ambiguity."),
    (0, 1, "cars | automobile | engines | brakes", "cars combine propulsion, steering, braking, suspension and electronics."),
    (0, 1, "motorcycles | motorbike | motorcycle", "motorcycles are compact machines with an engine, frame and two wheels."),
    (0, 1, "retro | old computers | 8 bit | zx81", "retro computing means tiny memory, clever tricks and patient loading tapes."),
    (0, 1, "kirrda | kirrda book | science fiction", "kirrda shows a possible first contact from the alien side, then disaster and a search for a new home on earth."),
    (0, 1, "draw a sine wave | plot sine", "10 FOR N=0 TO 63 #20 PLOT N,22+20*SIN(N/32*PI) #30 NEXT N"),
    (0, 1, "basic clock | write a clock", "10 FOR T=0 TO 10000 #20 PRINT T #30 PAUSE 50 #40 GOTO 10"),
    (16, 1, "|", "try health, philosophy, learning, art, music, astronomy, cars or kirrda."),
]

RETRO = [
    (0, 2, "games | game", "number game, riddle, quiz, chess, adventure."),
    (0, 2, "number game | guess a number", "think 1 to 10. i will narrow it down."),
    (0, 2, "riddle | puzzle", "riddle: face and two hands, no arms?"),
    (0, 2, "true or false | quiz", "zx81 uses z80. true or false?"),
    (0, 2, "chess | chess game", "move like e2 e4. engine later."),
    (0, 2, "adventure | text adventure", "locked observatory. left forest, right tower."),
    (16, 2, "|", "games: number, riddle, quiz, chess, adventure."),
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
        elif ch == '@':
            out.append(0x9C)
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
    """Return the parked MILO image from MEM through WORK_END."""
    base = bank_bytes('BASE', BASE)
    wea = bank_bytes('KNOWLEDGE', WEATHER)
    ret = bank_bytes('GAMES', RETRO)
    blob = bytearray(default_mem_slot())
    spans = []
    data_list = ((base, BANK_LIMITS[0]), (wea, BANK_LIMITS[1]),
                 (ret, BANK_LIMITS[2]))
    for data, limits in data_list:
        tag, lo, hi = limits
        while len(blob) < lo - MEM_ADDR:
            blob += b'\0'
        start = MEM_ADDR + len(blob)
        end = start + len(data)
        if end > hi:
            raise SystemExit('bank %s overflow: 0x%X..0x%X (slot 0x%X..0x%X)'
                             % (tag, start, end, lo, hi))
        spans.append((tag, start, end))
        blob += data

    for name, (addr, data) in prompt_bytes().items():
        while len(blob) < addr - MEM_ADDR:
            blob += b'\0'
        off = addr - MEM_ADDR
        blob[off:off + len(data)] = data

    while len(blob) < TURBO_ADDR - MEM_ADDR:
        blob += b'\0'
    blob += turbo_stub()

    while len(blob) < WORK_END - MEM_ADDR:
        blob += b'\0'

    for tag, start, end in spans:
        print('  %-8s 0x%04X..0x%04X (%4d bytes)' %
              (tag, start, end, end - start))
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
