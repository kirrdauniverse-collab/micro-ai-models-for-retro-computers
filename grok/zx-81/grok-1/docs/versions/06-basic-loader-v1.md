# BASIC Loader – első változat

Fájl: `src/loader-basic-v1.bas`

## Mit csinál
1. Bemutatja a Pico AI-t (cím, készítő, rövid leírás)
2. Elmagyarázza a RAMTOP + NEW folyamatot
3. Figyelmeztet, hogy a következő blokkot manuálisan kell betölteni (`LOAD ""`)
4. ENTER-re beállítja a RAMTOP-ot 30000-re (később pontosítjuk) és NEW-t csinál

## Megjegyzések
- A szövegek szándékosan rövidek és világosak (32 karakteres sorokhoz igazítva)
- A RAMTOP érték (30000) csak kiindulási pont – a végleges memóriatérkép alapján állítjuk be
- A loader után a felhasználónak kell indítania a következő sávot

## Következő finomítások
- Pontos RAMTOP érték
- Esetleg felhasználói adatok bekérése már itt (név, dátum) – változókban, majd a következő sáv menti a védett területre
- Szebb elrendezés inverz karakterekkel (ha a BASIC engedi)
