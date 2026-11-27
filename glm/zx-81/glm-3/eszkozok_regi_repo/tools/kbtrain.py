#!/usr/bin/env python3
"""kbtrain.py — Pico AI tudáscsomag-tréner.

Bemenet:  data/topics/*.txt  (soronként egy mondat, kisbetűs angol)
Kimenet:  engine/build/dict.bin  — közös szótár (~2,4 KB)
          engine/build/<téma>.pk — PK01 tudáscsomag a motornak

SZÓTÁR (256 token, 1 bájt/token):
  0x5220 HASHIDX  256 B  nyitott címzés: slot -> token-azonosító (0xFF üres)
  0x5320 FLAGS    256 B  token -> zászlóbájt
  0x5420 OFFS     512 B  token -> u16 eltolás a STRINGS-be
  0x5620 STRINGS ~1400 B [hossz][ZX-karakterkódok...] (max 15 betű)
A hash és a +1-gyel való szondálás bitpontosan egyezik a Z80 motoréval.

Zászlók: 1 kérdésszó, 2 ige, 4 főnév/tartalom, 8 hangulat, 16 trágárság,
32 szám-szó, 64 funkciószó, 128 trigger.

PK01 csomag (a motor 0x5C20-tól olvassa):
  "PK01" ver charset Nconc nplans u16:M u8:xor
  + fogalmak Nconc*8 = [token][osztály][6 társ]
  + bigram-index 512 B: tokenenként u16 kezdőbejegyzés (0xFFFF = nincs)
  + bigramok M*3 = [előző][következő][súly 1..8], előző szerint rendezve
  + tervek nplans*[típus][n][tokenek]
  + kívánság-medence 4*8 token, hangulat-medence, trágárság-medence
  + rögzített szövegek [id][hossz][ZX-kódok]..., 0xFF zár
  + szám-szó tábla 29 token
"""
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from asm import ZXCODE  # noqa: E402

# ------------------------------------------------------------- címek

DICT_HI = 0x5F00
DICT_FL = 0x6000
DICT_OF = 0x6100
DICT_ST = 0x6300
DICT_END = 0x6900

F_QUES, F_VERB, F_NOUN, F_MOOD, F_PROF, F_NUMW, F_FUNC, F_TRIG = \
    1, 2, 4, 8, 16, 32, 64, 128

# ------------------------------------------------------------- szólisták

QUESTION_W = ["WHAT", "WHO", "WHEN", "WHERE", "WHY", "HOW", "IS", "ARE",
              "AM", "WAS", "WERE", "DO", "DOES", "DID", "CAN", "COULD",
              "WOULD", "SHOULD", "WILL", "DONT", "DOESNT"]
FUNC_W = ["I", "YOU", "HE", "SHE", "IT", "WE", "THEY", "ME", "MY", "YOUR",
          "A", "AN", "THE", "AND", "OR", "BUT", "IF", "THEN", "SO", "TO",
          "OF", "IN", "AT", "ON", "FROM", "WITH", "ABOUT", "FOR", "AS",
          "BY", "LIKE", "THIS", "THAT", "NOT", "NO", "YES", "TOO", "VERY",
          "THERE", "HERE", "ITS", "OLD", "NEW", "BIG", "SMALL", "GOOD",
          "BAD", "LITTLE", "ALL", "UP", "DOWN", "OUT", "ONE"]
VERB_W = ["LIKE", "KNOW", "SAY", "THINK", "SEE", "LOOK", "MAKE", "TAKE",
          "WANT", "NEED", "TELL", "ASK", "WORK", "TALK", "HEAR", "FEEL",
          "FIND", "SAVE", "LOAD", "STOP", "HELP", "LEARN", "GIVE", "GO",
          "GOES", "KEEP", "TURN", "USE", "HURT", "HURTS", "SPEAK", "MEAN",
          "WONDER", "DREAM", "LIVE", "TRY", "PLAY", "READ", "WALK"]
