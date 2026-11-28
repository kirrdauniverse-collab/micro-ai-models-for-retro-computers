# Architektúra és memóriatérkép (v1.1.0)

## Összetevők

| Fájl | Feladat |
|---|---|
| `src/app1.asm` | Belépés (`$4082`: `BOOT`, `GEN`, `INIT`, `FWD`), billentyűzet (`KSCAN`, `GETKEY`), konzol (`PUTC`, `NEWLINE`, `REDRAW`, `CLS`) |
| `src/app3.asm` | Védett állapot (`ST`, `$7F00`): csomagolás, mentés, betöltés, ellenőrző összeg |
| `src/app4.asm` | Cím, kézikönyv-kérdés, beállító párbeszéd (nap, dátum, idő, név, nem), szövegkiírás |
| `src/app5.asm` | Sorolvasó (`READ_LINE`), parancsok (`HANDLE`), kulcsszavak, fő ciklus (`APP`) |
| `src/app6.asm` | Turbo kazettabetöltő (kikapcsolva, `TURBO_ON = 0`) |
| `src/app7.asm` | **Új v1.1.0:** óra, fejléc (0–2. sor), inverz csevegő-fejlécek, számlálók |
| `src/engine.asm` | Z80 neurális mag: beviteli leképezés, előrefelé menet, mintavétel, válaszgenerálás |
| `tools/build_image.py` | Összeállítás, a memória-kép (`.P`) és az EO81 (`.t81`) előállítása |
| `tools/make_dist.py` | Az összes kiadási kép legyártása (`dist/`) |

## A modell

- Formátum: **RTLM v2**, int8, 2666 bájt, osztály **F**.
- Kontextus (`ctx`) 8 karakter, beágyazás (`emb`) 10, rejtett réteg (`h1`) 16, szótár (`vocab`) 45.
- Szótár: index 0 = sortörés, 1 = szóköz, 2–27 = `a`–`z` (ZX81 nagybetűk erre képződnek le),
  28–29 = `,` `.`, 30 = `?`, 33–42 = számjegyek, 43 = `:`, 44 = `-`.
- Forward-menet: beágyazás → rejtett réteg (ReLU, 0–127 vágás) → kimeneti logitok
  (bitre pontosan megegyezik a `tools/ref_rtlm.py` Python-referenciával).
- Mintavétel: `greedy = 1` (alapértelmezés) a legnagyobb logit; `greedy = 0` esetén
  `TSH` hőmérséklet-eltolással súlyozott véletlen választás.
- A felhasználói sort a motor a modell kontextusába tölti, **utána sortörést (index 0)**
  tesz (v1.1.0-tól), így a bemenet a tanítási formátumot követi: `kérdés⏎válasz⏎`.

## Futási mód: SLOW és FAST

- A ZX81 `CDFLAG` ($403B) 6. bitje (`IY = $4000`): 1 = SLOW (a kijelző fut, `FRAMES` számol),
  0 = FAST (a kijelző és a `FRAMES` leáll, a CPU teljes sebességgel dolgozik).
- Alapértelmezés (v1.1.2-től): a `GEN_STEP` minden lépése SLOW módban fut, a kijelző
  végig látszik, a válasz élőben íródik (~3 s/karakter).
- **SHIFT-F** (`FASTF` = $61CC, 1 = BE): ilyenkor csak a forward-menet fut FAST módban;
  a mintavétel és a kiírás SLOW módban. Ez ~0,4 s/karakter, de a számítás alatt a kijelző
  fehér (v1.1.1-ig ez volt az alapértelmezés).

## Óra és időmérés (app7)

- Az óra percekben (`CLK_MIN`, 0–1439) és a perc-maradék keretekben (`CLK_FR`, 0–2999) áll.
  A beállító párbeszéd `IDO (OO PP)` kérdése állítja be (`SET_CLOCK`).
- A `FRAMES` ($4034) PAL-ban 50 keret/s. **Feltevés:** ez a számláló csökken (a FAST
  művelet nullázza; a szerzői leírás szerint). Az `CLK_SYNC` és a `TICK_SLOW` ezért
  `régi − új` különbséget számol. **Ellenőrizendő** az EightyOne-ban: ha az óra visszafelé
  jár, a két `sbc hl,de` sorrendjét meg kell fordítani.
- Minden szabad GETKEY-ciklus szinkronizálja az órát, és frissíti a fejlécet.
- **Válaszidő** (`GFR`): a SLOW-részek FRAMES-különbsége + forward-menetenként 20 keret
  (`FWD_FR`, becslés; az emulátoros T-állapot-mérés alapján kalibrálva).
