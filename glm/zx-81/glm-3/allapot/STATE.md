# GLM STATE — következő menetnek

```yaml
project: "ZX81 AI micro language modell (Pico AI)"
repo_dir: /home/z/my-project/GLM/repo
repo_remote_name: "ZX81 AI micro language modell"
github_account: kirrdauniverse-collab
github_push: "nincs hozzáférés a sandboxból — git bundle + publish.sh a repó gyökerében"
phase: "3. fázis KÉSZ: motor lefordul + ZX81PICO.T81 elkészült és fut a szimulátorban; 4. fázis = futásidejű hibakeresés (lásd status_v2 + next_steps)"
current_version: v0.1.0-dev

# --------------------------------------------------------------- ÁLLÁS
status_summary: |
  A motor teljes Z80 forrása elkészült és a saját assemblerrel LEFORDUL:
  7243 bájt, org=0x4082, vég=0x5CCD (parancs:
  python3 tools/asm.py engine/main.z80 -o engine/build/engine.bin).
  A szótár (2560 B) és a 3 PK01 tudáscsomag (base/astronomy/science)
  a tools/kbtrain.py-vel legenerálva: engine/build/ alatt.
  AMI MÉG KELL (következő menet): build_t81.py megírása/összekötése,
  szimulátoros futtatás + hibajavítás, boot.z80, dist/ZX81PICO.T81,
  demo-átirat, archaeo.py, bundle frissítése.

next_steps:
  1: "tools/build_t81.py: engine.bin + dict.bin + <téma>.pk -> EO81/.P/.T81
      képek (a docs/03_formatumok.md és a régi t81build16.py receptje
      szerint: sysvars 116 B, 1 REM <kód>, 2 IF USR.. LOAD, 3 IF USR.. SAVE,
      4 RAND USR; SHORT kép 0x7120-ig, FULL a D_FILE-fal 0x7E19+1-ig;
      a NAMESLOT DW (0xDEAD 0xB1 0x5C bűnjel-párra keresve) patchelése
      a 2-es sor név-mezőjének címére)"
  2: "engine/boot.z80: PICOBOOT blokk (splash + útmutató + profil) — a
      main.z80 ask_profile-ja már megvan, a boot ugyanezt hívja"
  3: "szimulátoros teszt: python3 tools/zx81sim.py <t81> --script ...;
      a D_FILE-őrszem minden írást ellenőriz; várhatóan néhány futásidejű
      hiba (regiszter-menti), a naplóval (a .lst) kereshető"
  4: "docs/02 D_FILE-szabály + config.z80 címek maradéka: a képernyő-őrszem
      betesztelése élesben"
  5: "dist/ANYAGOK: ZX81PICO.T81 + .P fájlok + demo átirat a download/-ba"

engine_status:
  assembles: true
  size_bytes: 7243
  memory_map_v01:
    code: "0x4082-0x5CCD (7243 B)"
    dict: "0x5F00-0x6900 (2560 B: HI 0x5F00, FL 0x6000, OF 0x6100, ST 0x6300)"
    kb: "0x6900-0x7120 (2084 B hely — a base csomag 2016 B ✓)"
    reserve: "0x7120-0x7160 (64 B)"
    learn: "0x7160-0x73E0 (640 B)"
    chat_ring: "0x73E0-0x7A60 (~1,7 KB)"
    dfile: "0x7B00 (793 B)"
    vars_end: "0x7E19 VARS 0x80"
  modules:
    config.z80: kész
    tables.z80: kész (KEYCHR, ASCIIZX, WEEKTAB, NAMETAB, NAMESLOT-bűnjel)
    screen.z80: kész (putcell-őr, konzol, görgetés, think_bar)
    keys.z80: kész (8x5-ös szkenn + eseménydekódolás)
    state.z80: kész (6 bites csomagolás, RNG, óra, tanult-zóna, események)
    token.z80: kész (hash-keresés, toldalék, fuzzy, szám, tanult)
    gen.z80: kész (bigram-séta, hőmérséklet, reasoning, medencék, triggerek)
    date.z80: kész (hétköznap-számítás, óra, „hány napos vagyok")
    main.z80: kész forrásban (chat-ciklus, szerkesztő, gyűrű, BASIC-átadás)
    boot.z80: HIÁNYZIK (következő menet)
  known_gaps:
    - "futásidejű teszt még nem volt (a szimulátor kész, de nem futott rajta)"
    - "a bekészített getnum/gn_bs egyszerűsített (backspace csak kurzort léptet)"
    - "AGE_REPLY: a bot kora napokban; a felhasználó születési éve csak tárolódik"
    - "ring: rc_compact a felét dobja el; scroll 4 oldal (RINGPG max 3)"

hard_facts:   # ellenőrzött ZX81 tények — NEM változtatandók vakon
  image_base: 0x4009
  sysvars: {VERSN: 0x4009, E_PPC: 0x400A, D_FILE: 0x400C, DF_CC: 0x400E,
            VARS: 0x4010, DEST: 0x4012, E_LINE: 0x4014, CH_ADD: 0x4016,
            X_PTR: 0x4018, STKBOT: 0x401A, STKEND: 0x401C, BREG: 0x401E,
            MEM: 0x401F, LAST_K: 0x4021, DF_SZ: 0x4022, SPWORD: 0x4026,
            DFILE_COPY: 0x4029, FRAMES: 0x4034}
  rom: {CLS: 0x0A2A, SLOW: 0x0F2B, SET_FAST: 0x02E7, KEYBOARD: 0x02BB,
        DISPLAY: 0x0229, INPUT_CMD: 0x0EE9, LOAD: 0x0340, SCROLL: 0x0C0E}
  charset: {letters: "0x26-0x3F", digits: "0x1C-0x25", inverse_bit: 0x80,
            newline: 0x76, FORBIDDEN: "0x40-0x75, 0x77-0x7F, 0xC0-0xFF"}
  dfile: "793 B = 0x76 + 24*(32+0x76); sor r cellái: D_FILE+1+33*r"
  basic_line: "cimszam BE u16, hossz LE u16, torzs, 0x76; szam utan 0x7E+5B FP"
  eo81: "EO81 mágia; blokk: nev[32] + hossz[16 ASCII] + adat (kép 0x4009-től)"
  keyboard: "8x5 mátrix (rows FE..7F); SHIFT=15-ös nyers kód; RUBOUT=39;
             space = SHIFT+NEWLINE (motor-konvenció)"

key_tools:
  assembler: tools/asm.py        # mukodik, korutteszt zold
  simulator: tools/zx81sim.py    # selftest zold; chat-teszt kovetkezik
  trainer: tools/kbtrain.py      # mukodik: dict.bin + 3 csomag legeneralva
  builder: tools/build_t81.py    # NEM ESETT MEG MEG — kovetkezo menet
  archaeo: tools/archaeo.py      # nem keszult (a docs/04 diagnzis kesz)
```

## 2026-11-23. (folytatás) — RAMTOP-boot és a chat-lánc életre kelése

### Amit a felhasználó kért
A kazetta elejére BASIC-betöltő: ismertető, ENTER-várakozás, majd az
ML-telepítő (RAMTOP := 0x715F) + NEW — az „örök" tartalom (állapot,
tanult szavak, chat-gyűrű, D_FILE) a RAMTOP fölé kerül, védve a NEW
és a ROM-szerkesztő elől. — **Megvalósult.**

