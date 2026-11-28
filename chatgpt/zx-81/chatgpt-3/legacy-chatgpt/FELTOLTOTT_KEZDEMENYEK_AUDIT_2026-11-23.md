# PIOCO / ZX81 AI — a feltöltött kezdemények műszaki áttekintése

**Vizsgálat dátuma:** 2026-11-23  
**Forrás:** rzx81_ai_eszben_Hasznalhatoak.zip  
**Módszer:** ZIP-leltár, forrás- és dokumentáció-olvasás, EO81/T81 blokkparszolás, memóriamutatók és D_FILE ellenőrzése, GLM build reprodukció, célzott C tesztek és hostos próba. Az eredeti feltöltött állományokat nem módosítottam.

## 1. Vezetői összefoglaló

**Elsődleges műszaki alapnak a GLM retro-tinyllm v0.5.4-et javaslom.** A teljes C89 motorforrás, a ZX81 16 KB-os port, a tréning- és csomagolóeszközök, a modellállományok és a T81-generátor is megvan. A többblokkos kazettát a saját generátorával újraépítettem, és az eredmény bájtról bájtra megegyezett a mellékelt kiadással.

**A GLM v0.6.5-öt későbbi bináris jelöltként tartsuk meg.** A használati leírás szerint több hibát javított, és a memóriaképe szerkezetileg életszerű. A feltöltött mappában azonban nincsenek meg a módosított források és a csomagolóeszközök, ezért önállóan nem reprodukálható.

**A Mistral egyblokkos változata szerkezetileg érdekes, de a RAMTOP mező kritikus ellenőrzést igényel.** A Claude és a RETRO-TINYAI csomagoknál a `FF 00` előtag a megadott EO81-betöltési konvenció mellett eltolhatja a rendszerváltozókat; a csíkos képernyőkép ezt a hibaképet támasztja alá.

A PIOCO szó-/szótag-/utótag-tokenes trigramötleteit nem dobnám el. A GLM jó futtató- és memóriakezelési alapot adhat, a PIOCO viszont másik nyelvfeldolgozási irány. A két motort nem keverném össze, amíg külön mérés nem igazolja az integráció előnyét.

## 2. GLM retro-tinyllm v0.5.4 — a legjobban visszaépíthető alap

### Tartalom és felépítés

- Teljes, hordozható C89 motorforrás (`engine/`).
- ZX81 16 KB-os portforrás (`ports/zx81/`) és külön 16K build.
- PC-s host szimulátor, modelltréner, kvantáló/csomagoló és kazettagenerátor.
- 16K-s `class G` alaptudásmodell és 13 szakosított modell.
- Többblokkos, név szerinti betöltést használó EO81/T81 kazetta.
- Profil- és eseménymemória, dátum-/időmodul, témairányítás és ROM-os mentési út.

A 16K kiadás 48 karakteres, egyszerűsített kisbetűs karakterkészletet használ, ékezetek nélkül. A modell kontextusa 8 karakter, embeddingje 8 dimenziós, rejtett rétege 4 egység. A `base_g.bin` 1030 bájtos; a mellékelt `modelinfo.py` **884 paramétert** számol. Ez kis méretű, de tényleges súlyokkal dolgozó karakterenkénti következőkarakter-generálás, nem pusztán mondatválasztó.

### Kazettaellenőrzés és reprodukálhatóság

A `GLM_v054_RT16_TOPICS.t81`:

- 225 199 bájt;
- 15 EO81 blokk: egy boot, egy alapmodell és 13 témapakk;
- a konténer pontosan a fájl végén zárul;
- az indító blokk 15 889 bájt, a többi 14 blokk 14 899 bájtos rövid kép;
- `D_FILE=$7B00`, `VARS=$7E19`, `RAMTOP=$7FFD` a teljes boot-képben.

A rövid témablokkok a `$7B00` képernyőzóna előtt érnek véget, így a témacsere nem írja felül a kijelzőt.

**Reprodukciós ellenőrzés:** a mellékelt `tools/t81build16.py` generátorral újraépítettem a kazettát a csomagban levő `rtchat16.bin`, `rboot16.bin` és `models16_v05/` alapján. Az új és az eredeti fájl SHA-256 értéke egyezik:

`5075ba3d9e368280464ded95b6705d76dda73150c17c8d7fce282b43d31f344b`

Ez a csomag és a generátor összhangját igazolja. A C/Z80 forrás teljes újrafordítását ebben a környezetben nem végeztem el; a reprodukció a mellékelt kész motorbinárisokból indult.

### Modellminőség és tanulás

A modell valóban generál karaktereket. A host próba során a `hello` bemenetre saját, de gyenge minőségű folytatást adott: `1 bamobbok al faczodek ez aszes azimos netolet ...`. Ez igazolja a generálást, de a nyelvi minőség még nem megfelelő.

A dokumentáció két tanulási szintet különít el:

- a tény-/profilmemória minden porton elérhető;
- az outputréteg súlyainak finomhangolása hoston és Amigán támogatott, nem a ZX81-es kiadásban.

