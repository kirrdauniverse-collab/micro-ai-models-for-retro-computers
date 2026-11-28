# ChatGPT 3 — project index

## Required workspace documents
- `README.md` — workspace identity and boundaries.
- `BASELINE.md` — selected CleanDisplay baseline, exact hashes and verification limits.
- `MIGRATION_MANIFEST.md` — exact source paths, SHA values, identified artifacts and exclusions.
- `MIGRATION_STATUS.md` — completed and blocked migration steps.
- `PROJECT_INDEX.md` — this index.
- `ERROR_AND_REPAIR_LOG.md` — known issues and repair history.
- `BREAKPOINT.md` — technical handoff and next actions.

## Selected binary baseline
- `PIOCO_AI_English_16K_CleanDisplay.t81` — 225,941 B, SHA-256 `6d2025bd66435ed51540efeb7e098292926a0f8b2ce9a489103a2fe3d33faea5`.
- Companion archive: `PIOCO_AI_English_16K_CleanDisplay_artifact.zip` — local, not committed to this branch.
- Full metadata, inner archive identity and limitations: `BASELINE.md`.

## Legacy ChatGPT materials copied
All files came from `kirrdauniverse-collab/PIOCO-AI-miniature-language-modell/CHATGPT/`:
- `legacy-chatgpt/ATVETELI_TESZTEK.md`
- `legacy-chatgpt/FEJLESZTESI_UTITERV.md`
- `legacy-chatgpt/FELTOLTOTT_KEZDEMENYEK_AUDIT_2026-11-23.md`
- `legacy-chatgpt/MODELLEKNEK.md`
- `legacy-chatgpt/MUSZAKI_AUDIT_2026-11-22.md`
- `legacy-chatgpt/README.md`
- `legacy-chatgpt/host_reference_chat.py`

## Binary migration status
The selected T81 and its companion build archive are verified locally but have not yet been committed into this GitHub workspace. The earlier IYBootstrap archive is a different build and is not the selected baseline. See `MIGRATION_STATUS.md`.

## Shared source project
The PIOCO AI source, firmware, data, build tools and cassette contents remain in the legacy source repository. This migration deliberately does not duplicate or modify that shared tree. The central repository's existing `pico-ai/` area and ChatGPT-1 payload are also untouched.
