# PIOCO AI — fejlesztési útiterv

## Első prioritás: a beszélgetési kör

A v0.6 után a következő mérföldkő ne újabb splash legyen, hanem a minimális, egykörös beszélgetés:

    ROM INPUT
      → normalizálás
      → tokenizálás
      → szándék-/tényillesztés
      → trigramjelöltek
      → generálás
      → biztonságos képernyőírás
      → chat history

Először egy kérdésre egy válasz működjön. A görgetést, rajzot, BASIC-szerkesztést, emlékeztetőket és témapakk-kezelést csak ezután bővítsük.

### v0.7 — PC referencia és első Z80 chat-kör

- A \`CHATGPT/host_reference_chat.py\` ugyanazzal a \`szotar.bin\`-nel vizsgálja a tényleges trigramfolytatásokat.
- A generátor pontosan dokumentált bemenetet, kontextust és kimenetet adjon.
- Z80 oldalon az INPUT-ból vett egyetlen sor feldolgozása és egy válasz generálása legyen az első végpont.
- A „WHO MADE YOU?” és „WHO IS SAFAR SANDOR?” ténykérdés maradhat külön, ellenőrzött slot.
- Ismeretlen bemenet nem okozhat végtelen keresést vagy tiltott D_FILE-írást.

**Kiadási kapu:** a PC referencia és a Z80 port legalább 20 azonos tesztbemenetre egyező tokenválasztást adjon temperature=1 mellett.

## v0.8 — chat UI és vezérlők

- Inverz fejlécek a felhasználói és modellüzenetek fölött.
- Időbélyeg, bejövő/kimenő token-szám, válaszidő.
- Rövid thinking státusz; a belső állapot ne legyen teljes szövegesen kiírva.
- Temperature 1–4, SHIFT+9 reasoning be/ki.
- SHIFT+5/6 chat-görgetés, SHIFT+S mentés, SHIFT+SPACE megszakítás.
- Egész szavas sortörés, 32 oszlopos korlát; hosszú szó önálló sorba kerül.
- Korlátozott history körbuffer, túlcsordulás tesztje.

**Kiadási kapu:** minden vezérlő valós eseményt indít, a képernyő és a history nem sérül, a token- és időmérés reprodukálható.

## v0.9 — dátum, emlékezet, multiload-biztonság

- Dátum bekérése; SKIP lehetőség a név/nem/születési adatokra.
- Külön Gergely-naptár algoritmus hét napja számításra; szökőévek tesztje.
- FRAMES csak az eltelt idő és session clock mérésére szolgál.
- PERSIST magic/verzió/CRC és 1 bites ténymezők, dátum- vagy napbélyeggel.
- Elavult adatnál a motor kérdezzen rá, és ne kezelje megerősített tényként.
- Minden loaderblokk célcímet és hosszot validáljon; PERSIST-tartományra csak a profilkezelő írhasson.

**Kiadási kapu:** rossz CRC, hiányzó blokk, rossz cím, PERSIST-átfedés és megszakadt betöltés mind biztonságos hibát ad.

## v1.0 — egyetlen .T81 multiload csomag

A .T81 saját, verziózott blokkformátumot kapjon:

- blokkazonosító, típus és formátumverzió;
- célcím és hossz;
- sorszám / sorrend és teljes blokkdarabszám;
- CRC-16;
- PERSIST- és ROM-veremzóna kizárása;
- hibás vagy megszakadt betöltés utáni helyreállás.

A turbo tape fejlesztés közben kikapcsolt marad. Először a gyári ROM LOAD út stabilitása kell, csak utána jöhet az opcionális gyors rutin.

## Korpusz és tréning

- Alapkorpusz: egyszerű beszélgetés, bemutatkozás, kérdések, érzelmek, udvariasság, számok.
- Nyelvtani korpusz: jelen/múlt idő, egyes/többes, DO/DOES, tagadás, rövidítések és gyakori elgépelések.
- Kérdés-válasz példák: nyelvtudás, alkotó, „egy napra ember lennél” típusú hipotetikus kérdések.
- Tematikus korpuszok: csillagászat, retro technika, tudomány, irodalom és más későbbi csomagok.
- A generátor minden futásnál mérje a szótárlefedettséget, trigramok számát, korpuszméretet, pack-méretet és a generált minták minőségét.

A tréningeszköz PC-n dolgozzon; a ZX81 a kész, tömörített adatcsomagot használja.

## Műszaki sorrend

1. A memóriatérkép és token-ID dokumentációs ellentmondásainak rendezése.
2. A host referencia tesztjei és golden kimenetei.
3. A Z80 tokenizáló és trigramkereső.
4. INPUT és teljes chat-kör.
5. UI és history.
6. PERSIST és dátumrutin.
7. .T81 multiload formátum és csomagoló.
8. ZEsarUX teszt minden blokkra és teljes láncra.
