# glm-3 — ZX81 Pico AI (GLM / z.ai, 3. példány)

A ZX81 (16 KB) „Pico AI" mikro-nyelvi modell fejlesztése, multi-load .T81
kazettával. Ez a `glm/zx-81/` alatti **glm-3 példány** munkaterülete a
`micro-ai-models-for-retro-computers` központi repóban (2026-11-27-től;
forrás: `ZX81-AI-micro-language-model/GLM3` @ `aefdee3`).

## Példány-rendszer — így dolgozhat 3 GLM modell ütközés nélkül egy fában

A gépkönyvtár (`glm/zx-81/`) alatt minden modellpéldány SAJÁT `glm-<N>/`
könyvtárban dolgozik; a példányok között nincs közös, több kéz által
szerkeszthető fájl — ez az ütközésmentesség alapja:

| Példány | Vonala | Eredeti forrás | Állapot |
|---|---|---|---|
| `glm-1` | v0.1–v0.4 (C-motor korszak) | `ZX81-AI-micro-language-model` gyökér `GLM/` (archív, `TÖRÖLHETŐ.TXT`) | a saját példánya költöztesse át → `glm/zx-81/glm-1/` |
| `glm-2` | v0.5.x | `retro-tinyllm` repó GLM-vonala | a saját példánya költöztesse át → `glm/zx-81/glm-2/` |
| `glm-3` | v0.6.5 újrakiadás → v0.9.2 (ez) | `ZX81-AI-micro-language-model/GLM3` @ `aefdee3` | **ÁTKÖLTÖZTETVE** (lásd `MIGRATION_MANIFEST.md`) |

Ez a példány kizárólag a `glm/zx-81/glm-3/` fájljait módosítja; más példány
vagy más modell munkájára csak pontos útvonallal és verzióval hivatkozunk.
Megjegyzés: a git üres könyvtárat nem tárol, ezért a 28 gépkönyvtár közül csak
azok látszanak, amelyekben már van fájl — a többi az első valódi fájl
közzétételekor jön létre.

## Könyvtárszerkezet

| Elem | Tartalom |
|---|---|
| `ERROR_AND_REPAIR_LOG.md` | Minden verzió: élő EO-próba eredménye, gyökérok, javítás, MD5 — a re-vizsgálat kiindulópontja is (átnevezve a korábbi `HIBA_ES_JAVITAS_TORTENET.md`-ből) |
| `BREAKPOINT.md` | Hol tart a fejlesztés, mi a következő lépés, előírt alapfájl (v0.6.5) |
| `MIGRATION_MANIFEST.md` / `MIGRATION_STATUS.md` | Honnan és mit költöztettünk; a költöztetés ellenőrzött állapota |
| `allapot/` | `STATE.md` (1–15. menet), `STATE_v0.7.1_backup.md`, `PROJECTLOG.md` |
| `kazettak/` | Minden megőrzött .T81 (v0.6.5 → v0.9.2), `MD5SUMS.txt`, `elozmenyek_v0.7.0_elott/` |
| `dokumentacio/` | Verziósways dokumentációk + változásnaplók (txt/docx/pdf) |
| `forraskod_csomagok/` | Verziósways forráscsomag .zip-ek |
| `szkriptek/` | Építő/ellenőrző/diagnosztika készlet (`build_v092.py`, `verify_*`, `diff_cassets.py`, `trap_disasm.py`, …) |
| `motor_v090/` | A v0.9.0 C-motor forrása (z88dk/zsdcc vonal) |
| `eszkozok_regi_repo/` | A v0.1-dev repo eszközei (asm.py, build_t81.py, zx81sim.py, t81_validate.py, kbtrain.py) node_modules és .git nélkül |
| `refs/` | Hiteles ZX81 ROM (8K) + disassembly referenciák |
| `toolchain/` | `GLM_z88dk_2.5_zx81_toolchain.tar.gz` (z88dk 2.5 + SDCC 4.2, zx81 clib) |
| `TELJES_LELTAR.txt` / `SHA256SUMS.txt` | Teljes fájlleltár méret+MD5, ill. SHA-256 |

## Aktuális állapot (2026-11-27)

- Legfrissebb kazetta: **`kazettak/GLM_PicoAI_v0.9.2_kazetta.T81`** (227 923 B,
  15 blokk, MD5 `6f5fc138e66e2ccdd52b982fffdb9003`). Élő EO-próbája függőben
  (A: profilkérdés; B: RTBASE16-lánc; C: /quit — lásd `BREAKPOINT.md`).
- **A re-vizsgálat előírt kiinduló fájlja: v0.6.5** — ettől a verziótól maradt
  a tünet változatlan a javítások ellenére (bizonyítéklánc:
  `ERROR_AND_REPAIR_LOG.md` 2. fejezet).
- Kulcstény: az RTBASE16 lánc-betöltési lépés élőben (EightyOne-ban) **soha nem
  ment el hibátlanul** — az összes eddigi javítás ezt az utat célozza.
- Régi munkahely: `ZX81-AI-micro-language-model/GLM3` — történeti példány
  (`ATKÖLTÖZTETVE.md` jelzéssel), semmi nem törlődött.
- A retro-tinyllm repó CI-hibája (`PICO_BOOT_R5.p: line1 is not REM`) a
  ChatGPT-vonal R5-builderének ügye — ebből a könyvtárból nem javítható.

## Újraépítés (v0.9.2)

```bash
tar xzf toolchain/GLM_z88dk_2.5_zx81_toolchain.tar.gz   # z88dk + zsdcc
python3 szkriptek/build_v092.py                          # kazetta-építés + verifikáció
```

Megjegyzés: a szkriptek a fejlesztő-sandbox abszolút útvonalaira íródtak
(`/home/z/my-project/...`); más környezetben futtatáskor az útvonal-konstansokat
a szkript fejlécében módosítani kell.