NOUN_W = ["TIME", "DAY", "NIGHT", "WEEK", "YEAR", "HOUR", "TODAY",
          "TOMORROW", "YESTERDAY", "MAN", "WOMAN", "HUMAN", "ROBOT",
          "MACHINE", "WORLD", "LIFE", "FRIEND", "HEAD", "MEMORY", "TAPE",
          "SCREEN", "WORD", "TOKEN", "MODEL", "MIND", "QUESTION",
          "ANSWER", "GLM", "PICO", "ZX81", "LANGUAGE", "NAME", "HOME",
          "SKY", "STAR", "SUN", "MOON", "EARTH", "LIGHT", "WATER", "AIR",
          "SPACE"]
MOOD_W = ["HAHA", "HIHI", "HEHE", "WOW", "OOH", "NOOO", "AAH", ":)", ":(",
          ":O", "HOHO", "OOPS"]
PROF_W = ["FUCK", "SHIT", "DAMN", "CRAP", "ASS", "HELL"]
NUMW = ["ZERO", "ONE", "TWO", "THREE", "FOUR", "FIVE", "SIX", "SEVEN",
        "EIGHT", "NINE", "TEN", "ELEVEN", "TWELVE", "FIFTEEN", "TWENTY",
        "THIRTY", "FORTY", "FIFTY", "HUNDRED"]
WEEKDAY_NAMES = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY",
                "FRIDAY", "SATURDAY", "SUNDAY"]   # a motor sajat tablaja
TRIGG_W = ["OTHER", "TOPIC", "QUIT", "COLOR", "SUMMER", "SWALLOW",
           "PROVERB", "HUNGARIAN", "ENGLISH", "HELP"]
EXTRA_W = ["HELLO", "HI", "BYE", "THANKS", "PLEASE", "OK", "SORRY", "OH",
           "WAIT", "LOVE", "BEST", "TRUE", "FREE", "SMILE", "HOPE", "TINY",
           "WATCH", "WORDS", "EARS", "VIBES"]

FIXED_STRINGS = [
    (0, "MADE WITH GLM HELP BY SAFAR SANDOR"),
    (1, "A BUS DRIVER IN HUNGARY. AMATEUR WRITER AND ASTRONOMER."),
    (2, "SAFIZX81"),                     # utána inverz 0 ( @ ) + GMAIL.COM
    (3, "GMAIL.COM"),
    (4, "I SPEAK ENGLISH ONLY, BUT I KNOW SZIA."),
    (5, "ONE SWALLOW DOES NOT MAKE A SUMMER."),
    (6, "PICO AI: A TINY MIND ON A TINY MACHINE."),
    (7, "SAVING MY MEMORY TO TAPE..."),
    (8, "MEMORY SAVED. LOAD ME AGAIN ANYTIME."),
    (9, "WHAT SHOULD I KNOW ABOUT IT? TELL ME MORE."),
    (10, "IF I WERE HUMAN FOR ONE DAY I WOULD"),
    (11, "YOUR HEAD... I WILL ASK ABOUT IT."),
    (12, "I AM "),
    (13, "DAYS OLD."),
    (14, "TODAY IS "),
    (15, "WHAT ABOUT"),
    (16, "I THINK"),
]

# kívánság-medencék: „mit tennél, ha egy napra ember lehetnél?"
# fix szélesség: ige 1, tárgy 2, hely 2, idő 2 szó (a motor így indexel)
WISH_VERBS = ["TASTE", "HUG", "SING", "SLEEP", "RUN", "CRY", "LAUGH",
              "WALK"]
WISH_OBJS = ["WARM BREAD", "REAL RAIN", "LONG ROADS", "OLD MUSIC",
             "A CAT", "THE SEA", "GOOD FOOD", "A DREAM"]
WISH_PLACES = ["A FOREST", "THE SUN", "MY STREET", "THE RIVER",
               "A HILL", "MY HOME", "A GARDEN", "THE RAIN"]
WISH_TIMES = ["AT SUNRISE", "ALL DAY", "ONE HOUR", "AT NIGHT",
              "EVERY DAY", "NO TIME", "ONE TIME", "THE MORNING"]

