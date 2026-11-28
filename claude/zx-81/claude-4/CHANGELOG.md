# Változásnapló

## v1.1.4 – 2026-11-24

- Javítás: a kazetta-kép D-file-jában egy elcsúszott `$80` bájt a kép jobb alsó sarkában
  fekete négyzetet okozott. A betöltő most a D-file minden nem-sorvég cellát üresen hagy,
  csak a sorvégek (`$76`) és a VARS-végjel (`$80` a `$7E19`-en) maradnak.

## v1.1.3 – 2026-11-24

- **Javítás (valódi gépen, nem az emulátorban látszik):** a kazetta-képbe a `MARGIN`
  ($4028) nullán maradt, pedig a ROM a kép felső üres sorainak számát (PAL: 31) itt tárolja;
  a `DF_SZ` ($4022) is üres volt. Emiatt a kép felfelé/lefelé gördült és fekete csík jelent meg.
  Most a builder beállítja: `DF_SZ = 2`, `MARGIN = 31`. A `$4029` (NXTLIN) korábbi, hibás
  D-file-írása megszűnt.
- A v1.1.2 SLOW/FAST és SHIFT-F viselkedése változatlan.

## v1.1.2 – 2026-11-24

- **Alapértelmezés: a kijelző mindig be van kapcsolva a válasz alatt.** A v1.1.0–1.1.1
  FAST módja a számítás alatt kikapcsolta a kijelzőt, ezért a képernyő fehér maradt,
  és a karakterek nem látszottak. Most a válasz élőben, karakterenként jelenik meg
  (kb. 3 s/karakter, mint a v1.0.0-ban).
- **SHIFT-F: opcionális FAST mód** (kapcsoló). A fejléc 2. sora mutatja: `GYORS:BE`
  (gyors, kijelző ki a számítás alatt) vagy `GYORS:KI` (alapértelmezés). A munkamenet
  indulásakor mindig KI; nem mentődik.
- **Törlés:** a `SHIFT-0` mellé a `SHIFT-8` is törli az utolsó karaktert. A `SHIFT-0`
  a szimulált billentyűzeten működik (ellenőrizve); ha a laptop Backspace-e az EightyOne-ban
  nem `SHIFT-0`-t ad, a `SHIFT-8` a tartalék.
- Kiegészítő cím: `FASTF` ($61CC), a fejlécben a 2. sor már nem üres.

## v1.1.1 – 2026-11-24

- Válasz előtt kiírja: `GONDOLKODOM (KEP SOTET)`. A FAST módban futó számítás alatt a
  kijelző ki van kapcsolva (fehér/sötét kép), ezt eddig nem jelezte a program, ezért
  lefagyásnak látszott. A válasz kb. 0,4 s/karakter, rövid válasznál is pár másodperc.
- Ismert, még nem reprodukált hiba: EightyOne-ban az utántöltés (`LOAD "WEATHER"`)
  után a gép a kérdés-kör közben fehéredett; ennek okát még vizsgáljuk.

## v1.1.0 – 2026-11-23

Javítások és új funkciók a v1.0.0 után (a tesztelő megfigyelései alapján):

- **Sebesség:** az előrefelé menet FAST módban fut (a kijelző nem veszi el a processzort).
  Emulátoros mérés: ~1,3 M T-állapot/menet ≈ 0,4 s/karakter, korábban ~3 s/karakter.
- **Fejléc (0–2. sor):** dátum (`DD.MM`), a hét napja, idő (`HH:MM`), név; hőmérsékleti szint,
  nem, gondolkodás állapota, a munkamenet összes tokenje (`TOK`).
- **Inverz csevegő-fejlécek:** minden kör előtt egy fordított sor: időbélyeg, bemenő
  tokenek (`BE`), generált tokenek (`KI`), válaszidő (`V`, becslés).
- **Óra:** az indításkor `IDO (OO PP)` kérdés (óra és perc), az óra FRAMES alapján percenként
  halad; a FAST-menetek becsült idejét is hozzáadja.
- **Csevegőterület:** 21 sor (3–23. sor); a görgetés ennek megfelelően korlátozott.
- **Alapértelmezések:** gondolkodás (greedy) BE, hőmérsékleti szint 1.
- **Sortörés a bemenet után:** a motor a felhasználói sor után sortörést (index 0) ad a
  modell kontextusába, így a bemenet a tanítási formátumot követi (`kérdés⏎válasz⏎`).
- **Memóriaátrendezés:** a négyzettábla ($6A00) és az exp-tábla ($6E00) a naplón túlra
  került, így a kód ($4082–$5213) elfér a modell ($5500) előtt.
- **Verziózás:** a kiadási fájlnevek viselik a verziót (`*_v1.1.0.*`); a `VERSION` fájl
  a forrás szerinti verzió.
- **Dokumentáció:** `README.md`, `docs/ARCHITEKTURA.md`, `docs/BILLENTYUK.md`,
  `docs/TUDASTAR.md`, `docs/FEJLESZTES.md`.

Ismert, nyitott kérdések: lásd `README.md` („Ismert korlátok”). A válaszminőség a modell
méretéből és az angol tanítóadatokból adódik; a számlálóirány (FRAMES csökken) valódi
gépen még ellenőrzendő.

## v1.0.0 – első kiadás

- RTCHAT (keret + motor + alapmodell), témablokkok (WEATHER, ANIMALS, JOKES, NUMBERS).
- EO81 `.t81` kazettakép öt blokkal; BASIC `LOAD`-os témaváltás; `SAVE "RTCHAT"` mentés.
- Fájdalom-emlékezet, név és nem tárolása a védett területen.
- A turbo betöltő a kerethez van építve, kikapcsolva.
