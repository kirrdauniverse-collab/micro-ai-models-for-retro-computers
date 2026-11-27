# 02 — Tervezés: memóriatérkép, sávstruktúra, működés (2. fázis)

Minden cím és méret a v0.1 tényleges megvalósítását tükrözi
(`engine/config.z80`-ból; a build kiírja a valós számokat is).

## 1. Memóriatérkép (16 KB RAM, 0x4000–0x7FFF)

```
0x4000–0x4008   ROM-függő rögzített terület (FLAGS = 0x4001)
0x4009–0x407C   rendszer-változók (116 B) — a .P/.T81 kép innen indul
0x407D          1 REM <MOTOR>            — a kód 0x4082-től indul (16514)
                1-es sor törzsének végén: 64 B TARTÓS FAROK (profil-másolat,
                pending-akció, téma-azonosító) — a ROM SAVE így kiírja
                2 IF USR 16514 = 1 THEN LOAD "PICOBASE"
                3 IF USR 16514 = 2 THEN SAVE "PICOBASE"
                0x76 programsor-vég jelző
0x4082–0x5220   MOTOR ~4,2 KB (boot, bevitel, tokenizáló, elemző,
                generátor, biztonságos képernyő, memória, szalag-híd)
0x5220–0x5B20   SZÓTÁR 2,25 KB: 256 szó × 7 B + 512 B hash-index
0x5B20–0x7120   ALAPTUDÁS "PK01" csomag ~5,8 KB (témacserével felülírandó)
0x7120–0x7160   tartalék 64 B (motor-oldali bővítéshez)
0x7160–0x73E0   TANULT-ZÓNA 640 B (rövid képek SOSEM írják felül):
                - 32 ideiglenes szó + mondatkörnyezet-bigram
                - emlékesemények (nap-bélyeggel, lejárattal)
                - bitmező bájtjai, téma-azonosító, hőmérséklet/gondolkodás
0x73E0–0x7A5F   CHAT-GYŰRŰ ~1,6 KB (token-üzenetek + időbélyeg)
0x7A60–0x7AFF   tartalék 160 B (adat-oldali bővítéshez)
0x7B00–0x7E18   D_FILE 793 B:
                  sor 0–2   csomagolt tartós állapot (6 bites cellák)
                  sor 3     státuszsor (inverz)
                  sor 4–17  csevegő-konzol (saját kurzor + görgetés)
                  sor 18    gondolkodás-sáv (animált)
                  sor 19–21 beviteli sor + prompt + token-számláló
                  sor 22–23 a ROM alsó képernyője (DF_SZ=2; nem nyúlunk hozzá)
0x7E19          VARS 0x80 jelző (a FULL kép vége)
0x7E1A…         E_LINE munkaterület (a ROM építi)
0x7FFD↓         gépi verem
```

**Ellenőrzött ZX81 tények, amikre ez épül** (forrás: a régi projekt hármas
ellenőrzése — z88dk appmake referencia, valódi ARTILLER.P, emulátor-írta
demo.T81 — plusz a ROM-disassembly): D_FILE = 0x400C; a D_FILE a **vezető**
0x76-ra mutat, a sor r első cellája `D_FILE+1+33*r`; a sorok száma BE, a
hosszak LE bájtsorrendben; az 0x4026-os szó a verem-tetej forrása
gyorsbetöltéskor; FRAMES = 0x4034, csak SLOW módban jár.

## 2. A `.T81` kazetta sávstruktúrája

```
EO81 mágia, majd blokkonként:  név[32] + hossz[16 ASCII] + adat
  1. PICOBOOT  FULL  ~2,9 KB  bejelentkező kép + profil-bekérés
  2. PICOBASE  SHORT ~15,3 KB motor + szótár + alaptudás
  3. PICOASTR  SHORT ~13,9 KB motor + szótár + csillagászat-csomag
  4. PICOSCIN  SHORT ~13,9 KB motor + szótár + tudomány-csomag
```

