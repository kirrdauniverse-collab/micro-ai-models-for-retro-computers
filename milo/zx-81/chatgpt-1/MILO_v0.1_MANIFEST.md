# MILO v0.1 — FILE MANIFEST

| File | Role | Status |
|---|---|---|
| MILO_v0.1_README.md | rövid projektleírás | dokumentáció |
| MILO_v0.1_HANDOFF.md | teljes átadási jegyzőkönyv | elsődleges átadás |
| MILO_v0.1_MANIFEST.md | fájllista | elsődleges leltár |
| MILO_v0.1_ZX81.asm | MILO forrás | auditálandó |
| MILO_v0.1_ZX81_BUILD.py | build/preprocess script | jelenleg régi útvonalakra hivatkozik |
| MILO_v0.1_ZX81.p | ZX81 RAM image | auditálandó |
| MILO_v0.1_ZX81.t81 | ZX81 cassette image | auditálandó |

## Branch

`milo/zx81-v0.1`

## Current head

`27bf808d4b36de1e8cc1211c6cdcabba3681dc44`

## Naming

Minden új MILO artifact:
`MILO_v<major>.<minor>_...`

## Release rule

A v0.1 csak akkor tekinthető elfogadott release-nek, ha:
- a P és T81 hash reprodukálható;
- a build script ugyanazt a binárist állítja elő;
- az egyetlen T81 emulátoros tesztje sikeres;
- lehetőség szerint valódi ZX81/16K RAM-on is ellenőrizve van;
- az eredeti AI16 kontroll és az új MILO állapot közti különbség dokumentált.