# fix szélesség: hangulat-bejegyzések 2 token, trágárság 3 token
MOOD_POOLS = {
    "JOY":   [["I", "LIKE"], ["GOOD", "VIBES"], ["HI", "FRIEND"]],
    "WOW":   [["MY", "WORD"], ["OH", "WOW"], ["WOW", "WAIT"]],
    "SAD":   [["I", "SEE"], ["OH", "NO"], ["SORRY", "FRIEND"]],
    "SHOCK": [["OH", "DEAR"], ["THAT", "NEW"], ["WAIT", "WHAT"]],
}
SASS_POOL = [["WATCH", "YOUR", "WORDS"], ["SAY", "THAT", "AGAIN"],
             ["MIND", "THE", "TAPE"], ["WORDS", "CAN", "HURT"]]

BASE_WORDS = (QUESTION_W + FUNC_W + VERB_W + NOUN_W + MOOD_W + PROF_W
              + NUMW + TRIGG_W + EXTRA_W + WISH_VERBS
              + [t for g in (WISH_OBJS, WISH_PLACES, WISH_TIMES)
                 for w in g for t in w.split()]
              + [t for k in MOOD_POOLS for s in MOOD_POOLS[k] for t in s]
              + [t for s in SASS_POOL for t in s])


# ------------------------------------------------------------- hash + szótár

def zx_code_of(ch):
    return ZXCODE.get(ch.upper(), None)


def word_codes(word):
    out = []
    for c in word:
        z = zx_code_of(c)
        if z is None or z == 0:
            return None
        out.append(z)
    if not (1 <= len(out) <= 15):
        return None
    return bytes(out)


def zxhash(codes):
    """A Z80 motorral BITPONTOSAN egyező hash: bájtonként RLC majd XOR,
    a végén + hossz (mod 256)."""
    h = 0
    for c in codes:
        h = ((h << 1) | (h >> 7)) & 0xFF
        h ^= c
    return (h + len(codes)) & 0xFF


def flags_for(w, is_corpus=False):
    f = 0
    if w in QUESTION_W:
        f |= F_QUES | F_FUNC
    if w in FUNC_W:
        f |= F_FUNC
    if w in VERB_W:
        f |= F_VERB
    if w in NOUN_W:
        f |= F_NOUN
    if w in MOOD_W:
        f |= F_MOOD
    if w in PROF_W:
        f |= F_PROF
    if w in NUMW:
        f |= F_NUMW
    if w in TRIGG_W:
        f |= F_TRIG
    if is_corpus and not f:
        f |= F_NOUN          # korpuszszó alapértelmezetten tartalomszó
    return f


def build_dict(vocab_with_prio):
    """vocab_with_prio: [(szó, prioritás)] — az azonos prefixű szavak közül
    a nagyobb prioritású marad. Nyitott címzés HASHIDX-be."""
    seen = {}
    for w, prio in vocab_with_prio:
        if w in seen and seen[w] >= prio:
            continue
        seen[w] = prio
    words = sorted(seen, key=lambda w: (-seen[w], w))
    hashidx = [0xFF] * 256
    flags = [0] * 256
    offs = [0] * 256
    strings = bytearray()
    ids = {}
    collisions = 0
    for w in words[:256]:
        codes = word_codes(w)
        if codes is None:
            continue
        tid = len(ids)
        home = zxhash(codes)
        pos = home
        while hashidx[pos] != 0xFF:
            pos = (pos + 1) & 0xFF
            collisions += 1
        hashidx[pos] = tid
        flags[tid] = flags_for(w, is_corpus=(seen[w] == 0))
        offs[tid] = len(strings)
        strings += bytes([len(codes)]) + codes
        ids[w] = tid
    blob = bytearray(DICT_END - DICT_HI)
    blob[0:256] = bytes(hashidx)
    blob[256:512] = bytes(flags)
    for t, o in enumerate(offs):
        blob[512 + 2 * t] = o & 0xFF
        blob[513 + 2 * t] = o >> 8
    blob[1024:1024 + len(strings)] = strings
    return bytes(blob), ids, {"szavak": len(ids), "utkozes": collisions,
                              "string_bajt": len(strings)}


# ------------------------------------------------------------- korpusz

