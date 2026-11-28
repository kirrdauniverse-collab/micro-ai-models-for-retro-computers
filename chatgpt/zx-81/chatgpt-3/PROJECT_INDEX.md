# ChatGPT 3 — project index

## Required workspace documents
- `README.md` — PICO AI workspace identity and boundaries.
- `BASELINE.md` — selected CleanDisplay baseline, PICO AI v0.1.0 filename and exact hashes.
- `VERSIONING.md` — official PICO AI name, filename scheme, semantic versioning and boot-screen requirements.
- `MIGRATION_MANIFEST.md` — exact source paths, SHA values, identified artifacts and exclusions.
- `MIGRATION_STATUS.md` — completed and blocked migration steps.
- `PROJECT_INDEX.md` — this index.
- `ERROR_AND_REPAIR_LOG.md` — known issues and repair history.
- `BREAKPOINT.md` — technical handoff and next actions.

## Selected binary baseline
The selected CleanDisplay bytes have version-labelled local copies:
- `PICO_AI_ZX81_16K_v0.1.0.t81` — 225,941 B, SHA-256 `6d2025bd66435ed51540efeb7e098292926a0f8b2ce9a489103a2fe3d33faea5`.
- `PICO_AI_ZX81_16K_v0.1.0_build.zip` — 36,049 B, SHA-256 `69433d00ac07a9c116fc9ddb8878666f5025d29dded0b5d023f65fb9c2a58234`.
- Both are byte-identical copies under new filenames; binary contents were not changed.
- The binaries are held locally and are not yet committed to this GitHub branch. Full details are in `BASELINE.md`.

## Legacy ChatGPT materials copied
All files came from `kirrdauniverse-collab/PIOCO-AI-miniature-language-modell/CHATGPT/`:
- `legacy-chatgpt/ATVETELI_TESZTEK.md`
- `legacy-chatgpt/FEJLESZTESI_UTITERV.md`
- `legacy-chatgpt/FELTOLTOTT_KEZDEMENYEK_AUDIT_2026-11-23.md`
- `legacy-chatgpt/MODELLEKNEK.md`
- `legacy-chatgpt/MUSZAKI_AUDIT_2026-11-22.md`
- `legacy-chatgpt/README.md`
- `legacy-chatgpt/host_reference_chat.py`

## Shared source project
The historical PIOCO/TinyLLM source lineage remains in the legacy repository. This migration deliberately does not duplicate or modify that shared tree. The central repository's existing `pico-ai/` area and ChatGPT-1 payload are also untouched.
