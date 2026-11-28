# Tudástárak (knowledge bases) – tartalom és szerepük

A tudástárak a `knowledge/` mappában vannak; a tanító szkriptek a `training/` mappában.
A korpuszokat sablonok állítják elő (`training/corpus_gen.py`, fix véletlen mag: `20260117`),
így a fájlok reprodukálhatóak.

## Fájlok

| Fájl | Méret | Sorok | Szerep |
|---|---|---|---|
| `knowledge/base.txt` | 1,20 MB | 45 495 | Az alapmodell (`RTCHAT`) tanítókorpusza: kisbeszéd, matematika, minden téma keveréke |
| `knowledge/val.txt` | 0,06 MB | 2 185 | Validációs korpusz (a tanítás ellenőrzéséhez) |
| `knowledge/topics/weather.txt` | 0,32 MB | 14 201 | WEATHER téma (eső, nap, hőmérséklet, szél) |
| `knowledge/topics/animals.txt` | 0,37 MB | 12 801 | ANIMALS téma (kutyák, macskák, állatok) |
| `knowledge/topics/jokes.txt` | 0,13 MB | 4 201 | JOKES téma (viccek) |
| `knowledge/topics/numbers.txt` | 0,14 MB | 7 201 | NUMBERS téma (számolás, egyszerű műveletek) |
| `knowledge/topics/greetings.txt` | 0,77 MB | 32 201 | Üdvözlések (a csomagban van, ZX81-es modell nincs hozzá) |
| `knowledge/topics/retro.txt` | 0,68 MB | 19 801 | Retro számítógépek (a csomagban van, ZX81-es modell nincs hozzá) |

A korpuszok formátuma: a kérdés egy sor, a válasz a következő sor, mindkettő
kisbetűs angol szöveg; a sor végén sortörés. Példa a `weather.txt`-ből:

```
what is the weather like?
today is foggy outside my window.
is it raining?
yes, take an umbrella!
```

## Melyik modell melyik tudástárból

| Modell (`models/`) | Tanítókorpusz (`knowledge/`) | Megjegyzés |
|---|---|---|
| `base_f.bin` (RTCHAT) | `base.txt` | alapbeszélgetés |
| `topic_weather.bin` | `topics/weather.txt` | |
| `topic_animals.bin` | `topics/animals.txt` | |
| `topic_jokes.bin` | `topics/jokes.txt` | |
| `topic_numbers.bin` | `topics/numbers.txt` | |

A `.bin` modelleket a csomag `models16/` mappájából másoltuk. A **pontos F-osztályú tanítási
futás** (ctx 8, emb 10, h1 16) nincs a csomagban: a `training/train.py` súgója a D osztályt
(ctx 8, emb 16, h1 40) írja le. Ezt a következő kiadásban pótolni kell, hogy a modell újra
előállítható legyen.

## Minőség (mért)

- A Python-referencia (greedy) angol kérdésekre:
  - `base_f`: `what is 6 plus 6?` → `3 fmy felpere?` (zagyva); `is it raining?` → `i am smeant.`
  - `topic_weather`: `is it raining?` → `yes, take an umbrella!` (a korpuszban is szerepel); `what is 6 plus 6?` → zagyva.
- Magyar kérdések (`szia`, `hogy vagy`) mindhárom modellen zagyvák, mert a korpusz angol.
- A Z80-program kimenete ugyanezekre a bemenetekre karakterről karakterre egyezik a referenciával.

## Mit kellene a következő verzióhoz

1. Magyar nyelvű tanítókorpusz (a jelenlegi 4 témához és az alapbeszélgetéshez).
2. Nagyobb modell: a 16 KB-os memóriában ~3 KB szabad hely van (`$6F00`–`$7AFF`) és a modell
   jelenleg 2,6 KB; egy ~4–5 KB-os modell még elfér, a `$5500` kezdetű terület bővítésével.
3. Az F-osztályú tanítási folyamat (`training/train.py`) dokumentálása és újrafuttatása.