Vagyis a ZX81-en a „tanulás” most elsősorban tartós tények eltárolása, nem a neurális súlyok helyben történő újratanítása.

### Futtatott tesztek

A `make test` a ZIP-ből kicsomagolt jogosultságok miatt `Permission denied` hibával indul. Közvetlenül `bash tests/run_tests.sh` paranccsal futtatva:

- 6 teszt átment;
- 5 teszt elbukott.

A bukások oka:
- a charset-teszt 45 karaktert vár, miközben a 16K változat készlete 48 karakter;
- a chat, finetune és golden teszt a normál `models/base_d.bin` modellt tölti, nem a ZX81-es `class G` modellt;
- a `scratch_e2e` a 45 karakteres `models/base_c.bin` fájlt próbálja betölteni, ezért ugyanazon modell-/karakterkészlet-eltérésen bukik el.

A `models16_v05/base_g.bin` fájllal külön tesztelve:

- golden: **100/100 vektor egyezett**;
- chat: **PASS**, determinisztikus kimenet és hosszkorlát rendben;
- finetune: **PASS** hoston; a vizsgált karakter logitja 257-ről 5420-ra nőtt.

A fordító több régi C89 függvénymutató-prototípusból eredő kompatibilitási figyelmeztetést adott. Ezeket érdemes rendezni.

**Korlát:** ebben a munkamenetben nem volt telepítve ZEsarUX vagy EightyOne, ezért a ZX81-es futtatást nem tudtam újra emulátorban ellenőrizni. A fenti eredmény bináris-/konténer- és hostteszt, nem friss emulátoros futás.

## 3. GLM retro-tinyllm v0.6.5 — későbbi, de forrás nélküli jelölt

A v0.6.5 csomag 227 923 bájtos, 15 blokkos EO81 állományt tartalmaz. A használati leírás a `/TOPIC` váltás és a chatbeli törlés javítását emeli ki. A `/quit` még nem állítja le a motort, és a valódi kijelző-/hardverteszt is hiányzik a leírás szerint.

**Korrekció az első gyors vizsgálathoz:** a blokkok elején látható nyolc bájt nem önmagában hibás adat. A mezők helyes értelmezése szerint ez a változat a `$4001–$4008` rendszerváltozó-résszel együtt tárolja a képet. `$4001` kezdőcímmel számolva `D_FILE=$7B00`, a boot `VARS=$7E19`, a rövid modell/témablokkok `VARS=$7AF5`, `RAMTOP=$7FFD`. Ez tehát eltérő képkezdési konvenció, nem bizonyított sérülés.

A fő hátrány: a v0.6.5 mappában nincsenek ott a módosított C/Z80 források és a csomagolóeszközök. Ezért csak bináris és használati leírás szintjén hasonlítható össze a v0.5.4-gyel.

**Javaslat:** maradjon összehasonlító célbináris; javításait csak a v0.5.4 forrásával összevetve, forráskóddal és emulátoros teszttel vegyük át.

## 4. Mistral — egyblokkos, szerkezetileg érdekes prototípus

A Mistral fájl egy EO81 blokkot tartalmaz, 15 437 bájt teljes konténermérettel és 15 385 bájt adatképpel. `$4009` kezdőcímet feltételezve:

- `D_FILE=$7908`;
- `VARS=$7C21`;
- `E_LINE=$7C22`;
- a 793 bájtos képernyőstruktúra megtalálható;
- a 25 darab szabályos `0x76` sor-/zárópozíció megvan, a többi cella biztonságos karaktertartományban van.

A kritikus kérdés a `$4026` RAMTOP mező: a binárisban `$FFFD` szerepel. Ez nem illeszkedik a 16 KB-os ZX81 `$7FFD` felső RAM-határához. Ellenőrizni kell, hogy a program később átállítja-e, vagy a kép más RAM-méretre készült. Forráskódot, tréningkorpuszt és generátort nem találtam.

**Javaslat:** emulátorban próbálható, de a RAMTOP tisztázásáig nem tekinthető igazolt 16K kiadásnak.

## 5. Claude és RETRO-TINYAI — valószínű rendszerváltozó-eltolódás

A Claude EO81 fájlja 7 blokkot tartalmaz; az indító `RTCHAT` blokk 15 891 bájtos. A RETRO-TINYAI UI-fájl egy `RTCHAT-BOOT` blokkot tartalmaz, hasonlóan 15 891 bájtos adatképpel.

Mindkét adatképen `FF 00` az első két bájt. Ha a betöltő a többi vizsgált EO81-fájlhoz hasonlóan `$4009`-re helyezi az adatot, a `$400C` címen levő `D_FILE` mutató értéke `$0001` lesz, nem a képernyő tényleges címe. A Claude-hoz mellékelt EightyOne képernyőképen két függőleges fekete sáv látszik; ez összhangban van a hibás D_FILE mutatóval.

