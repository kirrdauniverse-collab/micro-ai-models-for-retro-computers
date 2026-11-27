# Fázis 2 – .T81 sávstruktúra + RAMTOP technika

## Alapötlet (felhasználói javaslat alapján)
A szalag elején egy egyszerű **BASIC betöltő** van, amely:
1. Röviden ismerteti a Pico AI-t és a működést
2. Elmagyarázza, hogy a felső memória / tartós adatok védelméhez szükséges a RAMTOP beállítása
3. Figyelmeztet, hogy ENTER után a gép NEW-t csinál és újraindul a védett területtel
4. A felhasználónak manuálisan kell elindítania a következő kazettablokkot (LOAD "")

Ez a klasszikus ZX81 módszer a védett felső memória használatára.

## Javasolt sávsorrend a .T81 fájlban

### Sáv 0 – BASIC Loader + Bevezető
- Típus: tiszta BASIC program
- Feladata:
  - Splash / rövid bemutatkozás
  - Használati útmutató (opcionális, Y/N)
  - Felhasználói adatok bekérése (dátum, óra, név, nem, születés) – ezeket ideiglenesen változókban tárolja
  - RAMTOP beállítása a kívánt értékre (pl. 30000 vagy a számított határ)
  - NEW parancs (a változók elvesznek, de a felső memória védett marad)
  - Üzenet: „Most indítsd a következő blokkot: LOAD "" ”
- A tartós adatok még nincsenek a felső memóriában – azokat a következő sáv írja oda.

### Sáv 1 – Persistent Block + Alapstruktúra
- Típus: gépi kódú blokk (vagy BASIC + CODE)
- Betöltés a védett területre (RAMTOP fölé)
- Tartalom:
  - Tartós felhasználói adatok (név, dátum, nem, beállítások, bitmezők)
  - Verzió / checksum
  - Esetleg üres chat history fejlécek
  - D_FILE újraépítése / átállítása, ha szükséges
- Ez a blokk **soha nem íül felül** a későbbi tudáscsomagok betöltésekor.

### Sáv 2 – Motor + UI + Tokenizáló
- A fő program (gépi kód)
- Betöltés a normál területre (RAMTOP alá)
- Inicializálja a rendszert, ellenőrzi a Persistent Block érvényességét
- Elindítja a chat felületet

### Sáv 3 – Alaptudás / Vocab / Modelladatok
- A nagy tudásblokk
- Betölthető a Persistent Block mellé / fölé a védett területre, vagy a motor mellé
- Később cserélhető speciális tudáscsomagokra (ugyanarra a helyre LOAD-olva)

### Későbbi sávok (opcionális)
- Speciális tudáscsomagok (tudomány, retro, egészség, stb.)
- Ugyanarra a címre töltődnek, felülírva az előző tudást, de a Persistent Blockot érintetlenül hagyva

## RAMTOP stratégia (javaslat)

Példa beállítás:
- RAMTOP = 30000 (kb. 0x7530)
- 4000h – 752Fh : normál programterület (motor, UI, ideiglenes)
- 7530h – 7FFFh : védett terület (~2.7 KB) → Persistent + részben tudás

Vagy agresszívabb:
- RAMTOP alacsonyabbra (pl. 28000), hogy több hely legyen a védett tudásnak.

A pontos értéket a végleges méretek alapján állítjuk be.

## Előnyök
- A tartós adatok (név, dátum, beállítások, chat history részben) túlélik a NEW-t és a későbbi betöltéseket
- Klasszikus, megbízható ZX81 technika
- A felhasználó tisztában van a folyamattal (nem „varázslat”)

## Hátrányok / figyelmeztetések
- A felhasználónak manuálisan kell indítania a következő blokkot (ez szándékos)
- Emulátorokban a RAMTOP + NEW viselkedését ellenőrizni kell
- A BASIC loadernek nagyon rövidnek és világosnak kell lennie

## Következő
- Tokenizáló alapelvek
- A BASIC loader pontos szövegeinek megírása
- Címek véglegesítése a memóriatérképen a RAMTOP figyelembevételével