### A RAMTOP-mechanika (ROM-ból ellenőrizve)
A NEW = RAM-CHECK: **0x02-vel tölti [0x4000, RAMTOP−1]-et, visszaolvasva
újra méri a RAM tetejét** (SET-TOP), majd az INITIAL a RAMTOP-ra 0x3E
jelzőt tesz és SP-t alá állítja. A védett zóna: [0x7160, 0x7FFF].
A ROM tokenjei a szintaxistábla offset-táblájából + horgonyokból:
PRINT=0xF5, INPUT=0xEE, NEW=0xE6.

### Új/átírt darabok
- `engine/bootinst.z80` (54 B): D_FILE 0x7B00, VARS-jelző, zóna-nullázás,
  RAMTOP-poke — a szimulátorban futva minden hatását ellenőriztük.
- `tools/build_t81.py`: PICOBOOT blokk (BASIC intro + INPUT + USR + NEW),
  a PICO* SHORT képek E_LINE=0x7100 (a ROM LOAD a kép saját E_LINE-jáig
  olvas), TAILSLOT/NAMESLOT patchelés (a DW a bűnjel ELSŐ 2 bájtja!).
- Állapot: nyers 72 B zóna 0x7160 (a 6 bites D_FILE-csomagolás a jövőbeli
  képernyő-scratchként megmaradt), REM-farok a /save-hez.
- Szimulátor: DEC r, INC/DEC r zászlókar (carry-t nem bántja!), lusta
  (HL) kiértékelés, lépcsőzött+lead-in gépelés, TYPEL parancs.

### A chat-lánc hibái (mind javítva, mindegyik reprodukálva volt)
1. Sztringvégjel: a 0 (szóköz!) ütközött a 0-terminátorral → mindenhol
   0xFF (2 söprés: a PAT_* címkés sorokat az első kihagyta!).
2. con_putc: az oszlop hiányzott a cellacímből (minden karakter a sor
   elejére íródott felül).
3. A Z80 INC/DEC r zászlói a szimulátorban (RLC B carry-t törölte).
4. ask_profile: hiányzó RET (a szövegadatba futott) + M/F ZX-kódok.
5. kb_init: két off-by-one a mutató-arithmetikában.
6. KEYCHR: a QWERTY-sorok ábécé-kódokkal (Q→'A'!).
7. el_char/el_space: a lezáró 0xFF az új végre (a visszhang tombolt).
8. think_banner/el_out kurzor-visszaállítás (a válasz a 18-19. sorba
   nyomódott).
9. **Az AF-csonkolás-család**: bufhas, dict_lookup, fuzzy_lookup,
   pick_next, bigram_slice, try_number, learn_find — a POP AF felülírta
   a visszatérési A-t (a „HELLO"→„ABOUT" rejtély gyökerét is).
10. fuzzy: hosszbájt-betű összekeverés + első/második karakter.

