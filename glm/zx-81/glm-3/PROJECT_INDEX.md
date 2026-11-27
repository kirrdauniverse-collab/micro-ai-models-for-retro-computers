# PROJECT INDEX — glm-3 (zx-81)

Teljes fájlleltár méret+MD5: `TELJES_LELTAR.txt` · SHA-256: `SHA256SUMS.txt` ·
kazetta-MD5-kártya: `kazettak/MD5SUMS.txt`

## Kazetták (.T81) — megőrzött verziók

| Verzió | Fájl | Méret (B) | MD5 | Élő EO-próba eredménye | Állapot |
|---|---|---:|---|---|---|
| v0.6.5 | `kazettak/GLM_PicoAI_v0.6.5_kazetta.T81` | 227 923 | `1162414c907f7a0b13c5cc2b4999c0de` | betöltés+profil OK; RTBASE16 után grafikus karakterek, fehér kép, PC=$004x | **a re-vizsgálat alapfájlja** |
| v0.7.1 | `kazettak/GLM_PicoAI_v0.7.1_kazetta.T81` | 39 009 | `160b23b5c258b428bd37d021cbc96f3d` | „4/2" OUT OF RAM | archív (assembly-vonal) |
| v0.7.2 | `kazettak/GLM_PicoAI_v0.7.2_kazetta.T81` | 38 433 | `8f7025f1a6fd25b7e2ddc326a0df20e9` | ismét „4/2" | archív |
| v0.7.3 | `kazettak/GLM_PicoAI_v0.7.3_kazetta.T81` | 38 433 | `fae288550aa51884df6560f7c260ef8b` | **VISSZAVONVA** — hibás tokenek (FOR/PLOT) | archív, használatra alkalmatlan |
| v0.8.0 | `kazettak/GLM_PicoAI_v0.8.0_kazetta.T81` | 227 923 | `d7f154b6130871c801c05a896ce71d18` | „Semmi se változott, ugyanaz a hiba" (PC=$004x) | archív |
| v0.8.1 | `kazettak/GLM_PicoAI_v0.8.1_kazetta.T81` | 227 923 | `abbf634478e97f7c0b44ebfd852c6a5b` | önmagában nem tesztelve | archív (OUT(FE)-hiba) |
| v0.9.2 | `kazettak/GLM_PicoAI_v0.9.2_kazetta.T81` | 227 923 | `6f5fc138e66e2ccdd52b982fffdb9003` | függőben (A/B/C) | **legfrissebb, tesztelendő** |

## Előzmények (v0.7.0 előtt)

`kazettak/elozmenyek_v0.7.0_elott/` — `ZX81PICO.T81` (v0.7.0, fehér képernyős
hiba), `PICOBASE.p` / `PICOASTR.p` / `PICOSCIN.p`, korábbi állapot- és
naplófájlok, `zx81-ai-micro-language-modell.bundle`.

## Dokumentáció és naplók (`dokumentacio/`, 15 fájl)

Verziósways dokumentációk (txt / docx / pdf) + változásnaplók + a
`GLM_PicoAI_v0.8.0_valtozas_attekintes.txt` (a változatok áttekintése és a
helyes ZX81 token-tábla).

## Állapotnaplók (`allapot/`)

`STATE.md` (1–15. menet: a teljes hibakeresési és javítási történet + következő
menet teendői), `STATE_v0.7.1_backup.md`, `PROJECTLOG.md`.

## Forráscsomagok (`forraskod_csomagok/`, 7 zip)

v0.6.5 → v0.9.2: motor + builder + ellenőrző szkriptek az adott verzió
állapotában.

## Szkriptek (`szkriptek/`, 36 fájl)

Építés: `build_v092.py`, `build_v090.sh`, `build_v090_sdcc.sh`, `patch_v080.py`,
`patch_v081.py`, `package_v081.py`. Ellenőrzés: `verify_v081.py`,
`verify_v090.py`, `tape_blocks_report.py`, `basic_tokens_report.py`,
`diff_cassets.py`, `trap_disasm.py`, `z80dis.py`, `rom_cdf.py`,
`rom_regions.py`. Diagnosztika: `romsim_*`, `diag_*`, `keymap_probe.py`,
`load_diag*.py`, `flow_measure.py` stb.

## Motor, eszközök, referenciák, toolchain

- `motor_v090/` — a v0.9.0 C-motor forrása (z88dk/zsdcc vonal).
- `eszkozok_regi_repo/` — `asm.py`, `build_t81.py`, `zx81sim.py`,
  `t81_validate.py`, `kbtrain.py` + dist/docs/data/tests (node_modules és
  .git nélkül).
- `refs/` — hiteles 8K ZX81 ROM + disassembly referenciák.
- `toolchain/` — `GLM_z88dk_2.5_zx81_toolchain.tar.gz` (z88dk 2.5 + SDCC 4.2,
  zx81 clib); építés: `szkriptek/build_v092.py` (lásd README „Újraépítés").

## Tesztállapot összefoglaló

Bizonyítottan működő: v0.4.5 (felhasználó által megerősített; .P-korszak,
nem maradt meg). Kísérleti / függőben: minden v0.6.5 utáni változat; az
RTBASE16 lánc-lépés élőben soha nem ment el. Részletek:
`ERROR_AND_REPAIR_LOG.md`, `BREAKPOINT.md`.
