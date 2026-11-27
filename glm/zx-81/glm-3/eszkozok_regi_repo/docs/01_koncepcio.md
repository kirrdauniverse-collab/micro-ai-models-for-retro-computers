# 01 — Koncepció: a Pico AI architektúrája (1. fázis)

Ez a dokumentum rögzíti, **mi** a Pico AI, **miért** így épül, és hol vannak a
16 KB-os ZX81 realitásaihoz kényszerű kompromisszumok. A méreteket és a
címeket a 02-es tervezési dokumentum pontosítja.

## 1. A cél egy mondatban

Egy ZX81-en futó, angol nyelvű csevegő „AI", amely **valódi generálással**
(tokenenkénti súlyozott mintavétel + fogalmi újrangsorolás) válaszol, a
tartós és ideiglenes memóriáját kazettán őrzi, és témacsomagokkal bővíthető.

## 2. Mit jelent a „gondolkodás" itt? (realitásvizsgálat)

A ZX81: 8 bites Z80 @ 3,25 MHz, 16 KB RAM, 8 KB ROM, kazettás I/O
(~250 bájt/s gyári sebességgel). Ezen egy GPT-ális transzformer **nem** fut:
már a szótár és a súlymátrix is több lenne a teljes RAM-nál, az int8
matmul pedig per-tokent ~másodpercnyi ideig tartana.

Ami viszont **valóban belefér**, és mégis „modellszerű" (nem IF/THEN):

| LLM fogalom | Pico AI megvalósítás |
|---|---|
| tokenizálás | szóhasítás + toldalék-lehajtás (`-S`, `-ED`, `-ING`) + 256 szavas szótár hash-kereséssel |
| beágyazás / asszociáció | fogalomtábla: minden ismert tokenhez 6 társított token súlyokkal |
| „logits" | bigram-tábla: (előző token → következő jelöltek, súlyok) |
| mintavétel, hőmérséklet | súlyozott véletlen választás; T1..T4 a súlyok laposítását/tompítását állítja |
| gondolkodási fázis | kétlépcsős generálás: 1. jelöltek gyűjtése, 2. a bemenettel átfedés szerinti újrangsorolása (Reasoning be) |
| kontextus | beszélgetési gyűrűpuffer (tokenekben) + emlékbit-mezők |
| tanulás menet közben | ismeretlen szó elraktározása a mondatkörnyezetével, későbbi visszaidézéssel |