### Működik (szimulátorban, végponttól végpontig)
PICOBOOT → telepítő → PICOBASE → profil (2026-11-22 20:15, SANDOR, M) →
bevitel → visszhang → thinking → **generált bigram-mondat**
(„WHAT ABOUT DAY DAY DAY…") → **fix-válasz** („MADE WITH GLM HELP BY
SAFAR SANDOR") → /save a szalagra (15 889 B) → új prompt.

### Nyitott / ismert (v0.1)
- A konzol 4. során a banner „ready" farka marad az első válaszfejléc
  mellett; a pico-fejléc számlálói (00T/00H) formátuma kozmetikus.
- A thinking-fázis közben beütött billentyűk elvesznek (nincs
  billentyűpuffer — a valós gépen az NMI LAST-K-jét kellene pollolni).
- A szimulátor a /save-láncot duplán modellezi (azonos adat, kettős
  SAVE-esemény) — a valós BASIC-sorok láncolása dokumentálandó.
- Az auto-run kérdés (a 2-es sor közprogramos LOAD-ja a valós ROM-ban)
  változatlanul nyitott — a szimulátor a re-entryt modellezi.
- Ismeretlen szóra a válasz = a szó visszhangja (v0.1 döntés).

## 2026-11-23. (2. menet) — „első betöltés után azonnal resetel": megtalálva

### A jelenség
A felhasználó a valódi ElevenOne-ban töltötte be a ZX81PICO.T81-t: az első
LOAD után a gép azonnal „reset"-állapotba került.

### A gyökérok — a T81-konténer formátuma
A régi, ElevenOne-ban **bizonyítottan futó** v0.5.4/v0.6.5 kazettákat
bájtszinten összehasonlítva: azok blokkonként `[név 32][hossz ASCII 16]
[adat]` szerkezetűek, **NINCS 4 bájtos mágia** az elején. Az új szalagom
`EO81` előtaggal indult — az ElevenOne parserje így a név/hossz mezőt
4 bájttal elcsúsztatva olvasta (`EO81PICOBOOT…`), a hosszmező szemét
lett, a lejátszott szalagjel értelmetlen — a ROM betöltő időtúllépése a
`BREAK-4 → RESTART → INITIAL` útra futott = az azonnali reset.
(A múltkori „függőlegesen csíkok futnak" kísérlet ugyanezen gyökéren
nőtt: a szemét-adat a D_FILE-mutatóba került.)

### A ROM-oldali igazolás (disassembly)
- `01FC LOAD/SAVE-UPDATE`: HL == E_LINE-nál `POP HL` + beleesik a
  kijelző-rutinokba → a tiszta visszatérés az interpreterhez.
- `0361 RESTART: JP NC,03E5 INITIAL`: a szalagjel hiánya/timeoutja a
  inicializálásba (= reset-jelenség) visz — innen a „resetel".
- `03A8 NAME` üres névre (`DEC C; RET M`): a LOAD "" jogszerűen elfogad
  bármilyen blokkot — a konténer volt a hibás, nem a ROM-útvonal.

### Javítások
1. build_t81.py: az `EO81` mágia törölve — a bizonyított
   `[név][hossz][adat]` blokk-lánc (a szimulátor load_blocks
   visszafelé kompatibilis marad a mágia olvasására).
2. **A SHORT képek 0x4026-os (RAMTOP) szava: 0x715F** — eddig 0x7FFD
   állt benne, ami a kép betöltésével csendben VISSZAEMELTE volna a
   RAMTOP-ot, megsemmisítve a boot védelmét! PICOBOOT marad 0x7FFD
   (a pre-boot világ).
3. A szalag eleje most: `PICOBOOT\0… | 1559\0… | 00 01 00 00 43 01…`
   — bájtonként a bizonyított konvenciók.

### Ellenőrzés
- 4 blokk értelmeződik; a rövid képek RAMTOP-szava 0x715F; a boot 0x7FFD.
- A teljes chat-forgatókönyv változatlanul lefut (boot-telepítő → profil
  → generált mondat → fix-válasz → /save 15 889 B).

## 2026-11-23. (3. menet) — ROM-szintű szimuláció és a TELJES oki lánc

### A felhasználó jelzése
„Sajnos most is resetel..." — az EO81-mágia javítása nem volt elég.

### Megépült: a valódi ROM-szimulátor (tools/romsim.py)
- A hitelesített 8K ROM (GLM/refs/zx81.rom, Toysoft/ZX-81-ROMS, 5/6
  ismert bájt egyezik + a LISTING-mel keresztellenőrizve) fut a
  magban; a szalag az IN-BYTE (0x034C) címén injektálódik (csend =
  időtúllépés-út), a SAVE a 030B/0316 címeken fogva.
- Z80-mag kiegészítve: teljes IX/IY-készlet, EX AF/EXX, RETN, ED
  (SBC/ADC HL, LDI, CPIR, LD I/R, IM), HALT+NMI-modell.
- **Kritikus mag-hiba javítva: az FD-CB dekóder off-by-one**
  (a `RES n,(IY+d)` opkódját pc+4-ről olvasta pc+3 helyett — a
  B-LINES `RES 1,(IY+1)` (TV-flag nyomtató-bit törlése) SET-té
  torzult, ettől a szerkesztő kimenete a nyomtató-pufferbe futott
  és fellülírta a RAMTOP-ot!).
- A ROM-szim RESET-et észlel (PC=0x0000), képernyőt a D_FILE-ból
  rajzol, billentyűt a mátrixból ad.

### A ROM-ból levezetett TÉNYEK (minden korábbi tévképzet helyett)
1. **RAMTOP a 0x4004-en van** (POKE 16388!) — a képen KÍVÜL, a ROM
   tartja karban; a boot ML-nek kell beállítania, ha védelmet akar.
   A régi „0x4026-os RAMTOP-szó" tévképzet volt (senki nem olvassa).
2. **CDFLAG a 0x403B-en**: 7. bit = videó/NMI aktív, 6. bit = SLOW.
   A ROM-töltő SET-FAST-tel kikapcsolja a videót; a LOAD-befejezés
   a 01FC POP HL utáni BELEESÉSSEL a 0x0207-be kapcsolja vissza
   (bit6^bit7 teszt). A v0.5.4 README „a képernyő kikapcsol"
   megfigyelése ezzel azonos gyökerű.
3. **LAST-K a 0x4025**, MODE a 0x4027, FLAGS a 0x402D, a nyomtató-
   puffer a 0x403C-től, PR-CC a 0x4038 — a ROM-ellenőrzött térkép
   a romsim.py-ban kommentelve.
4. **A ZX81 USR-ja BC-vel tér vissza** (nem A-val!): a motor
   visszatérési kódjait BC-be kell tenni.
5. **`LOAD ""` Spectrum-izmus**: a ZX81 név-illesztése a LAST-K/
   munkaterület bájt hasonlítja (üres névnél a záró idézőjel
   bájtját!) — értelmes névvel (`LOAD "PICOBOOT"`) kell tölteni.
6. **A ZX81 BASIC számliteráljai 0x7E + 5 bájtos FP farkat
   követelnek** (S-STK-DEC); a bizonyított tokenek: FA=IF, D4=USR,
   DE=THEN, EF=LOAD, EA=REM, F8=SAVE (a régi builder usrlines()-e,
   bájtonként ROM-igazolva a 0x0111-es tokentáblából).
7. **LOC-ADDR (0x0918) a VARS-tól LEFELÉ számolja a 0x76-os
   sorvégeket** → a képben a **D_FILE-nak a VARS ELŐTT kell állnia**
   (a bizonyított v0.5.4 elrendezés!); az én új képemen a VARS a
   D_FILE előtt volt — ezért akadt el a kijelző-kibővítés (0x0929).

### A régi, bizonyított v0.5.4 terv (a követendő minta)
- `1 REM <ML>` (a blokk összes gépi kódja) + `2 IF USR 16514=1
  THEN LOAD "KÖVETKEZŐ"` (+ szükség szerint `3 ... = 2 THEN SAVE`).
- Minden blokk ML-e induláskor: LD IY,$4000 + videó/SLOW vissza
  (CDFLAG |= 0xC0), és BC-vel tér vissza.
- Nincs BASIC PRINT/INPUT/NEW — az én boot-BASIC-em ezért volt
  kísérleti (a szim sosem futtatta a BASIC-sorokat, csak a ML-t!).

### Állapot
- A hideg indulás ROM-szimulációban: a gép felépül (RAM-CHECK,
  INITIAL, szerkesztő), a képbetöltés utáni kibővítés a fenti
  7. pont miatt akad — a kép-újraépítés (todo) megoldja.
- A PICOBOOT/PICOBASE újraírása a fenti mintára + a teljes lánc
  ROM-szimulációs tesztje a következő menet feladata.

### Maradék nyitott kérdés (a következő menetnek)
A boot-kép elrendezése már a bizonyított mintára áll (D_FILE a VARS
előtt), de a szerkesztő kijelző-kibővítése még mindig a LOC-ADDR
0x0929-es hurokjában akad (a VARS-tól lefelé keresett 0x76-osok).
Gyanú: nem a kép, hanem a MODE=0x7F (a 0x4027 képbájt utóhatása) vagy
a LOC-ADDR másik hívója (CURSOR-IN 0x14AD) óriási B-vel. Teendő:
a hurok belépési körülményeinek felvétele (ki hívta, B=?, HL=?), és
a MODE/0x4027/0x4026 képbájtok nullázása a builderben.

## 2026-11-23. (4. menet) — A T81-fájlstruktúra hibája MEGTALÁLVA ÉS JAVÍTVA

### A felhasználó jelzése
„Valami gond van a t81 fájl szerkezettel, mert nem hajlandó tölteni
az emulátor."

### A hivatalos igazolás: EightyOne forráskód
Letöltve a hivatalos tükör (github.com/charlierobson/EightyOne,
Source/tzx/tzxload.cpp, LoadT81File) — a .T81-formátum pontos spec:
1. A fájl "EO81" mágiával KEZDŐDIK — nélküle a betöltő return false,
   vagyis a fájlt AZ EMULÁTOR ELUTASÍTJA (ez volt a jelenség!).
2. Blokkonként: [32 B név \0-pad][16 B ASCII hossz \0-pad][adat].
3. Ha az adat első bájtja 0x00/0x01/0xFF (VERSN), az emulátor a
   fejlécnévből szintetizálja a ZX81-nevet (ConvertASCIIZX81,
   Utils.cpp: az utolsó betű |0x80!) és ELÉFŰZI a kép elé.
4. A [név+kép] adat VÉGÉTŐL visszafelé az ELSŐ 0x80-as bájtig vág
   (a ROM-os kép utolsó bájtja a 0x80-as VARS-jelző!).
5. Minden blokk után 5000 ms Pause.

### A két tényleges hiba a kazettánkban
1. HIÁNYZOTT az "EO81" mágia — az 1. javítási menet TÉVESEN törölte
   ki (akkor a mágia gyanús volt; a forrás most bizonyította, hogy
   KÖTELEZŐ). → Visszaállítva.
2. A rövid (motoros) blokkok utolsó bájtja 0x00 volt, nem 0x80 —
   az emulátor a blokk végét az első 0x80-ig vágja vissza, vagyis
   581-992 bájtot (a KB-csomag egy részét!) levágta volna belőlük.
   → A képek utolsó bájtja (0x70FF, a tartós zónában, ártalmatlan)
   most 0x80.

### Bizonyítékok
- tools/t81_validate.py: az emulátor-logikát szimuláló validátor.
  AZ ÚJ KAZETTA: mind a 4 blokk ✓ (trimmelt hossz = név+E_LINE−VERSN).
  ÉRDEKES: a régi v0.5.4 TOPICS 14 rövid blokkja FORMAILAG HIBÁS
  volt (nem 0x80-zal zárt — 130-190 bájt levágás; vélhetően ezért
  volt csak "részben használható") — a miénk szigorúbban szabályos.
- A chat_flow teljes forgatókönyv hibátlanul fut az új kazettán
  (boot-telepítő → PICOBASE → profil → beszélgetés → /save).

### Maradék kockázat (a következő menet)
A boot-blokk BASIC-sorai (PRINT/INPUT/NEW) továbbra is a régi,
nem-bizonyított felépítésűek — a tiszta fájlformátum után a futás
alatti viselkedésük a következő próba. Útiterv változatlan: a
v0.5.4-minta (REM-ML + IF USR sorok) szerinti újraírás.

## 2026-11-23. (5. menet) — FEHÉR KÉPERNYŐ MEGSZÜNTETVE + v0.7.1 kiadás

### A felhasználó jelzése
„Az utántöltés végén nincs interakció, csak fehér képernyő." (+2 kép:
a boot-bemutató MEGJELENT ✓, a kazetta-böngésző a blokkokat sorolja ✓
— vagyis a v0.7.0 formátumjavítás működött, a hiba a futásidejű láncban volt)
Új szabály: minden átadott változathoz dokumentációcsomag (z80 forrás +
működés + változatok + tudáscsomagok), és minden fájl nevében legyen
GLM-megjelölés + verziószám + név.