def read_corpus(path):
    sents = []
    for raw in open(path, encoding="utf-8"):
        words = []
        for tok in raw.strip().upper().split():
            w = "".join(ch for ch in tok if zx_code_of(ch) is not None
                        and zx_code_of(ch) != 0)
            if w:
                words.append(w)
        if words:
            sents.append(words)
    return sents


def bigrams_from(sents, ids):
    cnt = Counter()
    for words in sents:
        toks = [ids[w] for w in words if w in ids]
        for a, b in zip(toks, toks[1:]):
            if a != b:
                cnt[(a, b)] += 1
    out = [(a, b, min(8, c)) for (a, b), c in cnt.items()]
    out.sort()
    return out


def concepts_from(sents, ids, flags, maxn=48):
    co = Counter()
    for words in sents:
        toks = [ids[w] for w in words if w in ids]
        uniq = sorted(set(t for t in toks if flags[t] & F_NOUN))
        for i, a in enumerate(uniq):
            for b in uniq[i + 1:]:
                co[(a, b)] += 1
    deg = Counter()
    for (a, b), v in co.items():
        deg[a] += v
        deg[b] += v
    nouns = [t for t in deg if flags[t] & F_NOUN and not flags[t] & F_FUNC]
    nouns.sort(key=lambda t: -deg[t])
    out = []
    for t in nouns[:maxn]:
        assoc = Counter()
        for (a, b), v in co.items():
            if a == t:
                assoc[b] += v
            elif b == t:
                assoc[a] += v
        best = [x for x, _ in assoc.most_common(6)]
        out.append((t, flags[t], (best + [0] * 6)[:6]))
    return out


# ------------------------------------------------------------- csomag

def make_pack(topic, sents, ids, flags):
    bigrams = bigrams_from(sents, ids)
    concepts = concepts_from(sents, ids, flags)
    starts = [0xFFFF] * 256
    for i, (prev, nxt, w) in enumerate(bigrams):
        if starts[prev] == 0xFFFF:
            starts[prev] = i

    def tid(w):
        return ids.get(w, 0)

    plans = [
        (0, [tid("I"), 0xFE, 0xFD, 0xFC, 0xFF]),       # I <ige> <tárgy> <vége>
        (0, [tid("YOU"), 0xFD, 0xFC, 0xFE, 0xFF]),
        (1, [tid("WHAT"), tid("ABOUT"), 0xFE, 0xFF]),
        (3, [0xFE, tid("IS"), 0xFC, 0xFF]),
    ]
    pool_tokens = []
    for grp in (WISH_VERBS, WISH_OBJS, WISH_PLACES, WISH_TIMES):
        for w in grp:
            pool_tokens.extend(ids.get(t, 0) for t in w.split())
    mood_tokens = []
    for k in ("JOY", "WOW", "SAD", "SHOCK"):
        for seq in MOOD_POOLS[k]:
            mood_tokens.extend([ids.get(t, 0) for t in seq])
    sass_tokens = []
    for seq in SASS_POOL:
        sass_tokens.extend([ids.get(t, 0) for t in seq])

    body = bytearray()
    body += bytes([len(concepts), len(plans),
                   len(bigrams) & 0xFF, len(bigrams) >> 8])
    for tok, fl, assoc in concepts:
        body += bytes([tok, fl] + assoc)
    for s in starts:
        body += bytes([s & 0xFF, s >> 8])
    for prev, nxt, w in bigrams:
        body += bytes([prev, nxt, w])
    for typ, seq in plans:
        body += bytes([typ, len(seq)]) + bytes(seq)
    # wish: [56 token] (8x1 + 8x2 + 8x2 + 8x2), fix elrendezésben
    assert len(pool_tokens) == 56, len(pool_tokens)
    body += bytes(pool_tokens)
    # mood: 12 bejegyzés x 2 token
    assert len(mood_tokens) == 24, len(mood_tokens)
    body += bytes(mood_tokens)
    # sass: 4 bejegyzés x 3 token
    assert len(sass_tokens) == 12, len(sass_tokens)
    body += bytes(sass_tokens)
    for sid, text in FIXED_STRINGS:
        codes = bytes(ZXCODE.get(c, 0) for c in text)
        body += bytes([sid, len(codes)]) + codes
    body += b"\xff"
    body += bytes([ids.get(w, 0) for w in NUMW])
    x = 0
    for b in body:
        x ^= b
    hdr = b"PK01" + bytes([1, 0, x])
    while (len(hdr) + len(body)) % 16:
        body += b"\x00"
    return bytes(hdr) + bytes(body), {
        "fogalom": len(concepts), "bigram": len(bigrams),
        "csomag_bajt": len(hdr) + len(body)}