A válasz tehát nem sablon: ugyanarra a kérdésre két alkalommal **különböző**
mondatot ad (a hőmérséklettől és a FRAMES-alapú véletlengenerátortól függően),
és a mondat szavait a modell statisztikája választja, nem egy listából
kikeresett kész mondat. Ahol viszont tényről van szó („ki készített?",
„milyen nap van ma?"), ott nem generálunk véletlenszöveget: az identitás
rögzített szöveg, a dátummatematika pedig tényleges számítás.

## 3. A nyelv: angol (a felhasználó döntése)

A felhasználó angol nyelvre váltotta a modellt: a rövidebb szavak, a toldalék-
és ragrendszer hiánya, a nagybetűs ZX81-karakterkészlet miatt **több szó fér
a szótárba, több bigram a tudásbázisba, és a tokenizáló is toleránsabb**
(elgépelésekre is toleránsabb). A magyar témacsomag-formatum marad lehetőség
(a csomag fejlécében él a charset-mező), a v0.1-ben angolul indul.

## 4. Kazetta = háttértár: a multiload koncepció

A `.T81` az EightyOne EO81 formátuma: blokkok láncolata, minden blokk egy
teljes memóriakép 0x4009-től. A Pico kazetta:

```
[PICOBOOT]  FULL kép:  bejelentkező kép, útmutató-kérdés, profil-bekérés
                        (dátum, idő, név, nem, születési év), mentés a
                        D_FILE felső soraiba, majd visszaadja az 1-et →
                        a 2-es BASIC sor LOAD "PICOBASE"-ot hajt végre
[PICOBASE]  SHORT kép: motor + alaptudás-csomag (a D_FILE-t NEM írja felül!)
[PICO…]     SHORT kép: témacsomagok (csillagászat, tudomány, …) — ugyanaz
                        a motor, más tudás; a megtanult szavak és emlékek
                        a képcserék alatt érintetlenek maradnak
```

A `SHORT`/`FULL` lényege: a ZX81 ROM betöltő mindent felülír a kép
hosszáig. Ami a **rövid** képek vége fölött van (profil a D_FILE sorain,
tanult szavak, emlékbit-mezők, chat-gyűrű), az átvészeli a blokkcsereket —
ez a „védett tartós memória" megoldás.

Mentés (`/save`, SHIFT+S): a motor 2-t ad vissza az USR-hívásnak, a 3-as
BASIC sor a ROM saját SAVE parancsát futtatja, ami az egész aktuális képet
(0x4009-től a VARS-jelzőig) kazettára írja — benne a D_FILE-ba csomagolt
profillal, a tanult szavakkal, a chat-gyűrűvel. Így a következő betöltésnél
minden visszaáll.

## 5. Memória-arányok (irányadó → tényleges v0.1)

| zóna | kérés | tényleges v0.1 | megjegyzés |
|---|---|---|---|
| motor/keret | 3–5 KB | ~4,2 KB | tiszta Z80, saját assembler |
| tartós szótár | 2–3 KB | 2,25 KB | 256 szó × 7 B + 512 B hash-index |
| chat history | 2–3 KB | ~1,6 KB | token-gyűrű — l. kompromisszumok |
| tudásbázis | 7–10 KB | ~5,8 KB (alap) + cserélhető csomagok | bigram+fogalom+tervek |
| tartalék | 50–150 B/modul | 64 B + 160 B zóna + modul-onként DS-n | bővítéshez |

**Kompromisszum (őszintén):** a 16 KB-ból a D_FILE (793 B), a rendszer-
változók (116 B), a BASIC-keret (~110 B), az E_LINE-munkaterület és a
verem is lejön — a „7–10 KB tudásbázis + 3 KB chat" együtt nem fér. A
választásom: a tudás prioritást kapott (több téma = több okosság), a chat-
history gyűrűje 1,6 KB-ra zsugorodott (a görgetés így is sok üzenetet mutat
— a képernyő 14 soros, a gyűrő 100+ token-üzenetet őriz). Ha egy későbbi
változatban nagyobb chat kell, a tudásbázis rovására állítható — ez egy
build-kapcsoló (`engine/config.z80: CHAT_RING_SIZE`).

## 6. Ami szigorúan tilos (a hibák tanulsága)

1. **A D_FILE-ban csak érvényes kódok**: 0x00–0x3F normál, 0x80–0xBF inverz,
   0x76 sorvég. Minden más (0x40–0x75, 0x77–0x7F, 0xC0–0xFF) a futó fekete
   csíkokat okozza. A motor minden cellaírást a `putcell` őrző rutinen át
   végez; a szimulátor emellett futásidőben minden írást ellenőriz.
2. **Nem hagyunk a rendszerre semmit**: a képernyő-görgetés, a kurzor, a
   beviteli szerkesztő, a sortördelés mind saját rutin — a ROM scrollja a
   D_FILE teljes területét mozgatná és összekuszálná a tárolt állapotot.
3. **A BASIC-sorok számait $7E+5 bájtos lebegőpontos farok követi**: a ROM
   futásidejű szcennere (S-STK-DEC) enélkül a sor vége mögött keresné a
   számot (a régi „B/2 report" ok).
4. **A modulok közti réseket nem töltjük fel**: utólagos bővítésre tartalék
   (a felhasználó kérése szerint 50–150 bájt modulonként).

## 7. Távlati portok (most nem épülnek)

Spectrum 48/128, C16/64/128, Amiga 500/1200, TVC 64, Enterprise 128,
Primo 32, HT1080Z — a motor Z80-forrásai gépfüggetlenek (a HAL-rutinok egy
táblában), a portolás fő munkája a képernyő- és szalagréteg lesz. A korábbi
GLM-retro-tinyllm projekt port-vázai (C89 HAL) átvehetők később.