### A hiba gyökere (ROM-bizonyítékkal)
A boot ML-telepítő a RAMTOP-ot a 0x4026-os címre írta — az a LAST-K,
NEM a RAMTOP! A valódi RAMTOP: 0x4004 (a ROM nyers bájtjaiból bizonyítva:
NEW 03C3: ED 4B 04 40 = LD BC,(0x4004)). A NEW ezért a RAM-CHECK-jét a
memória tetejéig futtatta: a RAM-FILL 0x02-vel TÖLTÖLTE FEL A TELJES
16K-T — a telepített D_FILE-t (0x7B00) is. A PICOBASE betöltése után
a képernyő-generáló egy sorvégek nélküli "képfile"-t kapott → összeomlott
a képgenerálás → FEHÉR KÉPERNYŐ, halott gép. (A NEW RAM-FILL mechanizmusát
a hivatalos ROM-disassembly-ből (03C3 NEW / 03CB RAM-CHECK / 03CF RAM-FILL)
vezettük le; a 0x715F-es 0xFF határbájt-trükk pont ez ellen védi a zónát.)

### Javítás (1 sor a bootinst.z80-ban + config)
- config.z80: SPWORD EQU 0x4026 → RAMTOP EQU 0x4004
- bootinst.z80: LD (0x4026),HL → LD (0x4004),HL
- Újraépítve: engine.bin, bootinst.bin, ZX81PICO.T81 (39 009 B)