- **FULL** = a kép a D_FILE-fal és a VARS-jelzővel együtt ér véget → friss
  gépen érvényes megjelenítőt kap (a megjelenítő-generátor sosem szalad el).
- **SHORT** = a kép 0x7120 előtt véget ér → a D_FILE (a profil-csomagkal!) és
  a tanult-zóna érintetlen marad a csere alatt.
- A láncolás BASIC-ből: `2 IF USR 16514 = 1 THEN LOAD "PICOBASE"`. A motor a
  kilépés ELŐTT átírja a LOAD nevét a 2-es sor név-mezőjébe (a v0.6.5-ben
  bizonyított trükk), majd 1-et ad vissza → a ROM LOAD névre keres a
  kazettán, betölt, és a betöltött program az 1. sorától újraindul.
- Mentés: a motor 2-t ad vissza → `3 … SAVE "PICOBASE"` a ROM saját SAVE-je
  kiírja az egész képet (benne: D_FILE-ba csomagolt profil, tanult szavak,
  chat-gyűrű, tartós farok). A következő munkamenet pont ide tér vissza.
- **Téma-váltás**: `/TOPIC n` szöveges parancs → a névtáblából (motor
  végén) az n-edik név a LOAD-név-mezőbe, pending=1, kilépés → lánc.
- A névmező 8 display-kód bájt (a ROM LOAD bájtonként hasonlít).

## 3. Képernyő- és D_FILE-szabályok (a „fekete csík" törvényei)

A ZX81 megjelenítője a D_FILE bájtból veszi a karaktert: **6 alsó bit** = a
karakter kódja (0–63), **bit 7** = inverz (0x80–0xBF), **0x76** = sorvég.
Minden más érték (0x40–0x75, 0x77–0x7F, 0xC0–0xFF) a képernyő-ütemezést
töri meg → **a borderen átfutó fekete csíkok** ( pontosan a régi hiba).

A motor ezért:

1. `putcell(r,c,érték)`: az értéket maszkolja `AND 0x3F`, majd bit 7
   külön kerül rá — érvénytelen bájt a D_FILE-ba **matematikailag sem
   kerülhet**; az író rutin emellett címőr-táblával a D_FILE-tartományba
   eső közvetlen írást is kizárja (debug-örömmel jelent).
2. A szövegkimenet `putchar`: ASCII→ZX-kódot egy 96 bájtos tábla ad, az
   ismeretlen karakter szóközzé válik (a ZX81-ben nincs `!`, `'`, `@`).
3. Az inverz fejlécek (státuszsor, üzenet-fejlécek) 0x80+0x3F körben
   állnak elő — az inverz Q–Z (0xB6–0xBF) itt **érvényes**, mert az inverz
   a 7. bit, nem a 6. (a 6. bit beállítása okozna 0x76-os ütközést — ezt a
   régóta ismert csapdát a putcell szerkezete zárja ki).
4. A D_FILE felső harmada munkaterület: a 0–2. sorok a csomagolt állapot
   cellái (3 bájt → 4 cella, 6 bit/cella ⇒ csak 0x00–0x3F jöhet ki —
   inherently biztonságos), a 18. sor a gondolkodás-animáció.
5. A szimulátor futás közben minden D_FILE-írást ellenőriz és hibát dob
   tilos kódra — a hibaosztály fejlesztés közben azonnal látszik.

## 4. Bitmezők: 1 bit = 1 tulajdonság (kérés szerint)

A `bits` bájt (a csomagolt állapotban és a tartós farokban is):

```
bit0  nem         0=férfi, 1=nő           bit4  fáj a feje most
bit1  gyerek-e    0=felnőtt, 1=gyerek     bit5  kérdezzen-e az emlékre
bit2  angol-e apreferred? (foglalt)       bit6  gondolkodás (reasoning) be
bit3  trágár-hangnem ebben a menetben     bit7  (foglalt)
```

