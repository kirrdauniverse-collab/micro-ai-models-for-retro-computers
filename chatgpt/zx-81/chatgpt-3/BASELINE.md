# PIOCO AI ZX81 — kiválasztott kiinduló változat

**Státusz:** ChatGPT-3 munkaterület hivatalos összehasonlítási alapja  
**Kiválasztva:** 2026-11-28  
**Eredeti fájl dátuma:** 2026-11-25 17:49 UTC (a korábbi fájltár metaadata szerint)

## Kanonikus kazetta

- Fájlnév: `PIOCO_AI_English_16K_CleanDisplay.t81`
- Méret: **225 941 bájt**
- SHA-256: `6d2025bd66435ed51540efeb7e098292926a0f8b2ce9a489103a2fe3d33faea5`

Ez a pontosan ellenőrzött fájl lett kiválasztva. A 2026-11-27-én újra feltöltött `PIOCO_AI_English_16K_CleanDisplay(1).t81` bájtról bájtra azonos vele, ugyanaz a méret és SHA-256.

## Hozzá tartozó buildarchívum

- Fájlnév: `PIOCO_AI_English_16K_CleanDisplay_artifact.zip`
- Méret: **36 049 bájt**
- SHA-256: `69433d00ac07a9c116fc9ddb8878666f5025d29dded0b5d023f65fb9c2a58234`

Az archívum belső kazettája:
`ports/zx81/pio16_release/PIOCO_AI_English_16K_ROM_INPUT.t81`

- Belső fájlméret: 225 941 bájt
- SHA-256: `6d2025bd66435ed51540efeb7e098292926a0f8b2ce9a489103a2fe3d33faea5`
- **Bájtról bájtra egyezik** a kiválasztott CleanDisplay kazettával. Az archívum belső fájlneve eltér, de a tartalma nem.

Az archívum további fájljai:
- `build/zx81/rboot16.P` — 6 822 B; SHA-256 `e493e6549a979856abb4b90b73ed0f2a16157501b738b034518a85e4157d99dc`
- `build/zx81/rboot16.bin` — 5 891 B; SHA-256 `0b55a00f6d352ce289f6ea5ca7e0b4cccb0d244fff469796ddc3b678670d81a3`
- `build/zx81/rtchat16.P` — 14 518 B; SHA-256 `40b3ee7b9ecbdc24dae9b400b6bcadba43c9c1d5e70519865549be7a88f00e29`
- `build/zx81/rtchat16.bin` — 13 587 B; SHA-256 `f3c55a7027fa16b1c65103cb59746eebe7041a9b59d1a582c4421abfbe440530`

**Fontos:** az archívum tartalmazza a kazettát és a fenti buildfájlokat, de a ZIP-ben nincs teljes forrásfa vagy teljes buildrecept. A hash-egyezés a kiválasztott T81 és az archívum belső T81 azonosságát bizonyítja; önmagában nem bizonyít teljes, forrásból reprodukálható buildet.

## Mit jelent a baseline-kijelölés?

1. Ezt a T81 fájlt nem írjuk felül és nem patcheljük helyben.
2. Minden további módosítás külön verziót kap, a forrásokkal és az előállítási folyamattal együtt.
3. Minden új kiadást össze kell vetni ezzel az alapverzióval: fájlhash, kazettablokkok, blokkcélcímek, hosszok, ellenőrzőösszegek és gépi kód.
4. A CleanDisplay és a korábbi IYBootstrap/ROM_INPUT különböző méretű buildjeit nem szabad összekeverni. Csak az itt rögzített, hash-sel azonosított belső kazetta tartozik ehhez az alaphoz.
5. A kiválasztás **nem** jelenti azt, hogy a kiadás most emulátorban vagy valódi ZX81-en újra hitelesítve lett.

## Első vizsgálati feladatok

- A kazetta tényleges blokkjainak és a T81 konténer struktúrájának feltárása.
- A betöltési címek, a D_FILE, VARS, E_LINE, CH_ADD, STKBOT, STKEND, RAMTOP és IY értékeinek rögzítése.
- A ROM INPUT és a profilbeviteli útvonal vizsgálata.
- A képernyő 24 soros szerkezetének és minden 0x76 sor-/záróbájtjának ellenőrzése.
- A CleanDisplay gépi kódjának összevetése a buildarchívum gépikódjaival és a hozzáférhető forrásokkal.
- A következő javításokat kizárólag új, ellenőrizhető kiadásként elkészíteni.