- A munkamenet-számláló (`SESS_TOK`) a `BE + KI` tokenek összege; indításkor nullázódik.

## Fejléc és csevegő-fejlécek

- A fejlécet a `HDR_DRAW` rajzolja a D-fájl 0–2. sorába; csak csevegés közben aktív
  (`HDR_ON`). A `GETKEY` szabad ciklusából hívódik.
- A csevegő-fejlécet a `CH_OPEN` írja (időbélyeg, placeholder-ek), majd a `CH_CLOSE`
  átírja a tényleges számokkal (`BE`, `KI`, `V`). A sor a naplóban van (`HDR_ROW`),
  fordított videóban (kód + 64).

## Memóriatérkép (v1.1.0)

| Cím | Tartalom |
|---|---|
| `$4009`–`$407C` | Rendszerváltozók (`.P` fejléc) |
| `$407D` | `REM` sor (a teljes program ide van rejtve) + `RAND USR 16514` |
| `$4082`–`$5213` | Kód: `app1`, `app3`–`app7`, `engine` (kb. 4,2 KB) |
| `$5500`–`$5F69` | RTLM modell (2666 B) |
| `$5F6A` | Témaazonosító (0 = alap) |
| `$5F80`–`$5FEC` | Karaktertáblák (MAPIN / MAPOUT) |
| `$6000`–`$6168` | Motor munkaterülete (`WIN` `$6000`, `INBUF` `$6010`, `XBUF` `$6040`, `HBUF` `$6090`, `LGBUF` `$60A0`, `WBUF` `$6100`, `ACC` `$6140`, `TSH` `$6164`, `GREEDY` `$6165`, `NOUT` `$6167`) |
| `$6169`–`$617F` | szabad |
| `$6180`–`$6197` | Keret változói (`LOGHEAD` `$6180`, `COL` `$6181`, `VOFF` `$6182`, `ROMSP` `$6183`, `SHFLAG` `$6185`, `TOPIC` `$6186`, `SS_B0..2` `$6190`, `MT_P` `$6194`, `MT_I` `$6196`, `RESTORED` `$6197`) |
| `$6198`–`$61CB` | **Új v1.1.0:** fejlécpuffer (`HDRB` 32 B), óra (`CLK_MIN`, `CLK_FR`, `CLK_F`), `GFR`, `SESS_TOK`, `HDR_ROW`, `HDR_ON`, `HDR_H/M`, decimális író |
| `$61CC` | **Új v1.1.2:** `FASTF` (SHIFT-F, gyors mód) |
| `$61CD`–`$61FF` | szabad |
| `$6200`–`$69FF` | Csevegőnapló: 64 sor × 32 cella (körpuffer) |
| `$6A00`–`$6DFF` | Négyzettábla (`sq[n] = n²/4`, 512 bejegyzés, `SQB = $6C00`) — **v1.1.0-ban áthelyezve** |
| `$6E00`–`$6EFF` | Exp-tábla (mintavételhez, 256 B, `EXPS = $6E00`) — **v1.1.0-ban áthelyezve** |
| `$6F00`–`$7AFF` | szabad (≈ 3 KB) |
| `$7B00`–`$7E18` | D-fájl (kijelző, 25 × 33 bájt): 0–1. sor fejléc, 2. sor elválasztó, 3–23. sor csevegő |
| `$7E19` | VARS (a `.P` vége) |
| `$7EF0` | Verem teteje |
| `$7F00`–`$7F17` | **Védett állapot** (24 B, a `.P` képen kívül; topic `LOAD` után is megmarad) |

**Megjegyzés:** a mentéskor a védett állapot tömörítve a D-fájl 0. sorába kerül, hogy a
BASIC `SAVE` elmentse. A `QUIT` ezt utoljára írja, így a mentett kép helyes marad, a
kijelző felső sorai utána a tömörített adatot mutatják.

## Ellenőrzött tulajdonságok (tesztek)

- `tests/regress.py`: beállítás + csevegés + kilépés; név; visszatöltés; esemény-kérdés;
  esemény törlése; témaprompt; fejléc 0–1. sor; csevegő-fejléc; óra.
- `tests/ref_gen.py`: greedy generálás a Python-referenciával (`tools/ref_rtlm.py`).
- `tests/clock_test.py`: az óra FRAMES-lépésekkel előre megy.
- `tests/calib.py`: forward-menet T-állapot-költsége (FWD_FR kalibrálás).
