# MILO v0.1 — HANDOFF / átadási jegyzőkönyv

## 1. Azonosítás

- Modell: MILO — Micro Intelligent Language Organism
- Verzió: v0.1
- Célgép: Sinclair ZX81, 16K RAM
- Modellgazda/fejlesztői ág: ChatGPT-1
- Git branch: `milo/zx81-v0.1`
- Jelenlegi ágfej: `27bf808d4b36de1e8cc1211c6cdcabba3681dc44`
- Repo: `kirrdauniverse-collab/micro-ai-models-for-retro-computers`

## 2. Mi a MILO v0.1?

A MILO v0.1 elsősorban név- és átadási kontrollpont. A történelmi PICO/AI16/R3/R4/R5 állományokat nem írjuk át és nem töröljük.

A v0.1 célja:
1. rögzíteni a MILO nevet és verziózási szabályt;
2. megőrizni az AI16 működő kontrollvonalát;
3. a következő fejlesztő számára egyértelműen dokumentálni, mi bizonyított és mi nincs;
4. a korábbi R3 regresszió vizsgálatát nem elveszíteni.

## 3. FONTOS ÁLLAPOT — ne kezeld kész, újraépíthető release-ként

A jelenlegi `MILO_v0.1_ZX81.p` mérete 15428 byte, míg a korábban ismert AI16 kontroll P-kép 15385 byte volt.

A jelenlegi `MILO_v0.1_ZX81.t81` mérete 15437 byte.

Ezért a repository jelenlegi MILO v0.1 binárisait **nem szabad automatikusan azonosnak tekinteni a korábbi AI16 kontrollal**. A korábbi jegyzet ezt kontrollként jelölte, de az eltérő P-méret miatt ezt most auditálni kell.

Következtetés:
- nincs még új MILO v0.1 hardveres/emulátoros elfogadási bizonyíték;
- a bináris/source reprodukálhatóság nincs lezárva;
- a következő modell első dolga az audit, nem egy új nagy architektúra.

## 4. A jelenlegi fájlok

- `MILO_v0.1_README.md`
- `MILO_v0.1_ZX81.asm`
- `MILO_v0.1_ZX81_BUILD.py`
- `MILO_v0.1_ZX81.p`
- `MILO_v0.1_ZX81.t81`

A fájlnevekben a modellnév és verzió kötelező.

## 5. A build script jelenlegi problémája

A `MILO_v0.1_ZX81_BUILD.py` tartalma még régi AI16/PICO útvonalakat és régi kimeneti neveket használ, például:
- `ports/zx81/ai16/zx81ai.asm`
- `ports/zx81/mistral_zx81ai16.t81`

Ez **nem tekinthető MILO v0.1 reprodukálható build rendszernek**.

Ezt a következő munkamenetben javítani kell, de csak a bináris eredet pontos azonosítása után. Nem szabad vakon átírni a build folyamatot, mert a korábbi projektben már volt olyan eset, amikor a forrás és a tényleges működő bináris eltért.

## 6. Ismert történelmi kontrollok

Korábban rögzített, ismert AI16:
- P: 15385 byte, SHA-256 `4bcbbcf756c6472862550ebef87b05c5029e9dab`
- T81: 15437 byte, SHA-256 `efe29d5348782139a891a71f42c2b853847e75c4`

R3:
- P: 15385 byte, SHA-256 `df926773d7d78dcf0a370c6b95028edbc581c253`
- T81: 15437 byte, SHA-256 `4277a74636e9bffeb2593e7491f27c43aaabe6af`

R4:
- P SHA-256: `011dbc9f0ef29701b190340f19ce97842a10d69b`
- T81 SHA-256: `b6169bb37b9697a80b65b3d8ae5652bb96b10516`

## 7. A legfontosabb korábbi eredmény

Az AI16 -> R3 összehasonlítás alapján a javítások nem egyszerűen 'elvesztek':
- AI16 és R3 P-kép között 7328 byte különbség volt;
- R3 és R4 között 4433 byte különbség volt.

Tehát a módosítások bekerültek a binárisokba.

Az első nagy R3 szemantikai változás commitja:
`4026f695f1ab24c1d5958d6afec3d60e4a64d751`

Leírás:
`PICO R3: deterministic startup setup, visible thinking and safe D-file scratch`

Szülője:
`8699d893082774261caeefb85f1ec5b1018b2063`

Ez a commit több dolgot egyszerre változtatott:
- D-file transient scratch;
- thinking tick sorrend;
- boot/setup folyamat;
- help gate;
- setup strings;
- egy régi boot funkció eltávolítása.

Ezért a következő fejlesztésnek **AI16 -> R3 commitonkénti regresszióvizsgálatot** kell végeznie.

## 8. Kötelező következő munkamenet

1. Ellenőrizd a jelenlegi MILO v0.1 fájlok valódi blobjait.
2. Ellenőrizd a P/T81 méretet és hash-t.
3. Derítsd ki, miért 15428 byte a MILO P-kép.
4. Azonosítsd, pontosan melyik történelmi AI16 binárisból származik.
5. Ellenőrizd a T81 payloadot is.
6. Ne kezdd újra az R5 architektúrát.
7. Ne módosíts egyszerre több alrendszert.
8. Az AI16 működő kontrollból indulj.
9. A R3 előtti szülőcommit legyen az első reprodukciós pont.
10. Ezután a R3 commitokat egyenként alkalmazd.
11. Az első hibás commitnál állj meg.
12. Csak az első bizonyított regresszió után javíts.

## 9. ZX81 biztonsági szabályok

- A D-FILE címe mindig a rendszer `$400C` pointeréből jöjjön.
- `$76` ZX81 NEWLINE/HALT, nem általános adatbyte.
- D-FILE-be csak érvényes ZX81 display kódokat írj.
- A 16K RAM tartomány: `$4000-$7FFF`.
- USR belépési cím és BASIC tokenizálás minden buildnél külön ellenőrzendő.
- Egyetlen kombinált T81 legyen a tesztkazetta, ha több egymás utáni betöltési blokk szükséges.
- Build siker =/= emulátoros/hardveres működés.

## 10. MILO név- és verziószabály

Új fájlok:
`MILO_v0.1_...`

Új fejléc:
`MILO v0.1`
és lehetőség szerint:
`ZX81 16K / BUILD XXXX`

A történelmi PICO/AI16/R3/R4/R5 neveket csak történelmi hivatkozásként használd.

## 11. Átadás állapota

**MILO v0.1: ELŐKÉSZÍTETT, DE NEM RELEASE-ELFOGADOTT.**

A következő fejlesztő feladata nem az, hogy 'továbbépítse, mert kész', hanem hogy először lezárja a bináris eredet és reprodukálhatóság auditját, majd folytassa a regresszióvadászatot.

Utolsó fontos elv:
**ne higgy a fájlnévnek — a byte-oknak higgy.**