Az emlékesemények (`events[8]`, 2 bájt/esemény): `[bit-index | napók óta
eltelt nap 7 bit]` — a lejárat számítása: `ma_nap - esemény_napja > 6`
→ az esemény **elavult**, a bit törlődik, és a modell később új
információval írja felül (a „kedden fájt a fejem" példa pontosan így él:
kedden bit=1; következő beszélgetésben, ha <7 nap, rákérdez; ha elmúlt,
törli és nem hozza fel többé).

A bitmező-összeállásból így sosem keletkezik a D_FILE-ban tilos érték: a
csomagolt cellák eleve 6 bitesek (≤ 0x3F).

## 5. Vezérlőbillentyűk

| funkció | billentyű | megjegyzés |
|---|---|---|
| hőmérséklet T1–T4 | SHIFT+1..4 | a mintavétel súlyának laposítása |
| gondolkodás be/ki | SHIFT+9 | második, újrangsoroló generálási menet |
| görgetés fel/le | SHIFT+5 / SHIFT+6 | a chat-gyűrűben lapoz |
| mentés | SHIFT+S (nyers S + shift) | → pending=2 → ROM SAVE |
| megszakítás | RUBOUT (SHIFT+0) | generálás közben megszakítja a választ |
| szóköz | SHIFT+NEWLINE | a ZX81-nek nincs space billentyűje |
| küldés | NEWLINE | beviteli sor lezárása |

Beviteli szerkesztő: saját kurzor, RUBOUT = karaktertöröl, túlfutásnál
sorgörgetés. A **ROM INPUT parancs-rutinját (0x0EE9) direktben gépi kódból
nem lehet biztonságosan hívni** (a BASIC-értelmező futásidejű kontextusát —
PPC, FLAGX, E_LINE-szerkesztő — feltételezi; a ROM-disassembly alapján
dokumentálva). Ehelyett a bevitel **karakteres módban** működik, pontosan
úgy, ahogy a ROM INPUT-belsője is: 8×5-ös mátrixszken port-FE-n (a ROM
KEYBOARD rutinjával azonos séma), a dekódolást a saját 40+40 bájtos
tábláink végzik (a ROM 0x007E/0x00A5 tábláinak megfelelői). Így a
SHIFT-billentyűk nyers szintű észlelése is megvan — a vezérlők
nem ütköznek a BASIC-tokenekkel.

## 6. Tokenizáló és elemző

1. Karakterek szavakra hullása; SHIFT+NEWLINE → szóköz.
2. Kisbetűsítés (a ZX81 csak nagybetűs glifákat rajzol; a chat logikája
   kisbetűs — kiíráskor a ZX úgyis nagybetűt mutat).
3. Toldalék-lehajtás: `-S` (többes), `-ED` (múlt), `-ING` → alapalak +
   jelzőbitek („múlt idő" és „többes szám" felfedhető és jelzhető a válasz
   nyelvtanában: `I LIKED → I LIKE… TOO, YESTERDAY` stb.).
4. Szótár-keresés: hash = (első+utolsó+hash(2. betű)) mod 512, lineáris
   probálás; találat → token-azonosító + szóosztálybitek.
5. **Ismeretlen szó** (elgépelés, új szó): fuzzy illesztés — hossz ±1,
   első 2 + utolsó betű egyezése, köztes bitek távolsága → legjobb
   jelölt; ha nincs: a szó a **tanult-zónába** kerül az előző tokenjével
   (bigram-környezet), és később a generátor vissza tudja idézni —
   szótárfájl-frissítés nélkül (a felhasználó 7. ötlete).
6. Számok: számjegysorozat → `NUM` token + érték; a válaszokban a
   számokat a modell számként ismételheti meg, vagy szövegként (ONE…
   TWENTY, TEN+EGYSÉG, HUNDRED — 60 bájtos táblából).

