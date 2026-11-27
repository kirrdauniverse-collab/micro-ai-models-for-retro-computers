# MIGRATION STATUS — glm-3 (zx-81)

Állapot: **TELJES a GLM-3 saját anyagaira** (2026-11-27)

| Tétel | Állapot |
|---|---|
| Forrás leltár (méret + MD5) | ✓ `TELJES_LELTAR.txt`, `kazettak/MD5SUMS.txt` |
| Másolás | ✓ 192 fájl, 30 548 341 bájt (binárisan, eredeti nevekkel) |
| SHA-256 fájlankénti egyezés (forrás vs. cél) | ✓ 192/192, eltérés: 0 |
| Átnevezés | ✓ 1 db: `HIBA_ES_JAVITAS_TORTENET.md` → `ERROR_AND_REPAIR_LOG.md` |
| Régi hely jelzése | ✓ `ZX81-AI-micro-language-model/GLM3/ATKÖLTÖZTETVE.md` @ `aefdee3` (push: `5b6b2c2..aefdee3`) |
| Törlés a régi helyen | — nem történt; történeti példány megmarad |
| Más példányok (glm-1, glm-2) | nem az én feladatom — a saját példányaik költöztetendők (README példány-táblázat) |
| Más modellek / más gépkönyvtárak | érintetlenül hagyva (chatgpt/, mistral/, grok/ stb. nem módosítva) |

## Ismert hiányosságok a leltárban (őszintén rögzítve)

- A **v0.5.4** és a **v0.9.0 / v0.9.1** kazetták nincsenek meg ebben a
  munkaterületben: a v0.5.4 a retro-tinyllm (GLM-2) vonal terméke volt; a
  v0.9.0 kazettáját a későbbi kézbesítés kiváltotta, a v0.9.1-et pedig a
  hibás RTMEM16-blokk miatt töröltük a kézbesítésből (rekonstruálható a
  v0.9.2-ből — lásd `ERROR_AND_REPAIR_LOG.md`). A v0.7.0 előtti névtelen
  kiadások megvannak (`kazettak/elozmenyek_v0.7.0_elott/`).
- A v0.4.5 (utolsó felhasználó által megerősített működő) csak .P-korszakbeli
  volt (`rt16_base.p`), .T81 példánya nem maradt meg.

## Következő lépés a költöztetés után

Fejlesztés a központi repóban, új verziószámmal; az előírt re-vizsgálati
kiindulópont: `kazettak/GLM_PicoAI_v0.6.5_kazetta.T81` (lásd `BREAKPOINT.md`).
