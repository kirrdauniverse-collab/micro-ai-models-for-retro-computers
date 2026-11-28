# PROJECT_INDEX – claude-4

## Verziók (CHANGELOG alapján)
| verzió | dátum | megjegyzés |
|---|---|---|
| v1.0.0 | (dátum nincs a CHANGELOG-ban) | első kiadás; lassú (~3 s/karakter), valódi gépen lefagyás |
| v1.1.0 | 2026-11-23 | FAST válasz (~0,4 s/karakter), fejléc, óra; FAST alatt fehér kép |
| v1.1.1 | 2026-11-24 | GONDOLKODOM jelzés; FAST alatt sötét kép (a v1.1.2 előtt) |
| v1.1.2 | 2026-11-24 | kijelző mindig be a válasz alatt; SHIFT-F gyors mód |
| v1.1.3 | 2026-11-24 | MARGIN/DF_SZ sysvar javítás |
| v1.1.4 | 2026-11-24 | D-file kitöltetlen cellák (fekete csík javítása) |
| v1.1.5-diag | 2026-11-25 | canary-diagnosztika (CK jel a veremsérülésre) |
| v1.1.6-diag | 2026-11-25 | RTLOAD betöltő (adatbekérés, védett mentés), Y/N témakérdés; munkaverzió |

## Főbb fájlok
- `src/app1.asm` – BOOT, billentyűzet-táblák, GETKEY.
- `src/app3.asm` – védett állapot ($7F00), ST_SAVE / ST_LOAD.
- `src/app4.asm` – TITLE, SETUP, ASK_MANUAL.
- `src/app5.asm` – READ_LINE, HANDLE, APP, LOADER (v1.1.6-diag), HK_TOP Y/N.
- `src/app7.asm` – óra, fejléc, inverz csevegő-fejlécek.
- `src/engine.asm` – az előrehaladási lépés (FORWARD, GEN_STEP).
- `tools/make_dist.py` – minden .P és .t81 kimenet.

## Fájlok listája
Teljes lista és hash: `MIGRATION_MANIFEST.md`.

## Átnevezés (2026-11-28)
- Modellnév: **Cricket-81** (Claude-4). A fájlnevekben: `Cricket81_Claude-4`.
- Fájlnév-minta: `<FÁJL>_v<verzió>_Cricket81_Claude-4.<kiterjesztés>`, pl. `RTCHAT_v1.1.6-diag_Cricket81_Claude-4.P`.
- A kép címsora: `CRICKET-81  V1.1.6`.
- A régi `..._Claude_Haiku_5.5` fájlok a `dist/` mappában történeti példányok, nem törölve.