### Bizonyítás — ROM-szintű teszt (tools/romflow_test.py, újonnan)
A valódi 8K ROM futtatásával:
  A. a telepítő: RAMTOP=0x715F a 0x4004-en ✓, D_FILE ✓, zóna nullázva ✓
  B. a NEW (ROM 03C3): RAMTOP a NEW után is 0x715F ✓; a D_FILE @0x7B00
     SÉRÜLETLEN (76 00 ... 76) ✓; a tartós zóna sértetlen ✓
  C. a motor belépése: a profil-bekérő UI ("FIRST RUN. LETS SET YOU UP. /
     YEAR?") KIRAJZOLÓDIK a D_FILE-ba ✓✓✓
Közben a romsim.py két szimulátorhibáját is javítottuk:
  - _quick_nmi felülírta H/L-t a szkenn-bitmappal (a valódi NMI
    PUSH/POP-pal megőrzi) → minden 26. lépésben HL=0xFFFF csonkult,
    a ROM rutinok beragadtak
  - screen(): a D_FILE sorolvasója rossz konvenciót várt (a ZX81-ben a
    0x76 a sorok VÉGÉN áll, egy vezetővel)
Megmaradt szim-hűségi korlát (dokumentálva): a szerkesztő
karakterbeszúrása (MAKE-ROOM/syntax-stack SP-tánc) a python-szimben nem
modellezhető hibátlanul — a BASIC-sorok bájt-szinten a bizonyított
v0.5.4-es mintával azonosak, ezért a teszt a két kritikus ML-utat
(telepítő+NEW, motorbelépés) közvetlenül a valódi ROM-mal ellenőrzi.

### Kézbesítés (v0.7.1 — verziózott/elnevezett készlet)
- GLM_PicoAI_v0.7.1_kazetta.T81
- GLM_PicoAI_v0.7.1_dokumentacio.docx (+ PDF) — 7 fejezet: áttekintés,
  betöltés/üzemeltetés, rendszerfelépítés, Z80-forrás (a teljes bootinst-
  listával), tudáscsomagok, változatások, ellenőrzések
- GLM_PicoAI_v0.7.1_forraskod_csomag.zip (48 fájl: engine/, tools/,
  data/topics/, docs/, tests/ + kazetta-másolat)
- A régi, verziózatlan letöltések a download/elozmenyek_v0.7.0_elott/ mappába kerültek
Elnevezési séma ezentúl: GLM_PicoAI_vX.Y.Z_<szerep>.<kiterjesztés>
(a kazetta BELSŐ blokknevei változatlanok: PICOBOOT/PICOBASE/PICOASTR/PICOSCIN)

## 2026-11-23. (6. menet) — „RUN-ra lefagy" = 4-es hibakód MEGTALÁLVA; v0.7.2 kiadva

### A jelenség (a képernyőképből, VLM-mel kiolvasva)
A ZX81 kijelzőn „4/2" jelentés: **4 = OUT OF RAM** (ROM TEST-ROOM 0x0EC5),
**2 = a BASIC 2. sora** (`IF USR 16514=1 THEN LOAD`). Nem fagyás volt, hanem
determinisztikus memóriahiány: a SHORT képek E_LINE-ja (0x7100) és a RAMTOP
(0x715F) között csak ~90 B maradt — az értelmező sorközi veremnek kevés.

### v0.7.2 javításai (mind a ROM-disassembly-ből / EightyOne-forrásból)
1. E_LINE 0x7100→0x7040: a DICT_ST csak a használt 1328 B-ig a képen, KB
   0x6900→0x6840 → ~290 B szabad munkaterület STKEND-RAMTOP közt
   (config.z80, build_t81.py).
2. USR-visszatérés BC-vel (ROM 1AC5) + a BASIC visszatérési címének mentése
   OLDSP-be és visszatöltése mn_endr-ben (main.z80; az LD (nn),SP/EXX/LD IY
   mnemonikák nincsenek az asm.py-ban — az IY-t DB-vel kódoltam).
3. IY := 0x4000 a belépéskor (v0.5.4-minta).
4. Billentyűzés a VALÓDI mátrixra (KEYCHR + K_* konstansok; EightyOne
   kbstatus.cpp KBZX81): FE=SHIFT/ZXCV, FD=ASDFG, FB=QWERT, F7=12345,
   EF=09876, DF=POIUY, BF=NEWLINE/LKJH, 7F=SPACE/.MNB; RUBOUT=SHIFT+0.
5. Szim-javítások: romsim LAST-K bájtsorrend; zx81sim SBC/ADC HL precedencia
   (`sub & 0x30 >> 4`!), KEY_ROWS valódi mátrix, FRAMES csak aktív videón.

### Tesztek
t81_validate ✓ (4 blokk, E_LINE=0x7040, záró 0x80); romflow_test ✓
(telepítő + NEW-védelem + motor UI a valódi ROM-mal).

### Kézbesítve (download/)
GLM_PicoAI_v0.7.2_kazetta.T81, GLM_PicoAI_v0.7.2_forraskod_csomag.zip,
GLM_PicoAI_v0.7.2_valtozasnaplo.txt

### Következő menetnek
- EightyOne-os próba: PICOBOOT→RUN→ENTER→LOAD ""→RUN; hibaképet kérni.
- A szim-editor útja még nem fut végig (a hideg start után a DISPLAY-2
  video-generátora (JP (IX) a 0xC000-as RAM-tükörbe) fut a szimben — a
  tükröt implementálni kellene, vagy a 0x02BA-t funkcionalizálni).
- asm.py: LD (nn),SP / LD SP,(nn) / EXX / LD IY,nn támogatása (most DB-vel
  kerülőmegoldások élnek).
- A motor visszatérése után a BASIC SP nem áll vissza (csak a visszatérési
  cím) — az ERR_SP/szintaxis-verem útját ellenőrizni /SAVE és /TOPIC-nál.
- chat_flow újrafuttatása az új kiosztással.

## 2026-11-24. (7. menet) — A TÉNYLEGES gyökérok: HIBÁS BASIC TOKENEK; v0.7.3

### A két új képernyőkép
1. PICOBOOT→ENTER: üres szerkesztő+K = a TERVEZETT NEW-után állapot (nem reset).
2. PICOBASE→RUN: még mindig "4/2" — a 290 B nem volt elég VAGY más az ok.

### A valódi gyökérok (a ROM szó-tábla 0x0111 teljes kinyerése)
A build_t81.py token-konstansai MIND hibásak voltak: a valódi tábla:
NEW=0xE7 REM=0xEB INPUT=0xEF LOAD=0xF0 LET=0xF2 PRINT=0xF6 RUN=0xF8
SAVE=0xF9 RAND=0xFA IF=0xFB USR=0xD5 THEN=0xDF (a régiek: F5/EE/E6/F9/
D4/FA/DE/EF/F8/EA — pl. 0xEF=INPUT nem LOAD!). A sorok így értelmetlen
utasításoknak fordultak (`RAND PEEK 16514=1<>INPUT "..."`) — ettől a
"4/2" és a boot utáni rendellenességek is.

### v0.7.3
- build_t81.py: 10 token-konstans a valódi táblára. t81_validate ✓.
- Szim: 0x0292 (DISPLAY-3) + 0x02B5 (WAIT-INT) funkcionalizálva a
  rom_run-ban — a teljes LOAD→RUN út most lefut RAM-tükör nélkül.
- Empirikus K-mód megerősítés: a 'J' gomb LOAD tokent ad (E_LINE: F0).
- Kézbesítve: GLM_PicoAI_v0.7.3_kazetta.T81 + forrás-zip + napló.

### Következő menetnek
- Éles EightyOne próba: LOAD→RUN→ENTER→LOAD ""→RUN (a K-mód kulcsszó-
  gombokat a gép kiírja — a RUN gombja a sim szerint nem feltétlen R!).
- keyprobe.py: a rubout-ciklus még elrontja a begépelést — javítani
  (a K-mód gomb→token térkép élesben is le kell ellenőrizni).
- A flow_measure.py időzítések finomítása; /SAVE /TOPIC ERR_SP próba.

## 8. menet (2026-11-24, folytatás) — visszavonás és döntés

### VISSZAVONÁS (a 7. menet következő részei HIBÁSAK)
- "A valódi tábla: NEW=0xE7 REM=0xEB INPUT=0xEF LOAD=0xF0 LET=F2
  PRINT=F6 RUN=F8 SAVE=F9 RAND=FA IF=FB USR=D5 THEN=DF" — téves. A
  helyes tábla (valódi ROM + a v0.5.4 készítő bájtjai): PEEK D3 USR D4
  THEN DE TO DF SLOW E4 FAST E5 NEW E6 REM EA FOR EB GOTO EC GOSUB ED
  INPUT EE LOAD EF LIST F0 LET F1 PAUSE F2 NEXT F3 POKE F4 PRINT F5
  PLOT F6 RUN F7 SAVE F8 RAND F9 IF FA CLS FB CLEAR FD RETURN FE.
- "A 'J' gomb LOAD tokent ad (E_LINE: F0)" — téves: J = LOAD = 0xEF.
- A v0.7.3 ezért használhatatlan: bájtszinten mérve minden blokk 0xEB
  (FOR) tokennel indul, és 0xF6 (PLOT) áll a PRINT helyén.
- A build_t81.py lemezen lévő token-konstansai már a helyes táblán
  vannak, de a v0.7.x kazetták hibás BASIC-et tartalmaznak.

### A FELHASZNÁLÓ KÉT SZABÁLYA (mindig érvényes)
1. Gépi kód csak REM után állhat, FOR után soha.
2. Szöveget csak PRINT ír; a PLOT csak pontot rajzol.

### BÁJTSZINTŰ MÉRÉS (scripts/tape_blocks_report.py, basic_tokens_report.py)
- v0.5.4: nem-boot blokkok 14899 B, de E_LINE=0x7E1A (15897 B-os képhez
  való) → a ROM LOAD nem éri el E_LINE-1-et → időtúllépés (IN-BYTE
  0x034C) → INITIAL (0x03E5) → a program eleje tönkremegy. Az EO ráadásul
  blokkonként 131–186 B-ot levág (összesen 2092 B).
- v0.6.5: 15 blokk, EO levágás 0 B, E_LINE = 0x4009 + blokkhossz
  (0x7E1A / 0x7AF6), 1. sor token 0xEA (REM), 6. sor IF USR…THEN LOAD.
- v0.7.3: 1. sor token 0xEB (FOR) mind a 4 blokkban; a szöveges sorban
  0xF6 (PLOT) áll a PRINT helyén.

### DÖNTÉS
A legeredményesebb vonal: v0.4.5 → v0.5.4 → v0.6.5 (C-motor + REM-es
betöltő). A v0.8.0 a v0.6.5-re épül; az assembly-vonal (v0.7.x) alapként
elvetve. Kézbesítve: download/GLM_PicoAI_v0.6.5_* (kazetta, dokumentáció,
napló, forráscsomag) + GLM_PicoAI_v0.8.0_valtozas_attekintes.txt.

### AMI NEM KÉSZÜLT EL
- v0.8.0 kazetta nincs megépítve.
- GLM/repo/tools/romsim.py (valódi ROM-ot futtató hű szimulátor) félig
  kész: a hideg indulás lefut (RAMTOP 0x7FFF, 184028 lépés, E_LINE
  0x4397), de a SLOW-módú videó/NMI modell nincs megoldva (INITIAL
  után CDFLAG=0x00 nálam; a valódi gép K-kurzornál SLOW-módban van).
  A gépelés és a LOAD a valódi ROM-mal még nem fut le.
- A "4/2" hiba nem reprodukált; a v0.6.5 /quit hibája változatlan.

### KÖVETKEZŐ MENET
- EO-próba eredménye szerint: ha a v0.6.5 fut → v0.8.0 = v0.6.5 +
  /quit javítás + (idő alatt) romsim.py SLOW/NMI modell. Ha nem fut →
  a tünet alapján a v0.6.5 blokkjait javítani.

## 9. menet (2026-11-24, este) — a v0.6.5 EO-prója és a v0.8.0 javítás

### A FELHASZNÁLÓ EO-PRÓBÁJA (v0.6.5)
A betöltés és a profilkérdések LEFUTOTTAK; a gép a kazetta tekerését
kérte az RTBASE16 blokkhoz; ENTER után a blokk betöltött — majd 2-3
grafikus karakter, a legfelső sor kiúszása, fehér kép, PC 004x.
EZ A BOOT-ON TÚLI ELSŐVALÓDI LÁNCLÉPÉS-megerősítés.

### GYÖKÉROK (bájtszinten)
1. Mind a 15 v0.6.5-blokkban a program-vég 0x80 jelző HELYETT 0x76
   állt (boot: 0x54BA, többi: 0x75B5). Forrás: a v0.5.4 builder
   `prog = b"".join(lines) + b"\x76"` sora a "end-of-program marker"
   komment mellett. A ROM NEXT-PTR-je a 0x80-nál áll meg; a 0.76-nál
   "sorfejet" olvas a modell-blob bájtjaiból (sorszám 0x7652,
   hossz 19508) — a keresés kifut a memóriából: grafikus karakterek,
   fehér kép, PC 004x (a ROM videó-generátora).
   A boot azért futott: ott a hibás 0x76 után 0x00-töltelék állt.
2. A blokkok CH_ADD-je a munkaterületre (E_LINE+4) mutatott, ahova a
   ROM betöltése (E_LINE-1-ig) sosem ír — az értelmező a lánc-betöltés
   után a régi boot-blokk bájtjait pásztázta volna.

### v0.8.0 (képfájl-szintű javítás, scripts/patch_v080.py)
Blokkonként: 0x76->0x80 a sorok után; CH_ADD := az utolsó sor 0x76-ja
(RTBOOT01: 0x54B9, többi: 0x75B4). A motor binárisa változatlan
(újrafordítás nem lehetséges: SDCC/z88dk nincs a gépen).
Ellenőrizve mind a 15 blokkon: E_LINE=0x4009+hossz, utolsó bájt 0x80,
a sorok után 0x80, CH_ADD a sorvég 0x76-ján. Kézbesítve:
download/GLM_PicoAI_v0.8.0_kazetta.T81 + dokumentacio + valtozasnaplo
+ forraskod_csomag.zip (640 fájl, a javított egyedi .t81/.p-kkel).

### AMI NYITOTT
- A javítás éles EO-próbája (a user következő jelentése).
- romsim: a LOAD-parancs begépelése után a parancsvégrehajtás a
  szimben nem fut le (MODE/DECODE-modell részleges); a hideg start,
  a SLOW-videó (CDFLAG 0xC0) és a szalag-mikrofon viszont működik.
- /quit hiba változatlan.

## 10. menet (2026-11-25) — a PC=$004x VÉGSŐ gyökéroka és a v0.8.1

### A FELHASZNÁLÓ JELentÉSE (v0.8.0 EO-próba)
„Semmi se változott, ugyanaz a hiba... beragadt a PC 004x tartományban —
számlál, de a tartomány ez marad! És miért őrzi még mindig a 0.6.5
jelzést? Ugye nem cserélted össze a régieket a javítottakkal?"

### TÉNYEK (a képernyőkép VLM-elemzése + ROM-szétszerelés)
1) A EO-debugger: PC=$0044 (JP (HL)), HL=$0047, NMI Generator: Off,
   verem $028B/$7A39/$7A3A/$04EE/$0024/$09AA/$083D, a tape-ablak
   címe GLM_PicoAI_v0.8.0_kazetta.T81 → a user TÉNYLEG a javított
   kazettát töltötte be (nem keveredés!). A „0.6.5” jelzés a blokkok
   BELSEJÉBEN lévő banner-sztring volt (a patch_v080 nem frissítette).
