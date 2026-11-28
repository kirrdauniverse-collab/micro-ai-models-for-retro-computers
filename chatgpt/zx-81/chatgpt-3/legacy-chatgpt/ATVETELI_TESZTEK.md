# PIOCO AI — átvételi tesztek

A verzió csak a ténylegesen lefutott tesztekkel léphet tovább. A PC-s referencia, a Z80 kód és a kazettaformátum eredménye külön jelentendő.

## A. Bináris szótár

- [ ] A szótár pontosan 2304 B.
- [ ] A rekordtér ID-kiosztása 0x20–0xEF között folytonos.
- [ ] A 16 bájtos betűtábla minden eleme egyedi.
- [ ] A trigramtér 1000 B, 250 darab 4 bájtos rekord.
- [ ] A súlymező aktuális értelmezése 0..7, felső nibble tartalék.
- [ ] A bináris formátumverzió és CRC egyezik a generátorral.

## B. Tokenizálás és nyelvtan

- [ ] Kisbetű/nagybetű egységesítése.
- [ ] Pont, vessző, kérdőjel, felkiáltójel, pontosvessző megőrzése.
- [ ] :) :( :O smiley-k egyben maradnak.
- [ ] DON'T / DOESN'T és gyakori rövidítések normalizálása.
- [ ] -S / -ED / -ING / -LY szótő + utótag felbontás.
- [ ] Ismeretlen szó biztonságos betűtokenes kezelése.
- [ ] Elgépelés-javítás csak egyértelmű jelöltnél; kétértelmű szó nem javítható automatikusan.
- [ ] Ismeretlen szó munkamenetbeli visszahasználata nem írhatja át véletlenül a szótárat.

## C. Generálás

- [ ] A generátor az utolsó két tokenből trigramjelölteket keres.
- [ ] Konkrét egyezés hiányában a backoff szabály dokumentált.
- [ ] Temperature=1 azonos seed mellett reprodukálható.
- [ ] Temperature=2..4 ténylegesen nagyobb jelölthalmazból választ.
- [ ] A generálás tokenlimittel és mondatvégi leállással korlátozott.
- [ ] Ismeretlen kontextusnál kontrollált „nincs folytatás” eredmény, nem végtelen ciklus.
- [ ] A „WHAT IS YOUR NAME?”, „WHO MADE YOU?” és „WHO IS SAFAR SANDOR?” esetek teszteltek.
- [ ] A „WHAT WOULD YOU DO IF YOU COULD BE HUMAN FOR ONE DAY?” eset bekerül a korpusztesztek közé.

## D. Z80 és chat loop

- [ ] A motor0.asm MWAIT helyén valódi INPUT → feldolgozás → válasz → history kör fut.
- [ ] A PC referencia és a Z80 legalább 20 esetben ugyanazt választja temperature=1 mellett.
- [ ] A ROM INPUT karakteres módban használatos, és a képernyőmutatók megmaradnak.
- [ ] SHIFT+1..4, SHIFT+9, SHIFT+5/6, SHIFT+S, SHIFT+SPACE mind működik.
- [ ] A 32 oszlopos sortörés nem választ szét szót.
- [ ] Az inverz fejléc mutatja a timestampet, tokeneket és válaszidőt mindkét beszélgetőfélnél.

## E. Dátum és állapotmemória

- [ ] A hét napját a megadott dátum alapján algoritmus számítja.
- [ ] Szökőév: 2000 igen, 2100 nem.
- [ ] A FRAMES nem kerül valós naptári dátumként értelmezésre.
- [ ] Profiladatok bevitele átugorható.
- [ ] PERSIST CRC és verzió ellenőrzött.
- [ ] Elavult állapotnál a modell rákérdez, és csak visszaigazolás után módosít.

## F. RAM és képernyőbiztonság

- [ ] A memóriatérkép zónái nem fedik át egymást.
- [ ] A BOOT méret és címhatár egyező, automatikus teszttel.
- [ ] PERSIST 0x7E00–0x7EFF.
- [ ] ROM-veremzóna 0x7F00–0x7FFF írása tiltott.
- [ ] D_FILE: 25 × 33 + 1 bájt; szabályos sorvégek és stop.
- [ ] Glif csak 0x00–0x3F vagy 0x80–0xBF.
- [ ] 0x76 csak a D_FILE sorvégeken és a végső stop-helyen.
- [ ] Minden képernyőírás egyetlen ellenőrzött print-funnelön keresztül történik.
- [ ] Bináris token, flag, cím, CRC soha nem íródik közvetlenül a D_FILE-ba.

## G. Kazetta és kiadás

- [ ] A .P fejléc-kapu minden verzióban megmarad.
- [ ] A .T81 saját blokkformátuma külön tesztelt.
- [ ] Rossz sorrend, hiányzó blokk, hibás CRC és megszakított betöltés tesztelt.
- [ ] PERSIST felülírása lehetetlen nem profilblokkból.
- [ ] ZEsarUX snapshot és ROM-os tape út tesztelt.
- [ ] Gyors tape alapértelmezésben kikapcsolt.
- [ ] A build reprodukálja a kiadási binárisokat.
- [ ] A kiadási jegyzet pontosan jelzi, hogy mi futott tényleges hardveren/emulátoron.