**Elemzés (a generátor előtt)**: kérdés-e (WHAT/WHO/WHEN/WHERE/WHY/HOW/
DO/DOES/IS/ARE/CAN + „?"), segédige típusa (DO/DOES/DON'T), hangulat
(HAHA/HEHE/WOW/NOOO/:) :( :O), trágárság (rövid tiltottlista → a válasz
a felhasználó hangnemét tükrözi, játékosan, sértés nélkül), identitás- és
dátum-aktivátorok, „ember-lennél" aktivátor, téma-jelzőszavak (a
folyam-társítás a betöltött csomaghoz).

## 7. A generátor (a „gondolkodás" menete)

```
bejövő tokenek ─► aktivátorok? ─► rögzített/nyelvi modulok (identitás,
                    dátum, nyelv-kérdés) — tények, nem mintavétel
        │
        ▼ általános út
  1) jelöltek: a bemenet tokenjeihez bigram-lépések + fogalom-társítások
     → (token, súly) halmaz, 24 elemig
  2) ha Reasoning: második menet — a súlyokat szorzózza a bemenet és az
     aktuális téma átfedésével (a „töprengés" itt történik: a súlyok
     újrasúlyozása látható a gondolkodás-sávon)
  3) hőmérséklet: T1 a legjobb súlyú jelölt (mohó), T2..T4 egyre laposabb
     súlyeloszlás (a súlytáblát zsugorítjuk/növeljük) → más-más szavak
  4) mondatterv választás: SVO / visszakérdezés / hangulat-visszhang /
     tény-mondatazonosítás ("X IS Y" a korpuszból)
  5) tokenenkénti mintavétel: következő szó = a bigram-tábla súlyozott
     sorsolása a hőmérséklet szerint; leállás: 8–14 token, pont, „?"
  6) toldalék-visszaadás, szám-szöveg átírás, sortördelés (nincs
     elválasztás: a 32 karakterhez nem férő szó új sorba kerül — minden
     alap-angol szó belefér, a hosszabb tanult szavaknál a tördelő
     görget)
```

A véletlenszám: XOR-shift (32 bit), a FRAMES-számlálóból és a felhasználó
gépelési idejéből keverve — gépenként, alkalmonként más sorozat.

