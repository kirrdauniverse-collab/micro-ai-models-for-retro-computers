# ChatGPT 3 — PICO AI ZX81 breakpoint

## Workspace
`chatgpt/zx-81/chatgpt-3/`

## Hivatalos kiindulópont
Olvasd el a [BASELINE.md](BASELINE.md) és [VERSIONING.md](VERSIONING.md) dokumentumokat minden további munka előtt.

A kiválasztott alapverzió:
- Hivatalos helyi kiadási név: `PICO_AI_ZX81_16K_v0.1.0.t81` — 225 941 B
- SHA-256: `6d2025bd66435ed51540efeb7e098292926a0f8b2ce9a489103a2fe3d33faea5`
- Társított archívum: `PICO_AI_ZX81_16K_v0.1.0_build.zip` — 36 049 B
- Az archívum belső T81 állománya byte-identical a kiválasztott CleanDisplay kazettával.

A helyi verziózott fájlnevek nem jelentik azt, hogy a bináris belsejét átírtam. A jelenlegi buildarchívumban a régi `PIOCO AI PROFILE OK` és `tinyllm v0.5.4` szövegek is megtalálhatók. A következő új build bootképernyőjén már `PICO AI ZX81` és a vele egyező kiadási verzió jelenjen meg.

## Korábbi, nem kiválasztott jelölt
A `PIOCO_AI_English_16K_IYBootstrap_Final2_artifact.zip` más buildet tartalmaz. Ne használd a CleanDisplay helyettesítésére.

## Bizonyítottság
- A T81 és a CleanDisplay buildarchívum belső T81 állománya azonos méretű és SHA-256 értékű.
- A verziózott helyi másolatok hash-e egyezik az eredeti állományokéval.
- Ez még nem friss EightyOne/ZEsarUX emulátorteszt.
- A csomaghoz tartozó ZIP-ben nincs teljes forrásfa és automatizált teljes buildrecept; forrásból történő reprodukálhatóság még nincs igazolva.

## Következő vizsgálati sorrend
1. A T81 konténer és minden blokk teljes feltérképezése.
2. Betöltési sorrend, célcímek, hosszak, CRC-k és belépési pontok rögzítése.
3. D_FILE, VARS, E_LINE, CH_ADD, STKBOT, STKEND, RAMTOP és IY előtte/utána állapotának mérése.
4. A ROM INPUT profilbeviteli útvonal, karakterkezelés, backspace és billentyűismétlés vizsgálata.
5. D_FILE 24 sorának, sorvégeinek és a záró STOP bájtnak ellenőrzése.
6. CleanDisplay futtatása EightyOne V1.41-ben; utána külön ZEsarUX- vagy valós ZX81-ellenőrzés, amennyiben elérhető.
7. Források és assembler/buildrecept beszerzése vagy visszaállítása. A boot név/verzió szövegét ezután a forrásban kell módosítani, majd teljesen újrafordítani.
8. Csak a megfigyelt hiba okának azonosítása után készülhet javítás. Minden javítás külön build, külön T81 és regressziós jegyzőkönyv.
9. Az eredeti baseline változatlanul megőrzendő.

## Guardrails
- Soha ne módosítsd a `chatgpt-1` vagy `chatgpt-2` könyvtárat.
- Ne másolj vagy írj át GLM-, Grok- vagy más modellhez tartozó anyagokat.
- A `.P`, `.T81`, assembly és buildszkriptek mindig verzióazonosan legyenek megőrizve.
- Külön jelentsd a statikus ellenőrzést, a hosttesztet, az emulátortesztet és a valódi hardvertesztet.