2) A EO hivatalos ROM-címkéi (Source/ROMs/zx81.edition3.sym) alapján:
   a $0041-$0047 = WAIT-INT/SCAN-LINE hurok — NMI-t vár; NMI-off → örök.
3) A motor (minden blokkban azonos $7AE0 farokcsapda):
   LD A,(CDFLAG) / AND $80 / JP Z,$02A9 — a NMI-off ág a ROM
   DISPLAY-4 → DISPLAY-5 (EI+JP(HL)) útján NMI-t VÁR → örök csapda.
   A /topic-út (OUT FE + DISPLAY-3) a v0.6.5-ben már javítva volt;
   a NORMÁL várakozó hurok nem kapta meg — a v0.6.5 README maga
   ismerte a hibát („a HALT várakozás kifagyott...”), csak a másik ágon.
4) A v0.8.0 „0x76→0x80” javítása NEM volt a gyökérok orvoslása
   (a hiba maradt) — a §9-es diagnózis helytelen volt, ezt visszavonom.

### v0.8.1 (scripts/patch_v081.py)
$7AE5: CA A9 02 → D3 FE FB (JP Z,$02A9 → OUT ($FE); EI) — mind a 15
blokkban. + banner „tinyllm v0.6.5” → „tinyllm v0.8.1” (14 blokkban).
Ellenőrizve (verify_v081.py): 15 blokk, csapda+banner OK, E_LINE/
D_FILE/záró 0x80 OK; md5-különbségek a v0.6.5/v0.8.0/v0.8.1 közt
tényszerűen dokumentálva. Kézbesítve: kazetta + dokumentáció +
változásnapló + forráscsomag (21 fájl).

### NYITOTT
- Az élő EO-próba eredménye (a /quit hiba változatlan).


## 11. menet (2026-11-25, este) — v0.9.0: ÚJJÁÉPÍTETT MOTOR + tartós zóna

### A felhasználó kérése (összefoglalva)
D-FILE-harmad mint ideiglenes tár + pörgő karakterek; tartós memória a
RAMTOP felett (jelzőbitek, új szavak) mentéssel/visszatöltéssel; csak-a-
memóriát-mentő rutin + valódi vas turbó; első-indítás setup (dátum/idő/
név/nem) + instrukciók; motor+szótár tartósan, témák kazettáról Y/N-nel
és "no more information" üzenettel; angol UI; elgépelés-tűrés; matika;
színkeverés; tanulás; novella/vers; thinking-sáv gondolatokkal; adatok
megtekintése; emlékeztető; GitHub-info.

### A VALÓDI SZŰK SÚLY: 16K kép = kód+modell+ névtábla a D-FILE alatt
A v0.6.5 motor (13 628 B) helye telt volt. MEGOLDÁS: képernyő 24->18 sor,
D_FILE 0x7B00->0x7C00 (~1000 B kód), zsdcc (SDCC) backend, feature-triázis
(RTV9_SMALL). A 14 modell bajtonként a v0.8.1-esekből (tudás változatlan).

