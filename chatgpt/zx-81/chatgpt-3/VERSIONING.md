# PICO AI — ZX81 kiadási és verzióelnevezési szabályzat

## Hivatalos modellnév

**PICO AI**

A korábbi forrásokban szereplő `PIOCO` vagy `tinyllm` elnevezések történelmi/build-eredetű szövegek. A mostani ChatGPT-3 fejlesztési ágban az új kiadások hivatalos termékneve PICO AI. A korábbi fájlokat és naplókat visszamenőleg nem nevezzük át, és a régi binárisok belső karakterláncait nem állítjuk át forrás nélküli, kockázatos bájtpatcheléssel.

## Kötelező fájlnév-formátum

Alapforma:

```
PICO_AI_ZX81_16K_vMAJOR.MINOR.PATCH.<extension>
```

Példák:
- `PICO_AI_ZX81_16K_v0.1.0.t81` — kiadható kazettakép
- `PICO_AI_ZX81_16K_v0.1.0.P` — azonos verziójú egyprogramos betöltő/futtatható kép, ha van
- `PICO_AI_ZX81_16K_v0.1.0_build.zip` — hozzá tartozó források, buildfájlok és tesztjegyzőkönyv
- `PICO_AI_ZX81_16K_v0.1.1.t81` — hibajavító kiadás
- `PICO_AI_ZX81_16K_v0.2.0.t81` — új funkciókat tartalmazó kiadás
- `PICO_AI_ZX81_16K_v1.0.0.t81` — első stabil, lezárt főverzió

Kísérleti buildnél a verzió után külön jelölés használható, például `_DEV`, `_TEST` vagy `_RC1`. A végleges kiadás fájlnevében ne legyen `final_final2`, `latest`, `fixed` vagy dátum nélküli `new` jelölés.

## Verziószám jelentése

- **MAJOR:** inkompatibilis memóriakép-, betöltési- vagy adat/állapotformátum-váltás.
- **MINOR:** új, a meglévő kezeléssel kompatibilis funkció vagy jelentős képesség.
- **PATCH:** hibajavítás, stabilitási, képernyő-, billentyűzet- vagy betöltési javítás, a külső formátum változtatása nélkül.

A verziószámot kiadáskor egyszer kell kijelölni, és minden kapcsolódó fájlnak ugyanazt kell használnia.

## A betöltő képernyőjén kötelező megjelenítés

A következő ténylegesen újraépített kiadástól a boot/betöltő képernyő egyértelműen jelenítse meg:

```
PICO AI ZX81
16K VERSION 0.1.0
```

A verziószámot a buildfolyamat egyetlen közös verziókonstansából kell előállítani; ne legyen külön kézzel átírt verzió a fájlnévben, a bootban és a chat fejlécében. A kijelzett név és verzió a chat nyitóképernyőjén is szerepeljen, ha a képernyőterv ezt lehetővé teszi. A szöveget ZX81-karakterkészletre kell konvertálni, és ellenőrizni kell a 32 oszlopos határt.

## Jelenlegi baseline címkéje

A kiválasztott CleanDisplay állományt változatlan bájtokkal, új helyi kiadási néven is megőriztem:

- `PICO_AI_ZX81_16K_v0.1.0.t81` — SHA-256 `6d2025bd66435ed51540efeb7e098292926a0f8b2ce9a489103a2fe3d33faea5`
- `PICO_AI_ZX81_16K_v0.1.0_build.zip` — SHA-256 `69433d00ac07a9c116fc9ddb8878666f5025d29dded0b5d023f65fb9c2a58234`

A `v0.1.0` itt a ChatGPT-3 PICO AI fejlesztési ág saját baseline-címkéje. **Nem állítja**, hogy ez az eredeti TinyLLM belső modellverziója, vagy hogy a verzió a jelenlegi T81 képernyőjén is megjelenik.

A jelenlegi, kiválasztott binárisban a buildarchívum vizsgálatakor ezek a régi belső szövegek voltak azonosíthatók:
- boot/profile szöveg: `PIOCO AI PROFILE OK`
- chatmotor szöveg: `tinyllm v0.5.4`

Ezek a baseline történelmi tartalmához tartoznak. A következő verzió tényleges újraépítésekor a forrásban kell átvezetni a PICO AI nevet és a verziószámot, majd az új kazettát lefordítani és ellenőrizni. A jelenlegi fájl neve megváltozott, a belső kódja nem.

## Kiadási kapu

Minden új kiadás előtt:
1. A fájlnév, bootképernyő, chat fejléc és build-manifeszt verziója egyezzen.
2. A T81, a buildarchívum és a forrásverzió ugyanahhoz a release-hez tartozzon.
3. Készüljön SHA-256 jegyzék és blokkonkénti kazettaellenőrzés.
4. A baseline-hoz képest gépikód-diff készüljön; a változatlan boot/chatbinárist nem szabad javítottként megjelölni.
5. Legyen külön jelölve a statikus teszt, hostteszt, emulátorteszt és valódi hardverteszt.
6. A korábbi kiadások maradjanak meg; új build soha ne írja felül az előző verziót.