**Rögzített (nem mintavételes) válaszok** — csak a felhasználó által
kifejezetten kért tények: „ki készített?" → `MADE WITH GLM HELP BY SAFAR
SANDOR`; „ki az a SAFAR SANDOR?" → `A BUS DRIVER IN HUNGARY, AMATEUR
WRITER AND ASTRONOMER` + a kapcsolat: `SAFIZX81` + inverz-0 + `GMAIL.COM`;
„beszélsz más nyelven?" → `I SPEAK ENGLISH ONLY, BUT I KNOW SZIA`;
közmondás-kérés → `ONE SWALLOW DOES NOT MAKE A SUMMER` (a magyar közmondás
angol megfelelője, ahogy a felhasználó javasolta a spórolásos megoldást).

**Dátum és idő** (számítás, nem táblázat): a profil óta a FRAMES-számláló
másodperceket ad; a napok száma a profil napjától: év*365 + szökőnapok
(saját rutin, Z80 16 bites aritmetikával). Hét napja: `(abszolút_nap +
EPOCH_OFFSZET) mod 7` — a 2000-01-01 szombatra esett, ezt az
egy konstansot hordozza a kód, a többi számítás. „MIT TENNÉL, HA EMBER
LENNÉL EGY NAPRA?" → a kívánság-táblából (I WOULD + ige + tárgy + hely
+ időklauzula) mintavételes összeállítás, két-három mondatrész.

## 8. Memória-modellek és a kazetta mint háttértár

- **Tartós farok** (a REM-ben): a ROM SAVE kiteszi a szalagra, és a minden
  betöltéskor visszajön — ez a „legkisebb közös tartós memória" (profil-
  másolat, téma, beállítások, utolsó üzenet-index).
- **D_FILE sorok 0–2**: az élő munkamenet csomagolt állapota — a blokkcsere
  (LOAD) nem írja felül, mert a SHORT képek korábban végződnek.
- **Tanult-zóna + chat-gyűrű**: szintén a SHORT-képek fölött; a /save kiírja.
- Emlék-lejárat: a fenti 7-napos szabály.
- Régi adat felülírása: a /save az aktuális PICOBASE blokk pozíciójára ír
  (valódi szalagon: visszatekerés a blokk elejére, felvétel felül).

## 9. Szalagkezelés, turbo

- A lánc és a mentés a **ROM saját LOAD/SAVE rutinjait** használja a BASIC
  keretsorokon át — ez a maximálisan emulátor-/gépbiztos út.
- A **turbo tape** rutinok (`engine/tape_turbo.z80`) jelen vannak
  (bit-bang port 0xFF-en, CRC-8-cal), de **inaktívak**: a fejlesztés
  idejére egy fejlesztői kapcsoló tartja őket kikapcsolva, ahogy a
  felhasználó kérte (az emulátorok nem kezelik megbízhatóan). Éles
  gépen kapcsolt állapotban ~3–4×-os sebesség, blokk-CRC-cel.
- A fejlesztés alatt a szimulátor a ROM LOAD/SAVE szemantikáját modellezi
  (blokk alkalmazása a képre / kép kiírása blokkba), így a teljes lánc
  (boot → base → téma → mentés → visszatöltés) tesztelhető.

## 10. Eszközlánc

| eszköz | mit csinál |
|---|---|
| `tools/asm.py` | kétmenetes Z80 assembler (címkék, kifejezések, DZ/DZI ZX-szöveg-direktívák) + disassembler |
| `tools/zx81sim.py` | Z80-mag, 16 KB RAM, D_FILE-őr, FRAMES-óra, billentyű-injektálás, LOAD/SAVE-lánc, szövegképernyő-dump |
| `tools/build_t81.py` | motor-bináris + PK01-csomagok → EO81/.P/.T81 képek (appmake-konvenció szerint) |
| `tools/kbtrain.py` | szöveges korpusz → szótár + bigram + fogalom-táblák → PK01 csomag; kiírja a tömörítési arányt |
| `tools/archaeo.py` | régi T81/P fájlok boncolása (blokkok, D_FILE-jogosság, Z80-disassembler) |

## 11. A RAMTOP-védett tartós zóna (a felhasználó ötlete, v0.2-től éles)

### 11.1 A ROM-mechanika (a disassemblyből ellenőrizve)

A NEW parancs (`0x03C3`) nem „csak töröl": **SET-FAST, majd BC=RAMTOP−1,
ezután a RAM-CHECK rutin 0x02-vel TÖLTI a [0x4000, RAMTOP−1] tartományt,
visszaolvasással ÚJRA MÉRI a RAM tetejét, és `SET-TOP (LD (RAMTOP),HL)`
visszaírja** — majd a NEW belefolyik az INITIAL-be (`0x03E5`), amely a
RAMTOP-re 0x3E-jelzőbájtot tesz, a vermet (SP) közvetlenül alá állítja,
és friss, üres rendszert épít alatta.

A visszamérés menete: a fill után a rutin felfelé sétál; minden bájt,
ami pontosan 0x02 volt, nullázódik és a séta megy tovább; **az első,
nem 0x02/0x01 bájtnál megáll — az a cím lesz az új RAMTOP** (a határon
lévő bájt két DEI-et szenved, majd az INITIAL úgyis 0x3E-re írja).

### 11.2 A következmény: a védett zóna

```
RAMTOP (új) = 0x715F     ← a ROM 0x3E-jelzőjének „otthona" (áldozatbájt)
0x7160-0x71A8  ÁLLAPOT-ZÓNA 72 B (nyers bájtok — már nem kell a 6 bites
              D_FILE-csomagolás! a pack6/unpack6 a jövőbeli képernyő-
              scratch funkcióvá válhat)
