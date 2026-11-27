# Fázis 2 – Részletes memóriatérkép (16 KB ZX81)

> **Fontos frissítés:** A tartós adatok és részben a tudásbázis a **RAMTOP feletti védett területre** kerül (lásd `docs/04-t81-structure-and-ramtop.md`). A címek ennek megfelelően finomítandók.

## Alapadatok
- Teljes RAM: 16 KB (16384 bájt)
- ROM: 8 KB (0000–1FFF)
- RAM kezdete: 4000h
- Tipikus ZX81 rendszerterület: 4000h–407Dh körül (rendszerváltozók)
- D_FILE: változó helyen, de általában a RAM eleje felé
- Cél: minél több hely a modellnek, miközben a rendszer stabil marad
- **RAMTOP technika:** A BASIC loader beállítja a RAMTOP-ot, majd NEW-t csinál → a felette lévő terület védett marad.

## Javasolt magas szintű felosztás

| Terület                    | Méret (kb.) | Megjegyzés |
|----------------------------|-------------|----------|
| Rendszer + stack + D_FILE  | ~1.5–2 KB  | ZX81 saját igénye + képernyő |
| Motor / keretprogram       | 3.5–4.5 KB | Tokenizáló + generáló mag + UI |
| Tartós adatok (user)       | 0.4–0.6 KB | Név, dátum, nem, beállítások, bitmezők |
| Chat history buffer        | 2.0–2.5 KB | Körkörös, görgethető |
| Alaptudás / vocab + modell | 7.5–9.0 KB | Tokenek, súlyok/probák, tudás |
| Tartalék / szabad          | 0.3–0.8 KB | Későbbi bővítésre |

## Részletes címtérkép (előzetes, finomítható)

```
4000h – 407Fh   : ZX81 rendszerváltozók (érintetlenül hagyjuk, amennyire lehet)
4080h – 40FFh   : Saját rendszer flags + kis munkaterület
4100h – 41FFh   : Tartós felhasználói adatok (Persistent Block)
                  - Név (max 16 karakter)
                  - Születési dátum / kor
                  - Nem (1 bit)
                  - Aktuális dátum/óra (betöltéskor megadva)
                  - Temperature (2 bit)
                  - Reasoning flag (1 bit)
                  - Egyéb bitmezők (fejállapot, hangulat, stb.)
                  - Checksum / verzió

4200h – 4FFFh   : Motor + UI kód (kb. 3.5–4 KB)
                  - Tokenizáló
                  - Generáló mag
                  - Képernyőkezelő (inverz fejcímek, görgetés)
                  - Billentyűkezelő (SHIFT kombinációk)
                  - Multiload kezelő

5000h – 57FFh   : Chat History Buffer (2 KB)
                  - Körkörös buffer
                  - Minden üzenet: fejléc (ki, idő, token, időtartam) + szöveg
                  - Max üzenetszám: ~12–18 (hosszúságtól függően)

5800h – 7BFFh   : Tudásbázis + Vocab + Modelladatok (kb. 8–9 KB)
                  - Token szótár (string → ID)
                  - Inverz szótár (ID → string)
                  - Egyszerű valószínűségi táblák / n-gram / Markov
                  - Alaptudás mondatok / tények (tömörítve)
                  - Speciális válaszok (Who made you?, stb.)

7C00h – 7FFFh   : Stack + ideiglenes munkaterület + tartalék
```

## Bitmezők a tartós adatokban (példa elrendezés)

Egy bájt (FLAGS1):
```
bit 7: nem (0=férfi, 1=nő)
bit 6: reasoning on/off
bit 5-4: temperature (0–3)
bit 3: has_headache (példa)
bit 2: is_child / is_adult
bit 1: reserved
bit 0: valid_data flag
```

További bitek más bájtokban. Fontos: a bitmezőkből összeálló bájtok **soha ne legyenek 0x76** és ne tartalmazzanak parancskódokat, ha azok a D_FILE-ba kerülhetnek.

## D_FILE használat
- Alsó ~20–22 sor: chat megjelenítés + input
- Felső 1–2 sor: státusz (inverz)
- A D_FILE felső részét (ha van hely) lehet munkaterületként használni, de csak biztonságos karakterekkel.

## Multiload és tartós memória
A Persistent Block (4100h–41FFh) a boot sávban íródik, és a későbbi sávok **nem írják felül**.
A motor sáv betöltésekor ellenőrzi a valid_data flag-et és a checksumot.

## Megjegyzések
- A pontos címek a tényleges kódméret alapján fognak eltolódni.
- A tudásbázis lesz a leginkább tömörítendő rész.
- Chat history-t érdemes token ID-kkal tárolni a nyers szöveg helyett (helyspórolás).

## Következő dokumentum
04 – .T81 sávstruktúra és betöltési sorrend
