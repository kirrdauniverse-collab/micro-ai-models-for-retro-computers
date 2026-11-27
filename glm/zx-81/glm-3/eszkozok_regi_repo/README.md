# ZX81 AI micro language modell — „Pico AI”

Egy **valódi, generatív mini nyelvi modell a 16 KB-os Sinclair ZX81-en**,
tiszta Z80 assembly-ben, egyetlen `.T81` kazettafájlként, több betöltési
sávval (multiload lánc).

Készítette: **Sáfár Sándor** (GLM segítségével) — SAFIZX81 kukac GMAIL.COM
(a ZX81 nem ismeri a @ jelet: a címben inverz 0-s van a helyén).

```
   felhasználó ──INPUT──► tokenizáló ──► elemző (kérdés/hangulat/profanitás)
        ▲                                       │
        │                                       ▼
   képernyő ◄── biztonságos író ◄── GENERÁTOR ◄── súlyozott mintavétel
   (D_FILE)        (0x76-őr)        bigram+fogalom táblák  (hőmérséklet,
                                                            gondolkodási fázis)
```

## Mit tud a v0.1 (a részletek a docs/ mappában)

- **Valódi generálás**: a válaszokat bigram- és fogalomtáblákból állítja
  össze tokenenkénti mintavétellel (hőmérséklet: SHIFT+1..4), nem előre
  beégetett mondatokból. Gondolkodási mód (SHIFT+9) esetén második,
  súlyozó átfutás választ a jelöltek közül.
- **Multiload kazettalánc**: `PICOBOOT` (bejelentkező kép + profil) →
  `PICOBASE` (motor + alaptudás) → témacsomagok (`PICOASTR`, `PICOSCIN`, …).
  A tartós adatok (profil, megtanult szavak, emlékbitjeid) a képcserék alatt
  is a helyükön maradnak, és `/save` (SHIFT+S) a szalagra menti őket.
- **Emlékezés 1 biten**: a kétállapotú dolgok (nem, fáj-e a fejed, …) egy-egy
  biten élnek; lejárt emléket a modell elavultként felülírja.
- **Dátum- és időérzék**: a betöltéskor megadott dátumból **kiszámolja** a
  hét napját és az eltelt időt (naptárrutin, nem táblázat és nem beégetett
  válasz).
- **Billentyűk**: SHIFT+1..4 hőmérséklet, SHIFT+9 gondolkodás, SHIFT+5/6
  görgetés, SHIFT+S mentés, RUBOUT (SHIFT+0) megszakítás.
- **Biztonságos képernyő**: a D_FILE-ba csak érvényes karaktersorok
  kerülhetnek (0x00–0x3F, 0x80–0xBF inverz, 0x76 sorvég) — a motor minden
  cellaírást őrző rutinen át végez. A régi „futó fekete csíkok" hibája
  (érvénytelen bájtok a képernyő-memóriában) így szerkesztés közben is
  kizárt (lásd docs/02_tervezes.md).

## Mit jelent „valódi generálás” 16 KB-on?

A Pico AI nem LLM, hanem a 8 bites lehetőségekhez mért statisztikus
nyelvi modell: szótár + bigram-tábla + fogalom-társítások + mondattervek,
tokenenkénti súlyozott mintavétellel és hőmérséklet-vezérléssel. Ugyanaz a
kérdés máskor mást ad vissza; a válaszok a betöltött témacsomag korpuszából
származó szókincset használnak. A korpusz szöveges fájlokból a
`tools/kbtrain.py` tréningeli be — így bővíthető kazettánként cserélhető
tudáscsomagokkal (tudomány, csillagászat, gasztronómia, …).

## Repó tartalma

```
docs/     01_koncepcio.md, 02_tervezes.md, 03_formatumok.md, 04_regeszlet.md
engine/   Z80 források (boot, tokenizáló, generátor, képernyő, memória, szalag)
tools/    asm.py (Z80 assembler+disassembler), zx81sim.py (szimulátor),
          build_t81.py (kazettaépítő), kbtrain.py (tréner), archaeo.py (elemző)
data/     téma-korpuszok szöveges formában (bővíthető!)
tests/    szimulátoros tesztek (beszélgetési forgatókönyvek)
dist/     ZX81PICO.T81 + .P fájlok — ez megy az emulátorba/valódi gépbe
publish.sh  GitHub-közzététel segéd (bundle-lel)
```

## Kipróbálás (EightyOne emulátor)

1. `dist/ZX81PICO.T81` megnyitása tape/kazetta ként (File → Open Tape).
2. Gépeld: `LOAD ""` majd NEWLINE — betölt a `PICOBOOT` blokk; `RUN`.
3. A boot rákérdez az útmutatóra, majd dátum, idő, név, nem, születési év;
   utána magától láncol a `PICOBASE` blokkra és indul a csevegés.
4. Chat: kisbetűkkel írd az üzenetet, szóköz = SHIFT+NEWLINE, küldés = NEWLINE.

Fejlesztői gyorsstart: `python3 tools/build_t81.py` (épít) és
`python3 tools/zx81sim.py --script tests/chat_demo.txt` (beszélgetés a
szimulátorban, a D_FILE-őrszem minden cellaírást ellenőriz).

## Licenc

MIT (lásd LICENSE).
