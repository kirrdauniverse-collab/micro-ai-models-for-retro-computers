# MIGRATION_MANIFEST.md – claude/zx-81/claude-1

## Honnan kerültek ide a fájlok

| Fájl | Forrás | Megjegyzés |
|---|---|---|
| `binaries/t81/ZXAI_v3..v9_*.t81` | Claude Sonnet 4.6 munkamenet, 2026-11 | 9 kazettaverziót patcheltem bináris szinten |
| `binaries/p/ZXAI_v3..v9_*.p` | Claude Sonnet 4.6 munkamenet, 2026-11 | 9 nyers ZX81 képfájl |
| `reference/engine/` | retro-tinyllm v0.4.0-16k, Gemini/GLM build | Az eredeti C-motor forrása, nem módosítva |
| `reference/app16.c` | retro-tinyllm v0.4.0-16k | ZX81 port belépési pont |
| `reference/hal_zx81.c` | retro-tinyllm v0.4.0-16k | Hardware abstraction layer |
| `models/base_f.bin` | retro-tinyllm v0.4.0-16k | Class F RTLM modell, 2666 bájt |
| `tests/golden_base_f.txt` | retro-tinyllm v0.4.0-16k | Referencia tesztvektorok |
| `tools/verify_findings.py` | Claude Sonnet 4.6 | ROM és modell ellenőrző szkript |
| `docs/B2_checksum_length.md` | Claude Sonnet 4.6 | B2 hiba és javítás leírása |
| `docs/B3_line2.md` | Claude Sonnet 4.6 | B3 hiba és javítás leírása |

## Átvétel dátuma
2026-11-25

## Eredeti munkaterület
Claude.ai csevegés (Sáfár Sándor, kirrdauniverse-collab tulajdonos)
