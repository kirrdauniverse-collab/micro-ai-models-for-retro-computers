# Fejlesztés: építés, tesztelés, verziókövetés

## Követelmények

- Python 3 (csak standard könyvtár: `re`, `struct`, `sys`, `os`, `random`; a referencia-modellhez
  és a tanító szkriptekhez NumPy kell).
- Git.

## Építés

```
python3 tools/make_dist.py
```

Ez a `models/*.bin` fájlokból és a `src/*.asm` forrásból elkészíti a `dist/` mappa
összes fájlját; a fájlnevekbe a `VERSION` fájl verziója kerül.

## Tesztelés

Az összes teszt a saját Z80-emulátoron (`tools/z80emu.py`) fut; a billentyűzetet a
ROM-matrix szerint szimulálja (`tests/run_app.py`).

```
python3 tests/regress.py     # fő regresszió (10 eset)
python3 tests/ref_gen.py     # greedy generálás a Python-referenciával
python3 tests/clock_test.py  # óra: FRAMES-lépésekkel
python3 tests/calib.py       # forward-menet költsége (FWD_FR kalibrálás)
python3 tests/log_view.py    # csevegőnapló dekódolva (fordított fejlécekkel)
```

Megjegyzés: az emulátor **nem** modellezi a keretmegszakítást, ezért a `FRAMES` értékét a
teszt maga állítja (lásd `clock_test.py`). A valódi óra működését EightyOne-ban kell
ellenőrizni.

## Verziókövetés

- A verzió a `VERSION` fájlban van, és a kiadási fájlnevekben.
- Tagek: `v1.0.0` (az első kiadás, a zip tartalma), `v1.1.0` (ez a verzió).
- Commit-üzenetek: rövid összefoglaló, majd részletek; a végén a szerzői sorok.
- Új kiadás menete: a forrás módosítása → `VERSION` átírása → `tools/make_dist.py` →
  `tests/regress.py` → `CHANGELOG.md` bővítése → commit → `git tag -a vX.Y.Z`.

## Mappaszerkezet

```
src/       Z80 forrás (app1, app3–app7, engine)
tools/     összeállító, emulátor, képépítő, referencia-modell
tests/     regresszió és diagnosztika
models/    RTLM v2 modellek (.bin)
ref/       exp-tábla forrása (rt_lut.h)
knowledge/ tudástárak (korpuszok)
training/  korpusz- és tanító szkriptek (a csomagból)
dist/      kiadási képek (.P, .t81)
docs/      dokumentáció
```
