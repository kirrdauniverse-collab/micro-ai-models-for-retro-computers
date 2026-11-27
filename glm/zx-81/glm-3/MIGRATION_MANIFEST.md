# MIGRATION MANIFEST — glm-3 (zx-81)

Dátum: 2026-11-27. Végrehajtó: GLM-3 példány (GLM / z.ai).

## Forrás → cél

- **Forrás repó:** `kirrdauniverse-collab/ZX81-AI-micro-language-model`
- **Forrás könyvtár:** `GLM3/` @ commit `aefdee3` („ATKOLTOZTETVE jelzés a GLM3/ alatt…")
- **Cél:** `glm/zx-81/glm-3/` (ez a könyvtár)
- **Módszer:** bináris fájl-másolás (eredeti fájlnevekkel), majd fájlanként
  méret- és SHA-256-összevetés forrás vs. cél.
- **Eredmény:** 192 fájl, 30 548 341 bájt átmásolva; egyezés: 192/192; eltérés: 0.
- **Ellenőrző listák a célban:** `SHA256SUMS.txt` (a cél teljes állapota),
  `TELJES_LELTAR.txt` (méret + MD5), `kazettak/MD5SUMS.txt` (kazetták).

## Elemenkénti bontás

| Forrás (`GLM3/…`) | Fájlok | Bájt | Megjegyzés |
|---|---:|---:|---|
| `kazettak/` | 21 | 1 337 408 | 7 verziósways .T81 + MD5SUMS.txt + `elozmenyek_v0.7.0_elott/` (14 fájl: ZX81PICO.T81, PICO*.p, korábbi állapotfájlok, bundle) |
| `dokumentacio/` | 15 | 288 770 | verziósways dokumentáció (txt/docx/pdf) + változásnaplók + v0.8.0 áttekintés |
| `forraskod_csomagok/` | 7 | 4 663 464 | v0.6.5 → v0.9.2 forráscsomag .zip-ek |
| `allapot/` | 3 | 68 175 | STATE.md (1–15. menet), STATE_v0.7.1_backup.md, PROJECTLOG.md |
| `szkriptek/` | 36 | 112 838 | build + verify + diagnosztika készlet |
| `motor_v090/` | 58 | 689 190 | C-motor forrás (z88dk/zsdcc vonal) |
| `eszkozok_regi_repo/` | 45 | 622 029 | v0.1-dev repo eszközei; node_modules és .git kizárva |
| `refs/` | 3 | 544 962 | hiteles 8K ZX81 ROM + disassembly |
| `toolchain/` | 1 | 22 194 898 | GLM_z88dk_2.5_zx81_toolchain.tar.gz |
| gyökérfájlok | 4 | — | README.md, ERROR_AND_REPAIR_LOG.md, SHA256SUMS.txt, TELJES_LELTAR.txt |

## Átnevezés (dokumentált, tartalom változatlan)

- `HIBA_ES_JAVITAS_TORTENET.md` → `ERROR_AND_REPAIR_LOG.md` — a központi
  kötelező sablon neve szerint; a tartalom a forrás `aefdee3` példányával
  azonos a fejléc-megjegyzés és a kereszthivatkozások frissítése kivételével.

## Kizárások

- `ATKÖLTÖZTETVE.md` — a régi hely jelzése; ott marad, nem tartozik a
  munkaterület tartalmába.

## Megőrzés

- A forrás repóban semmi nem törlődött vagy módosult a költöztetés során;
  `GLM3/` történeti példányként megmarad (`ATKÖLTÖZTETVE.md` jelzéssel).
- Nem átköltöztetett, más példányhoz tartozó anyagok (tilos azokat áthelyeznem):
  a gyökér `GLM/` (GLM-1 archív) és a `retro-tinyllm` GLM-vonala (GLM-2) —
  ezek a saját példányaik feladatai (lásd `README.md` példány-táblázat).
