# ChatGPT 3 — PIOCO AI ZX81 breakpoint

## Workspace
`chatgpt/zx-81/chatgpt-3/`

## Hivatalos kiindulópont
Olvasd el a [BASELINE.md](BASELINE.md) dokumentumot minden további munka előtt.

A kiválasztott alapverzió:
- `PIOCO_AI_English_16K_CleanDisplay.t81` — 225 941 B
- SHA-256: `6d2025bd66435ed51540efeb7e098292926a0f8b2ce9a489103a2fe3d33faea5`
- Társított archívum: `PIOCO_AI_English_16K_CleanDisplay_artifact.zip` — 36 049 B
- Az archívum belső `PIOCO_AI_English_16K_ROM_INPUT.t81` fájlja byte-identical a kiválasztott CleanDisplay kazettával.

A két helyi fájl a jelenlegi ChatGPT-munkamenetben elérhető, de a binárisok még nincsenek feltöltve ebbe a GitHub-repóba. A fájlnevek és hash-ek részleteit a BASELINE.md tartalmazza.

## Korábbi, nem kiválasztott jelölt
A `PIOCO_AI_English_16K_IYBootstrap_Final2_artifact.zip` más buildet tartalmaz. Ne használd a CleanDisplay helyettesítésére, és a belső ROM_INPUT kazettát se keverd össze a kiválasztott alapváltozattal, kivéve, ha egy külön összehasonlítás ezt kifejezetten vizsgálja.

## Bizonyítottság
- A T81 és a CleanDisplay buildarchívum belső T81 állománya azonos méretű és SHA-256 értékű.
- A T81 és az archívum SHA-256 értékei ellenőrizve a helyi munkakörnyezetben.
- Ez még nem friss EightyOne/ZEsarUX emulátorteszt.
- A csomaghoz tartozó ZIP-ben nincs teljes forrásfa és automatizált teljes buildrecept; forrásból történő reprodukálhatóság még nincs igazolva.

## Következő vizsgálati sorrend
1. A T81 konténer és minden blokk teljes feltérképezése.
2. Betöltési sorrend, célcímek, hosszak, CRC-k és belépési pontok rögzítése.
3. D_FILE, VARS, E_LINE, CH_ADD, STKBOT, STKEND, RAMTOP és IY előtte/utána állapotának mérése.
4. A ROM INPUT profilbeviteli útvonal, karakterkezelés, backspace és billentyűismétlés vizsgálata.
5. D_FILE 24 sorának, sorvégeinek és a záró STOP bájtnak ellenőrzése.
6. CleanDisplay futtatása EightyOne V1.41-ben; utána külön ZEsarUX- vagy valós ZX81-ellenőrzés, amennyiben elérhető.
7. Csak a megfigyelt hiba okának azonosítása után készülhet javítás. Minden javítás külön build, külön T81 és regressziós jegyzőkönyv.
8. Az eredeti baseline változatlanul megőrzendő.

## Guardrails
- Soha ne módosítsd a `chatgpt-1` vagy `chatgpt-2` könyvtárat.
- Ne másolj vagy írj át GLM-, Grok- vagy más modellhez tartozó anyagokat.
- A `.P`, `.T81`, assembly és buildszkriptek mindig verzióazonosan legyenek megőrizve.
- Külön jelentsd a statikus ellenőrzést, a hosttesztet, az emulátortesztet és a valódi hardvertesztet.
