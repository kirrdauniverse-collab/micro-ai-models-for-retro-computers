# Valódi motor terve – kilépés a tiszta BASIC-ből

## Állapot
A v0.1–v0.3 verziók szándékosan BASIC demók voltak, hogy a loader, a RAMTOP technika, a multi-load .T81 és a felhasználói adatbekérés stabilan működjön.  
Mostantól a fókusz a **valódi token-alapú motor** felé tolódik.

## Célarchitektúra (16 KB ZX81)

1. **Loader (BASIC)** – marad, mert praktikus az adatbekéréshez és a RAMTOP beállításhoz.
2. **Persistent Block** (RAMTOP felett) – név, nem, dátum, idő, beállítások, bitmezők. Gépi kóddal írjuk/olvassuk.
3. **Engine** (gépi kód):
   - Egyszerű tokenizer (szóköz + kisbetűsítés + kis vocab lookup)
   - Vocab tábla (string → ID)
   - Bigram vagy kis trigram tábla (következő token valószínűségek)
   - Generáló rutin (hőmérséklet + mintavételezés)
   - Kimenet kiírása a képernyőre (biztonságos karakterekkel)
4. **Tudáscsomagok** – cserélhető blokkok a védett vagy normál memóriában.

## Következő konkrét lépések (v0.4 felé)
- Persistent block bináris elrendezés + kis Z80 rutinek a mentéshez/olvasáshoz
- Minimális vocab + válasz-tábla gépi kódban (először még nem generál, csak lookup)
- USR-hívható rutin a válaszadáshoz
- Később: valódi bigram generálás

## Miért nem volt eddig gépi kód?
Először a kazetta-struktúrát, a RAMTOP védelmet és a multi-load .T81-et kellett stabilizálni.  
Mostantól a motoré a prioritás.