A mintázat különösen gyanús, mert a GLM v0.5.4 műszaki jegyzete egy korábbi képfájl-változatnál már leír egy `FF 00` előtag okozta, hasonló eltolódást.

**Fontos:** nem javaslom a két bájt vakon történő törlését. Először a célbetöltő tényleges kezdőcímét kell rögzíteni, majd a rendszerváltozókat ahhoz igazítani. A Claude-változatnál ez a legvalószínűbb hibaforrás.

## 6. ZX81 TINYLLM 16K csomagok

A `zx81_tinyllm_16k_pack/` egy közel teljes, 15 892 bájtos `tinyllm-16k.p` fájlt, receptdemót és négy kisméretű témacsomagot tartalmaz. A README részletes memóriatérképet, `$7B00` D_FILE címet, 12,5 KB tématerületet és automatizált témabetöltést ír le.

A README szerint a `build_tinyllm_16k.py` assembler/generátor forrása is a csomagban van, de ez a fájl a ZIP-ben nem található. A fő `.p` kép `$4026` RAMTOP mezőjében `$FFFF` szerepel, ami külön ellenőrzést igényel. A kisebb, 2627 bájtos `zx81_tinyllm_16k_csomag/tinyllm_16k.p` nem azonos a teljes, közel 16 KB-os képpel.

**Javaslat:** az ötleteket és a topic binárisokat őrizzük meg, de forrás/generátor és helyes RAMTOP-igazolás nélkül ne erre építsük a fő projektet.

## 7. Rangsor

| Jelölt | Erősség | Fő kockázat | Javasolt szerep |
|---|---|---|---|
| GLM v0.5.4 | Teljes forrás, C89 motor, tréning, 16K build, újragenerálható 15 blokk | Gyenge nyelvi minőség; elavult tesztfuttató; emulátoros újrateszt kell | **Elsődleges fejlesztési alap** |
| GLM v0.6.5 | Későbbi bináris, topicváltás/törlés javításai | Forrás és generátor hiányzik; `/quit` ismert hibája; valós képernyőteszt hiányzik | Összehasonlító célbináris |
| Mistral | Egyblokkos fájl, konzisztens D_FILE és képernyőstruktúra | `$FFFD` RAMTOP; forrás és tréninganyag nincs | Emulátoros próbajelölt |
| Claude | Több témapakkos próbálkozás | `FF 00` prefix mellett `$0001` D_FILE lehet | Hibakeresési példa |
| RETRO-TINYAI UI | Önálló boot/UI próba | Ugyanaz a gyanús `FF 00` előtag; nincs forrás | Hibakeresési példa |
| TINYLLM 16K pack | Részletes UI-, téma- és memóriakoncepció | Builder hiányzik, RAMTOP `$FFFF`, nem reprodukálható | Ötlet- és binárisreferencia |

## 8. Kapcsolódás a PIOCO-hoz

Nem javaslom a GLM- és PIOCO-motor teljes összeolvasztását. Két külön modellcsaládról van szó:

- **GLM:** karakterenkénti, int8 súlyokkal dolgozó kis neurális nyelvi modell, teljes futtató- és téma-/memóriarendszerrel.
- **PIOCO:** szó-/szótag-/utótag-tokenekre épülő statisztikai trigramgenerálási irány, amelynél a tényleges ZX81 chat-kör még fejlesztendő.

A GLM-ből a memóriatérkép, D_FILE-kezelés, ROM-os betöltési lánc, témapakk- és mentési logika, host szimulátor és build-/tesztfolyamat hasznosítható. A PIOCO-ból a morfológiai tokenizálás, normalizálás, ismeretlen szavak és a témánkénti szó-/trigram-tudás ötletei maradhatnak külön ágban.

A következő motorválasztást méréshez kötném: ugyanazt a legalább 30 promptot futtassuk a GLM class G és a PIOCO host referencián, és pontozzuk az érthetőséget, relevanciát, ismétlést, időt és memóriaigényt.

## 9. Következő gyakorlati lépések

1. A GLM v0.5.4-et rögzítsük tiszta, visszaépíthető alapverzióként.
2. A tesztfuttatót igazítsuk a 48 karakteres `class G` kiadáshoz, és javítsuk a C függvénymutató-prototípus figyelmeztetéseit.
3. A v0.6.5-ből kérjük be a hiányzó forrásokat és módosított generátort, vagy készítsünk hozzá külön összehasonlító munkát.
4. Emulátorban ellenőrizzük a GLM v0.5.4 és v0.6.5 betöltési láncát, majd a Mistral RAMTOP mezőjét.
5. Csak ezután válasszunk végleges motort és építsünk új, saját nevű kiadást.

**Amit ez az audit nem állít:** nem történt friss EightyOne/ZEsarUX futás az összes feltöltött binárison, és a Mistral/Claude/TINYLLM belső Z80-kódjának teljes visszafejtése sem készült el. Az ezekre vonatkozó következtetések szerkezeti vizsgálaton, a csomag leírásain és a mellékelt képernyőképeken alapul.
