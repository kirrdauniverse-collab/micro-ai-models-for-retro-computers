# 04 — Régészet: a korábbi archívum elemzése és az újrahasznosítás

A felhasználó Google Drive archívuma (4,3 MB ZIP, 795 fájl) a projekt korábbi
meneteinek anyagát tartalmazza. Ez a dokumentum rögzíti, **mi volt benne,
mit diagnosztizáltam, és mit vettünk át** — a `tools/archaeo.py` eszközzel
bármelyik régi `.T81`/`.P` újra elemezhető.

## 1. A lelet-lista

| útvonal | méret | értékelés |
|---|---|---|
| `GLM-retro-tinyllm-v0.5.4/` | ~9 MB | teljes korábbi projekt (C89 motor, int8 modellek, z88dk build, host-tesztek 11/11 zöldek) — **a formátumismeret forrása** |
| `GLM-retro-tinyllm-v0.6.5-16k/` | 15 fájl | a 16K-s újjáépítés: multiload T81 (225 KB, 15 blokk), 13 téma + magyar téma; a lánc-logika szimulációban bizonyított |
| `RETRO-TINYAI…csikok_futnak.t81` | 15,9 KB | **hibás build** — l. 2. fejezet |
| `Claude/Claude_ZXAI.t81` | 106 KB | másik ágens próbálkozása (EO81, 1 blokk) — nem futtatható lánc, de a képernyő-UI ötletei átgondolásra érdemesek |
| `Mistral/mistral_zx81ai16 (1).t81` | 15,4 KB | EO81, 1 blokk, 16K — hasonló próbálkozás |
| `zx81_tinyllm_16k_csomag/` | 5 fájl | korai magyar multiload (2627 B motor + 4×1536 B téma) — a témacsomag-csere gondolata innen jött |
| `zx81_tinyllm_16k_pack/` | 7 fájl | a C-os kiadás .bin modelljeivel |
| `Claude/Névtelen*.jpg` | 2 db | képernyőfotók ( dokumentáció ) |

## 2. A „futó függőleges fekete csíkok" hibája — diagnózis

A fájl `RTCHAT-BOOT` blokkjában a rendszer-változók mező **2 bájttal el
van csúsztatva**: a betöltő így `D_FILE = 0x0001`-et olvas ki, vagyis a
megjelenítő a **ROM-ból** olvassa a „képernyőt". A ROM bájtjai nagy
valószínűséggel tiltott D_FILE-kódok → a megjelenítő-generátor sor-kiszink
hiba → **a borderen átfutó fekete sávok** (a felhasználó által leírt jelenség).

Ez ugyanaz a hiba, amit a korábbi projekt v0.4.1-ben elkövetett és a
dokumentumában leírt („a kitalált 2 bájtos FF 00 prefix elcsúsztatta a
képet, a betöltő D_FILE=$0001-et olvasott → függőleges csíkok / gördülő
képernyő fagyás"). A tanulság most is érvényes:

- a kép **pontosan 0x4009-től** indul (VERSN bájt az első);
- a builder ezt strukturálisan ellenőrzi (a build_t81.py a konvenció
  minden invariánsát assertálja a kép kiírása előtt);
- a motor oldala a `putcell` őrző író, a szimulátor a D_FILE-őr.

**Megjegyzés**: a D_FILE-ba közvetlenül írt tiltott bájt (0x40–0x75,
0x77–0x7F, 0xC0–0xFF) ugyanezt a hibaképet adja — a Pico motorban ez a
kód szerkezete miatt sem fordulhat elő (6 bites csomagolás + maszkolt
kiíró rutinok).

## 3. Mit vettünk át, miből lett új terv

**Átvettem (bizonyított tények):**
- EO81 konténerformátum és a P-kép konvenciója (0x4009 bázis, sor-formátum,
  $7E+FP számok, D_FILE=0x400C, sor-címzés `D_FILE+1+33*r`);
- a BASIC-keret mintája: `IF USR 16514 = 1 THEN LOAD "NÉV"` lánc és a
  `= 2` → `SAVE` kézrátétel (a v0.6.5 szimulációban bizonyított);
- a név-átírásos téma-váltás (a LOAD-név mező átírása a sorban);
- a D_FILE-munkaterület-ötlet (a SCRATCH.md 6 bites cellacsomagolása);
- a FRAMES-alapú óra és a SLOW-mód kötelezettsége (FAST alatt a kijelző
  és a FRAMES is áll);
- a „törlés = 8-as kód" tapasztalat (a RUBOUT valódi dekódja).

**Ami új (a felhasználó mostani kérése szerint):**
- tiszta Z80 motor saját assemblerrel — nem C89/z88dk (a régi motor
  34 KB volt; a Pico ~4,2 KB); a 16K-s kiadás arányai így a kérésnek
  megfelelően alakulnak;
- valódi tokenizáló-elemző-generátor lánc hőmérséklettel és
  gondolkodási újrangsorolással (a régi motor karakter-szintű MLP volt);
- bitmezős emlékek lejárattal, tanult szavak, profilt és születési adatot
  tartalmazó állapot;
- EO81-kazetta **egyetlen fájlban**, boot → base → témák sorral.

**Amit szándékosan nem vettem át:** a z88dk 1.8 build-megkerülések (nem
kell — nincs külső toolchain), a karakter-szintű modellformátum (az új
generátor más), és az 48K-s motor-elrendezés.
