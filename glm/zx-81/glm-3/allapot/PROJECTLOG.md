# GLM munkakönyvtár — projektnapló

Ez a könyvtár a "GLM" (a fejlesztő ágens) saját munkaterülete. Minden itt van:
projektnapló, állapotfájl, eszközök, és a repó teljes tartalma.

---

## 2026-11-22 — menet: "ZX81 AI micro language modell" (Pico AI v0.1)

A feladat: a felhasználó sokadik újraindítása a miniatűr AI-modell projekten.
Ezúttal minden verziókövetve, egy helyen, hogy újraindítás után is folytatható legyen.

### Mit csináltam ebben a menetben (1–3. fázis)

1. **Archívum-feldolgozás** (Google Drive, 4,3 MB ZIP, 795 fájl):
   - `GLM/tmp/dl/extracted/reszben_Hasznalhatoak/` — a korábbi próbálkozások:
     - **GLM-retro-tinyllm-v0.5.4** — a korábbi "saját" projektem (C89 motor,
       int8 modellek, z88dk build, 48K-s változat + 16K-s újjáépítés v0.5.4/0.6.5).
       A T81/P formátumismeret innen jött (EO81 konténer, 0x4009 képbázis,
       appmake-kompatibilis betöltősorok, $7E+FP farok, D_FILE=0x400C stb.).
     - **Claude_ZXAI.t81** (105 KB), **Mistral** (15 KB), **zx81_tinyllm_16k_csomag**
       (magyar témacsomagok), **RETRO-TINYAI...csikok_futnak.t81**.
   - A "függőlegesen futó fekete csíkok" hibás fájl diagnózisa: a kép 2 bájttal
     elcsúszva került a konténerbe → a betöltő D_FILE=$0001-et olvas ki → a
     megjelenítő a ROM-ból olvas "képernyőt" → érvénytelen kódok → futó fekete
     sávok a borderen. (Ugyanaz a régi, dokumentált hiba, mint a v0.4.1-es prefix-bug.)
   - Újrahasznosítva: T81 formátum + builder-logika (t81build16.py alapján),
     HAL-beli ZX81 tények (hal_zx81.c), boot-folyamat (boot16.c), 6 bites
     D-file scratch-tárolás (SCRATCH.md), EO81 blokklánc-terv.

2. **Műszaki specifikációk webes ellenőrzése**:
   - karakterkészlet: 0x00–0x3F normál, 0x80–0xBF inverz (bit 7!), 0x76 újsor;
     a 0x40–0x7F (0x76 kivételével) és 0xC0–0xFF **tilos** a D_FILE-ban →
     ezek okozzák a fekete csíkokat. (Wikipedia ZX81 character set.)
   - ROM disassembly (Logan–O'Hara, k1.spdns.de tükör): CLS=$0A2A,
     SLOW=$0F2B (CDFLAG bit 6), SET-FAST=$02E7, KEYBOARD=$02BB (port FE,
     8×5 mátrix, eredmény HL-ben + LAST-K), INPUT parancs=$0EE9 (csak BASIC
     környezetből hívható — lásd döntés a tervezésben), LOAD=$0340,
     SCROLL=$0C0E, LOAD/SAVE UPDATE=$01FC.
   - ZX81 P fájl = memóriakép 0x4009-től (VERSN) a VARS 0x80 jelzőig.

3. **Döntések** (részletesen: repo/docs/02_tervezes.md):
   - Tiszta Z80 assembly, saját assembler + szimulátor (nincs z88dk-függőség).
   - EO81/.T81 multiload lánc: PICOBOOT (FULL) → PICOBASE (SHORT) + témacsomagok
     (SHORT) — a D-file felső sorai és a megtanult zóna túléli a cserét.
   - /save: a motor 2-t ad vissza → a 3-as BASIC sor ROM SAVE-t hajt végre.
   - Bevitel: saját szerkesztő, ROM KEYBOARD-szkennek megfelelő port-olvasás.
   - Angol nyelvű működés (a felhasználó döntése: kevesebb memória/token).

### Következő menet (4. fázis) terve
- Valódi emulátoros teszt (EightyOne), ROM-rutin címek éles ellenőrzése.
- Nagyobb korpuszok, több témacsomag, minőség-optimalizálás.
- Turbo tape bekapcsolása emulátor-támogatás után.

Fájlok:
- `repo/` — a git repó (ZX81 AI micro language modell) teljes tartalma
- `STATE.md` — géppel olvasható állapot a következő menethez
- `tmp/` — nyersanyagok (letöltött archívum, referenciák) — nem része a repónak

### Menteés előtti állás (a menet végén)
- **A motor Z80 forrása ELKÉSZÜLT és LEFORDUL**: 7243 bájt
  (`python3 tools/asm.py engine/main.z80`). Modulonként: config, tables,
  screen (D_FILE-őr + konzol + görgetés), keys (8×5 szkenn), state
  (6 bites csomagolás, RNG, óra, tanult-zóna), token (hash + toldalék +
  fuzzy + szám), gen (bigram-séta, hőmérséklet, reasoning, medencék,
  triggerek), date (hétköznap-számítás), main (chat-ciklus, szerkesztő,
  gyűrű, BASIC-átadás).
- A szótár (256 szó) és a 3 PK01 csomag legenerálva (kbtrain.py).
- **Nem készült el**: build_t81.py (a .T81 összeállítása), boot.z80,
  a szimulátoros futtatás és hibajavítás — a következő menet 1. lépése
  (pontos teendők: GLM/STATE.md).
- A szótár/KB címei a motor méretéhez igazítva: DICT 0x5F00, KB 0x6900.

### Zárás (menet vége)
- **dist/ZX81PICO.T81 elkészült** (EO81, 3 blokk, 41 177 B) és a
  szimulátorban fut: betöltés + 30 000 utasítás hiba nélkül, a
  D_FILE-őrszem SEMMILYEN tiltott képernyő-írást nem talált.
- Következő menet első lépése: a képernyő-kiírások futásidejű
  hibakeresése (ask_profile kérdései), majd a chat-forgatókönyvek.
  Pontos lista: GLM/STATE.md (status_v2, next_steps).