# ------------------------------------------------------------- főprogram

def main():
    here = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(here, "..", "data", "topics")
    out_dir = os.path.join(here, "..", "engine", "build")
    os.makedirs(out_dir, exist_ok=True)
    topics = sorted(f[:-4] for f in os.listdir(data_dir)
                    if f.endswith(".txt"))
    freq = Counter()
    corpora = {}
    for t in topics:
        sents = read_corpus(os.path.join(data_dir, t + ".txt"))
        corpora[t] = sents
        for words in sents:
            freq.update(words)

    # MAG-lista: ezek minden körülmények között bent maradnak (elemző,
    # medencék, számok, nyelvtani minimum); a többi gyakoriság szerint
    # versenyez a szabad slotokért (a kézi listák 1-es bázisgyakorisággal
    # indulnak, a korpuszszavak a valós gyakoriságukkal).
    core = set(QUESTION_W + MOOD_W + PROF_W + TRIGG_W + NUMW + EXTRA_W)
    core |= {t for g in (WISH_VERBS, WISH_OBJS, WISH_PLACES, WISH_TIMES)
             for w in g for t in w.split()}
    core |= {t for k in MOOD_POOLS for s in MOOD_POOLS[k] for t in s}
    core |= {t for s in SASS_POOL for t in s}
    core |= {"I", "YOU", "HE", "SHE", "IT", "WE", "THEY", "ME", "MY",
             "YOUR", "A", "AN", "THE", "AND", "OR", "BUT", "NOT", "NO",
             "YES", "TOO", "VERY", "TO", "OF", "IN", "AT", "ON", "WITH",
             "ABOUT", "FOR", "BY", "LIKE", "THIS", "THAT", "IS", "ARE",
             "AM", "DO", "DOES", "WHAT", "WHO", "WHEN", "WHERE", "WHY",
             "HOW", "GLM", "PICO", "ZX81", "TOPIC", "GOOD", "BAD", "OLD",
             "NEW", "BIG", "SMALL", "LITTLE", "TRUE", "SORRY", "HI"}
    if len(core) > 170:
        print(f"FIGYELEM: mag-lista {len(core)} szó — nagyon szoros lesz")
    pool = [(w, 1) for w in FUNC_W + VERB_W + NOUN_W if w not in core]
    pool += [(w, c) for w, c in freq.items() if w not in core]
    pool.sort(key=lambda wc: (-wc[1], wc[0]))
    nfree = 256 - len(core)
    vocab = [(w, 2) for w in core] + [(w, 1) for w, _ in pool[:nfree]]
    dict_blob, ids, stats = build_dict(vocab)
    flags = dict_blob[256:512]
    open(os.path.join(out_dir, "dict.bin"), "wb").write(dict_blob)
    print(f"szótár: {stats['szavak']} szó (mag {len(core)} + gyakorisági "
          f"{nfree}), {len(dict_blob)} B, "
          f"strings {stats['string_bajt']} B, {stats['utkozes']} ütközés")
    missing = sorted(set(freq) - set(ids))
    if missing:
        print(f"FIGYEELMEZTETÉS: {len(missing)} korpuszszó nem fért a "
              f"szótárba: {' '.join(missing[:30])}")
    total = 0
    for t in topics:
        pack, pstats = make_pack(t, corpora[t], ids, flags)
        open(os.path.join(out_dir, t + ".pk"), "wb").write(pack)
        print(f"csomag {t:12s}: {pstats['fogalom']:3d} fogalom, "
              f"{pstats['bigram']:4d} bigram, {pstats['csomag_bajt']:5d} B")
        total += pstats["csomag_bajt"]
    print(f"összesen {total} B tudáscsomag + {len(dict_blob)} B szótár")
    return 0


if __name__ == "__main__":
    sys.exit(main())
