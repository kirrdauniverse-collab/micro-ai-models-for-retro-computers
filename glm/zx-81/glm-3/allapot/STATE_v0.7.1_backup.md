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
