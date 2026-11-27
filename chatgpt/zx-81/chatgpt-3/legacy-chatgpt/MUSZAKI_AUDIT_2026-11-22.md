# PIOCO AI — műszaki audit (2026-11-22)

## 1. Forrásalapú állapot

A \`main\` ág legutóbbi megvizsgált commitja:

- Commit: \`8fd2bbba4156b6928e429e24d1e94ee3b13b1e1f\`
- Fejlesztési napló: 3. fázis, 10. szelet, D-4.2
- Kiadás: \`kazetta/pioco-0.6.p\`, 5100 bájt

A napló és a \`docs/HASZNALAT-0.6.txt\` szerint a fájlt ZEsarUX 13.1-B1 emulátorban két úton ellenőrizték: közvetlen memóriakép-betöltéssel és ROM-os szalagbetöltéssel. A boot lefut, a D_FILE címe 0x4200, a képernyőn a PIOCO AI / 16K PIOCO 0.6 splash látszik. A legutóbbi restart-hibát az okozta, hogy a .P fejléc NXTLIN mezője az XOR-kódolt hordozóra mutatott; a javítás az autostart sor 0x407D címét állítja be, és a \`pfuttatas.py\` fejléc-kapuja ellenőrzi a fejléc összes releváns bájtját.

**Ez valódi emulátoros boot-igazolás, nem a teljes beszélgető modell tesztje.**

## 2. A legfontosabb hiányzó funkció

A jelenlegi \`motor/motor0.asm\` a splash kiírása után ezt futtatja:

    MWAIT: JR MWAIT

A motor tehát jelenleg elindul és várakozik. A következők még nincsenek bekötve Z80-on:

- ROM INPUT / billentyűzetkezelés és a fő beszélgetési ciklus;
- bemeneti karakterlánc tokenizálása;
- szándék- és tényréteg Z80-oldali meghívása;
- trigram-jelöltek keresése és következő token generálása;
- temperature-alapú kiválasztás, generálási korlátok és megszakítás;
- chat history bejegyzések és görgetés;
- inverz üzenetfejlécek, időbélyeg, token-szám, válaszidő és thinking státusz;
- végleges többblokkos .T81 csomagolás és blokk-ellenőrzés;
- mentés és visszatöltés teljes, valódi gépi tesztje.

A README és a korábbi naplórészek egy része korábbi verziót említ; a legfrissebb állapothoz a napló utolsó D-4.2 bejegyzése és a forrásfájlok az irányadók.

## 3. Ami már jó alap

- \`motor/boot.asm\`, \`motor/motor0.asm\`: a boot és a minimális rezidens motor forrása.
- \`eszkozok/tokengen.py\`: a szótár és a trigramtábla generátora.
- \`eszkozok/token_demo.py\`: PC-oldali bemeneti tokenizálási referencia és viselkedési próbák.
- \`eszkozok/pgen.py\`, \`eszkozok/pfuttatas.py\`: .P előállítás és szerkezeti/virtuális ellenőrzés.
- \`eszkozok/zvaloditest.py\`: ZEsarUX-alapú valódi emulátorteszt.
- \`tudas/alap_korpusz_en.txt\`, \`tudas/alapmag_slotok.txt\`: angol korpusz és válasz-slot manifeszt.
- \`kazetta/adat/szotar.bin\`: 2304 B; \`alapmag.bin\`: 2048 B.
- A korpusz és a szótár már tartalmaz múlt időre/többes számra irányuló példákat, DO/DOES alakokat, smiley-kat, önazonossági tényeket, nyelvválaszokat és közmondást.

## 4. A specifikáció és a forrás közti eltérések

### 4.1 BOOT méret

A fázis-2 memóriatáblázat a 0x4082–0x41FF tartományt 464 bájtosnak írja. A címhatárokból számolt méret azonban:

    0x41FF - 0x4082 + 1 = 382 bájt

A dokumentációt javítani kell. A memóriatérkép minden zónáját géppel ellenőrzött cím- és hosszasserttel kell kezelni.

### 4.2 Tokenek

A tényleges \`tokengen.py\` 29 funkciótokent rögzít a 0x20–0x3C sávban; a tartalmi szótokenek 0x3D-től indulnak, majd 16 betűtoken következik 0xF0–0xFF között. Egyes tervezési szövegek még 28 funkciótokent és 0x3C kezdőcímű tartalmi tartományt említenek. A forrásgenerátor, a Z80-konstansok és a dokumentáció egyetlen verziózott kiosztást használjon.

### 4.3 Trigram súlyok

A terv több helyen 4 bites előjeles súlyt (-8..+7), illetve két súlyt/bájt említ. A tényleges szótárgenerátor jelenleg 4 bájtos rekordokat készít:

    [előző_token_1, előző_token_2, következő_token, súly]

A súly alsó nibble-je 0..7 korpuszgyakorisági pontszám; a felső nibble tartalék. Ez jelenleg nem tanult neurális súly és nem két súly/bájt. Első működő generátorhoz ez elfogadható, de a dokumentációt a valós formátumhoz kell igazítani. Később csak mérhető előny esetén váltsunk más kvantálási formára.

### 4.4 .P és .T81

A v0.6 igazolt terjesztési fájlja .P. A .P formátum nem azonos a célként kitűzött többblokkos .T81 formátummal. A meglévő régi \`pioco-0.1.tape\` nem bizonyítja a végleges multiload specifikációt. A .T81-hez külön blokkszintű fejléc, típus, verzió, célcím, hossz, CRC, sorrend- és hiányzóblokk-ellenőrzés szükséges.

### 4.5 PERSIST és ROM-verem

A tervezett tartós blokk 0x7E00–0x7EFF. A 0x7F00–0x7FFF tartomány a ROM veremének és képernyőmegszakítási koreográfiájának területe; oda a program nem írhat. Minden betöltőblokk célcímtartományát még az első bájt írása előtt ellenőrizni kell, és a PERSIST-et minden nem profilblokk számára ki kell zárni.

Az XOR-maszk és CRC-16 sérülésfelismerésre szolgál; nem titkosítás és nem adatvédelmi garancia. A személyes profiladatok megadását átugorhatóvá kell tenni, és a felhasználó kifejezett jóváhagyása nélkül nem szabad menteni.

### 4.6 D_FILE és 0x76

A ZX81 képernyőmemóriája végrehajtott display-file struktúra. Normál glifek: 0x00–0x3F; inverz glifek: 0x80–0xBF. A 0x76 csak a szabályos sorvégeken és a végső stop-helyen engedélyezett. Minden bináris token-ID, flag, cím és CRC dekódolás nélkül tilos a képernyőre írni.

A 0x76 általános RAM-adatként önmagában nem tiltott; a veszély a D_FILE szerkezetében van. Egyetlen print-funnel legyen az egyetlen képernyőíró kapu, és a puffer-ellenőrzés ellenőrizze a sorvégeket és a végső stop bájtot is.

## 5. A viselkedési extrák valós állapota

A \`token_demo.py\` tartalmaz obszcén szólistát, Levenshtein-1 közeli egyezés demót, sortörési szabályt és ismeretlen szó echo-tanulására vonatkozó leírást. Ezek PC-oldali demonstrációk és specifikációk, nem kész Z80-funkciók.

Különösen fontos: a tokenizáló demó a közeli szavakat felsorolja, de a fő \`tokenize()\` útvonal még nem javítja automatikusan a felhasználói szót. A tényleges Z80-motorba csak akkor kerülhet funkcióként, ha külön regressziós teszt és RAM-időmérés igazolja.

A számok most szöveg-tokenek. Ez megőrzi az „8 00” vagy „10 30” alakot, de nem jelent matematikai vagy naptári műveletet. A hét napját külön, determinisztikus Gergely-naptár algoritmussal kell kiszámítani a bekért dátumból. A FRAMES a betöltés óta eltelt időt méri, de önmagában nem tudja megállapítani a valós dátumot.

A „Mit tennél, ha egy napra ember lehetnél?” kérdésre a statisztikai modell csak akkor tud használható választ generálni, ha a korpusz tartalmaz megfelelő témájú összefüggéseket. Ez generált tokenfolytatás lesz, nem mai LLM-szintű szabad következtetés.

## 6. Javasolt generálási modell

A ZX81-en a reális megoldás:

1. kisbetű/nagybetű és írásjel normalizálása;
2. egész szó → szótő + utótag → betűtokenes fallback;
3. az utolsó két token alapján trigramjelöltek gyűjtése;
4. gyakorisági súly szerinti rangsorolás;
5. temperature 1–4 szerinti determinisztikus / változatos választás;
6. token dekódolása, toldalékok visszaépítése és egész szavas tördelés;
7. külön, kis tény- és állapotmemória, csak ha a kérdéshez tényleg releváns.

A rövid, biztos tények (például alkotó neve) maradhatnak külön slotokban; az általános beszélgetés viszont a trigramgenerátorból épüljön. A két útvonalat világosan külön kell választani a tesztekben.