0x71B0-0x742F  TANULT-ZÓNA 640 B
0x7430-0x7A5F  CHAT-GYŰRŰ ~1,6 KB
0x7A60         idle/reserve
0x7B00-0x7E18  D_FILE — a felhasználó javaslata szerint a RAMTOP FÖLÖTT:
              a NEW és a ROM-szerkesztő sose nyúl hozzá
0x7E19         VARS 0x80 jelző (a boot-telepítő írja)
```

**A NEW utáni világon**: az alatti [16509, RAMTOP) területet a ROM
frissíti (program, munkaterület), a fölötti mind érintetlen marad —
a felhasználó által kért „minden tartós dolog ide kerül" pontosan ez.

### 11.3 A boot-blokk (a felhasználó folyamata)

A kazetta elején egy kis BASIC-betöltő áll (`PICOBOOT`):

```
1 REM <ML-telepítő>
2 PRINT "PICO AI V0.1 — TINY MIND ON A TINY MACHINE"
3 PRINT ... rövid ismertető / használat (opcionális) ...
4 PRINT "PRESS ENTER TO SET UP THE UPPER MEMORY"
5 INPUT A$
6 RAND USR 16514        ← ML-telepítő:
                          - üres D_FILE a 0x7B00-ra (793 B, csak legális
                            cellák + 0x76 sorvégek),
                          - 0x80-as VARS-jelző a 0x7E19-re,
                          - a tartós zóna [0x7160, 0x7A60) nullázása,
                          - RAMTOP := 0x715F (0x4026-os rendszer-változó)
7 NEW                    ← a ROM átrendezi a világot a védelem alatt
```

A NEW után a képernyő kiürül (a ROM friss D_FILE-t épít a RAMTOP alá) —
ezért az ismertető ELŐRE szól: „after the screen clears, type LOAD ''".
A felhasználó `LOAD ""`-t üt → a `PICOBASE` blokk (SHORT kép,
`E_LINE=0x7100`, a Load a képfájl saját E_LINE-jéig olvas) betölt, majd
`RUN` — és a motor a védett D_FILE-ra, állapot-zónára talál.

Az állapot és a profil a REM-farokban (a 2-es sor 1-es REM-jének
végén, 72 B) is biztonsági másolatot kap: `/save` után a kazettán
visszatér, a tartós zóna pedig NEW-ra, témacserére és szerkesztésre
egyaránt védett.

### 11.4 Mi marad a RAMTOP ALATT, és miért

A szótár és a tudáscsomagok **a betöltendő képben** maradnak
([0x4009, 0x7100)): ezek kazettáról érkeznek és blokkonként cserélődnek
— a szalag úgyis ide szállítja őket; fölmásolásuk csak betöltő-logikát
költsözne. Az E_LINE-munkaterület (a ROM calculator-verme) szintén alul
marad ([0x7100, 0x715F) ≈ 95 B) — az interpreter e nélkül nem tudja a
`2 IF USR 16514 = 1 THEN LOAD ...` sort végrehajtani.

### 11.5 A /save hatálya (őszinte korlát)

A ROM SAVE `[VERSN, E_LINE)` = `[0x4009, 0x7100)`-ot ír: motor +
szótár + tudás + az 1-es sor REM-vege (az állapot-farokkal ✓).
A D_FILE-ban és a tartós zónában élő chat-gyűrű/tanult szavak így nem
kerülnek szalagra (v0.1); a profil és a beállítások a farokkal
visszatérnek. (v0.2: a farok bővítése, vagy E_LINE ideiglenes felhúzása
a SAVE előtt — az utóbbi újratöltésnél munkaterület-gondot okarna, ezért
most elkerüljük.)