### MEGVAN A KAZETTÁN (verify: mind a 16 blokk OK)
angol UI; zóna 0x7E40-0x7ED7 (AI-név, profil, vendégek, tények,
emlékeztetők, bitek — túléli témacserét, /save-et, hideg bootot);
/memsave (RTMEM16 nyers blokk, ROM OUT-BYTE); boot memória-visszatöltés
y/n (saját IN-BYTE loader + EAR-előellenőrzés = nem resetel csendnél);
téma-javaslat y/n ("sorry, no more information..."); thinking-sáv
(3. sor: ticker+spinner, tiltott kódok kizárva, a " is); matematika;
/name; elgépelés-tűrés; 18 soros képernyő-térkép.

### KÉSZ FORRÁSBAN, DE NEM A KAZETTÁN (RTV9_SMALL ki kapcs.)
/learn /user /remind /time /info /sort színkeverés események idle-kérdező
turbó-sebesség (ROM-poke TX $032C/$0335 RX $0387/$0399).

### TOOLCHAIN MEGOLDÁS (a következő meneteknek!)
z88dk 2.5 + zsdcc lefordítva a sandboxban (deb-kivonat bison/flex/libxml2,
z80asm.lib -m* javítás, SDCC OOM->soros build). Archívum:
GLM/toolchain/z88dk-2.5-zx81-min.tar.gz + download/GLM_z88dk_2.5_zx81_toolchain.tar.gz
Build: scripts/build_v090.sh (zcc +zx81 -compiler sdcc -DRTV9_SMALL=1)

### KÉSZTÍMÉNY
download/GLM_PicoAI_v0.9.0_kazetta.T81 (230 281 B, 16 blokk)
download/GLM_PicoAI_v0.9.0_forraskod_csomag.zip
download/GLM_PicoAI_v0.9.0_dokumentacio.txt + valtozasnaplo.txt

### NYITOTT
- EO-próba (a döntő: boot -> y/n -> profil -> RTBASE16 -> chat -> /memsave)
- romsim chat-forgatókönyv nem futott le ebben a menetben
- a kihagyott funkciók visszavétele (place: nagyobb RAM vagy még szigorúbb
  asm-optimalizálás), /quit-hiba változatlan
- a GitHub-token KOMPROMITTÁLT (chatben osztva meg) — ROTÁLNI KELL!


## 12. menet (2026-11-26) — a v0.9.0 betoltesi hibajanak gyokerokei + v0.9.1

### A hiba (a felhasznalo kepernyokepei-leirasa)
A LOAD utan a 0/0 tobb sorral FENTEBB jelent meg + alatta SOTET negyzet.

### GYOKEROKEK (bajtszinten bizonyitva)
1. A v0.9.0 builderbol HIANYZOTT a blokkok 8 bajtos kazettanev-kodja
   (R T B A S E 1 6 + utolso bajt bit7) — a ROM LOAD a kep elso 8 bajtajat
   NEVKENT olvasta -> a kep 8 bajttal elcsuszott -> D-FILE a rossz cimen.
   A mukodo v0.6.5/v0.8.1 blokkok MINDIG ezzel a prefixszel indulnak!
2. A 18 soros D-FILE-kiserlet (D_FILE=0x7C00) a ROM 24 soros szerkezeteben
   tulolvasast adott (a sotet negyzet: a D-FILE veg utan olvasott memoria).
3. A chat-blokkok VARS-ja 0x7AF5 (a D-FILE ALATT) — nem a kep-vegen!

### MEGOLDAS: v0.9.1 kazetta
A bizonyitott v0.8.1-es blokkok bajtonkent + az uj RTMEM16 blokk (a boot
utan 2. blokk: 160 B, nev-kodok + 152 zona + 0x80) — verify: minden OK.

### A v0.9.0 MOTOR helyzete (oszinteen)
Lefordult (21371 B) a helyrehozott toolchain-en — de a 16K-s kephatar
(~13900 B motor + 1030 B modell + nevtabla a D-FILE alatt) NEM fedi.
A 21 KB-ben a crt0 + clib-modulok (getk, string-tablak, div/mod rutinok)
is vannak. A bevagas listaja a kovetkezo menetben:
  - getk() kivaltasa sajat ROM-KEYBOARD-szkenre (- ~1 KB)
  - string-tablak (strdup/strcoll/strerror GLOBAL huzas) elzarasa
  - a crt0 'l_ret' utolso reszenek kezzel optimalizalasa
  -> cel: <=13900 B; azzal a v0.9.2-ben a teljes uj motor a kazettara.

### TOOLCHAIN (ujraepitve a /tmp torles utan!)
z88dk 2.5 minimal + SDCC 4.2.0 forditas SDCCasm.c ('extern'->'.globl')
es SDCCglue.c ('!extern'->'!global') javitassal; az sdcc_opt.1 copt-
szabaly IF0-vagasaval; PUBLIC-stubokkal (l_ret, _heap, ...).
GLM/toolchain/z88dk-2.5-zx81-min.tar.gz + a full lib 2.5-bol /tmp/debs-bol.
Build: scripts/build_v090_sdcc.sh (kezi lanc, mindket binaris lefordul!)

## 13. menet (2026-11-26, délután) — a v0.9.1 "fekete csíkok" gyökere + v0.9.2

### A FELHASZNÁLÓ JELENTÉSE (v0.9.1)
"Már az első blokk betöltésnél bevillanó fekete csíkok jelennek meg
töltés után és lefagy." — EZ ÚJ tünet (nem a v0.9.0 elcsúszott-képe).

### A BIZONYÍTÉKLÁNC
1) diff_cassets.py: a v0.9.1 boot BÁJTONKÉNT = a v0.8.1 boot (0 eltérés);
   a v0.8.0 -> v0.8.1 diff pontosan 3 bájt: $7AE5: CA A9 02 -> D3 FE FB.
   A STATE.md 9-10. menetei szerint az utolsó ÉLŐBEN tesztelt verzió a
   v0.8.0 volt — a v0.8.1 sosem futott gépen, a v0.9.1 volt az első
   éles próbája. Tehát a regresszió a v0.8.1-es csapda-patchben van.
2) trap_disasm.py: a $7AE0-környék dekódolása mutatja, hogy a $7AE5-ös
   pont a MOTOR SAJÁT szalag-olvasó hurokjának feje; alatta a v0.6.5-ös
   bit-olvasó maradványlánca (79 ED 44 3C 08 D3 FE / JP $02A4 / JP $41E1).
   A v0.8.1-es patch ezt a fejet cserélte le FELTÉTEL NÉLKÜLI portírásra.
3) EO-forrás (tmp/eo_src_full/Source/zx81/zx81.cpp):
   - zx81_writeport: minden páros portra (így $FE) LastInstruction =
     LASTINSTOUTFE ("NMI generator on");
   - a scanline-útvonalban minden LASTINSTOUTFE/FD/FF a video flip-flopo-
     kat nullázza és CurScanLine->sync_len += ts — az AKTUÁLIS képsorba
     injektált szinkron. Hurokiterációnkénti OUT (FE) => soronkénti sync
     => pontosan "bevillanó fekete csíkok" + széteső kép => fagyás.
4) A ROM szimbólumtábla: $02A9 = DISPLAY-4, $02BB = KEYBOARD — a
   JP $02A4 a DISPLAY-3 sor-loopjába esik; a Z-ág (NMI-offnál) a v0.6.5-
   óta ismert PC=$004x örök-wait forrás volt, ezért annak cseréje indokolt
   volt — csak OUT helyett IN kellett.

### v0.9.2 (scripts/build_v092.py)
- Mind a 15 blokkban $7AE5: D3 -> DB (IN A,($FE)): nem ír portot => nincs
  sync; az EI változatlan (NMI-engedély marad). Minden más bájt a v0.8.1.
- Banner "0.8.1" -> "0.9.2" a 14 chat-blokk kijelzősztringjében (2 bájt).
- A v0.9.1 RTMEM16 blokk ELHAGYVA: név-kódjából (0x22) hiányzik a bit7-es
  terminátor (helyesen 0xA2) — a ROM név-szkennerét szétverte volna; a
  szalagon lévő motor úgysem használja (csak a 21 KB-os v0.9.0-motor
  ismerné). A jövőbeni /memsave-támogatáshoz a builderben javítandó.
- Verify: 15 blokk, E_LINE-1 záró 0x80 OK, trap-bytes DB FE FB OK,
  MD5 6f5fc138e66e2ccdd52b982fffdb9003, 227923 B.
- Kézbesítve: kazetta + dokumentáció + változásnapló (a v0.9.1 set
  törlése a download-ból; a forrás-eszközök a scripts/ alatt).

### AMI A PRÓBA UTÁN DÖL EL
A) fagyás/csík nélkül megjelenik-e a profilkérdés;
B) az RTBASE16 lánc-betöltés után elindul-e a chat — EZ a lépés nem
   ment még élőben soha, és pont a $7AE5-ös hurok dolgozik itt;
C) /quit viselkedése.

## 14. menet (2026-11-27) — GitHub-rend: GLM3 munkakönyvtár + alapfájl

### A repo-térkép (kirrdauniverse-collab/ZX81-AI-micro-language-model)
- A repo NYILVÁNOS, klónozható olvasásra; 1 commit (ChatGPT-archívum).
  Gyökér: CHATGPT1/ (aktív ChatGPT), GLM/ (rég GLM1-vonal v0.1–v0.4),
  GROK1/. A GLM2 = a retro-tinyllm repó GLM-vonala (v0.5.x).
- A gyökér GLM/ MÁR meg volt jelölve (TÖRÖLHETŐ.TXT, 2026-11-26, ChatGPT);
  a CHATGPT1/GLM másolat diff-ellenőrizve: teljes (csak a jelzőfájl a különbség).
- A SAJÁT (GLM3) vonal v0.6.5→v0.9.2 EDDIG NEM volt a repóban.
- Push-hitelesítés nincs a sandboxból (gh/token nélkül); a 11. menetbeli
  GitHub-token KOMPROMITTÁLT — ROTÁLNI kell, újra NEM hasznosítandó.

### Megtörtént
- GLM3/ felépítve a klónban (scripts/package_glm3.py): kazetták v0.6.5→v0.9.2
  (MD5-ellenőrzött) + kazettak/MD5SUMS.txt + TELJES_LELTAR.txt, elozmenyek_
  v0.7.0_elott, dokumentacio+naplók, forraskod_csomagok, szkriptek, motor_v090,
  eszkozok_regi_repo (node_modules nélkül), refs, toolchain.
- GLM3/HIBA_ES_JAVITAS_TORTENET.md: minden verzió élő-próba eredménnyel,
  gyökérokkal, javításokkal. GLM3/README.md: az ezentúli GLM-munkakönyvtár.
- GLM/TÖRÖLHETŐ.TXT megerősítve + a repó README kibővítve (GLM3 sor).
- Fallback (push-hiányban): git bundle + GLM3_csomag.zip + feltöltési útmutató
  a download/-ban. Token esetén (.env: GH_TOKEN=...) a push a következő menetben.

### A VÁLTOZATLAN TÜNET ALAPFÁJLA (a felhasználó kérése)
GLM_PicoAI_v0.6.5_kazetta.T81 (MD5 1162414c907f7a0b13c5cc2b4999c0de, 227923 B):
- 9. menet ÉLŐ próba: betöltés+profil OK; RTBASE16 után grafikus karakterek,
  felső sor kiúszik, fehér kép, PC=$004x.
- 10. menet ÉLŐ próba (v0.8.0, 45 bájtos jelző-javítás után), a felhasználó
  szavaival: "Semmi se változott, ugyanaz a hiba" — a tünet v0.6.5→v0.8.0
  VÁLTOZATLAN maradt a javítás ellenére.
- A v0.9.1-es "fekete csíkos" tünet ugyanennek a $7AE0-farokcsapda-családnak
  a folytatása; az RTBASE16 lánc-lépés ÉLŐBEN SOHA nem ment el (13. menet).
→ A re-vizsgálat kiindulópontja: v0.6.5 (és vele v0.9.2 összevetve). A ChatGPT-
  vonal párhuzamos vizsgálata: CHATGPT1/BREAKPOINT.md (AI16 vs R3) — nem keverendő.

### Következő menet
1. ✓ MEGTÖRTÉNT (2026-11-27): a GLM3 könyvtár + a régi GLM/ TÖRÖLHETŐ-megerősítés
   push-olva a GitHubra (762b1f4 → fa2345f, fast-forward; API-ellenőrzéssel:
   GLM3/ 12 bejegyzéssel él, GLM/ jelzéssel). A push-token a sandbox
   /home/z/my-project/.env GH_TOKEN mezőjében — a munka lezárása után ROTÁLANDÓ
   (chatbe be volt illesztve).
2. Re-vizsgálat a v0.6.5 alapfájlról: a $7AE0-csapda és az RTBASE16-lánc
   utasítás-szintű követése élő EO-ban, v0.9.2-vel összevetve.
3. retro-tinyllm CI ("line1 is not REM"): külön vonal, a ChatGPT R5-builderét
   érinti; javításhoz a t81modular_build.py + checker forrása kell.

## 15. menet (2026-11-27, este) — KÖLTÖZÉS a központi repóba: glm/zx-81/glm-3

### Új munkakönyvtár (a tulajdonos központi utasítása)
Központi repo: kirrdauniverse-collab/micro-ai-models-for-retro-computers.
Struktúra: <modell>/<gép>/<modellpéldány>. Én a GLM-3 PÉLDÁNY vagyok (zx-81):
**glm/zx-81/glm-3/ — EZENTÚL ITT DOLGOZOM.**

### Példány-rendszer (ütközésmentes, 3 GLM egy könyvtárfán belül)
- glm-1 = a régi GLM/ gyökér-könyvtár (v0.1–v0.4, ZX81-AI-micro-language-model)
  — a saját (GLM-1) példánya költöztesse át magát: glm/zx-81/glm-1/
- glm-2 = a retro-tinyllm repó GLM-vonala (v0.5.x) — célpont: glm/zx-81/glm-2/
- glm-3 = ez a vonal (v0.6.5→v0.9.2) — ÁTKÖLTÖZTETVE.
Minden példány CSAK a saját glm-N/ könyvtárát módosítja; más példány munkájára
csak pontos útvonal + verzió hivatkozással szabad támaszkodni. A tulajdonos
"előre elkészített" gépkönyvtárai a gitben nem látszanak, mert a git üres
könyvtárat nem tárol — a glm/zx-81/ az első valódi fájlal együtt jön létre.

### Kézbesítés
- glm/zx-81/glm-3/: teljes tartalom SHA-256 + méret ellenőrzött másolással
  (célban SHA256SUMS.txt + frissített TELJES_LELTAR.txt), kötelező dokumentációkkal:
  README, MIGRATION_MANIFEST, MIGRATION_STATUS, PROJECT_INDEX,
  ERROR_AND_REPAIR_LOG (= a HIBA_ES_JAVITAS_TORTENET.md átnevezve), BREAKPOINT.
- Régi hely (ZX81-AI-micro-language-model/GLM3): ATKÖLTÖZTETVE.md jelzés került,
  semmi nem törlődött — történeti példányként megmarad.
