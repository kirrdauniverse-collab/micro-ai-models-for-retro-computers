# ChatGPT 3 — migration manifest

## Destination
`chatgpt/zx-81/chatgpt-3/` in `kirrdauniverse-collab/micro-ai-models-for-retro-computers`, branch `migration/chatgpt-3-pio-co-ai-zx81`.

## Official new-work name
**PICO AI**

New ChatGPT-3 work uses the versioned pattern `PICO_AI_ZX81_16K_vMAJOR.MINOR.PATCH`. Historical PIOCO/TinyLLM source documents and binary strings remain preserved as legacy evidence; they are not silently rewritten. See `VERSIONING.md`.

## Source workspace
- Repository: `kirrdauniverse-collab/PIOCO-AI-miniature-language-modell`
- Source directory: `CHATGPT/`
- Only the ChatGPT-owned directory was copied. The source repository root, shared source, GLM/Grok material and all other model paths were left untouched.

## Copied legacy files
Seven UTF-8 files were copied under `legacy-chatgpt/`. Their source blob SHAs are recorded below; destination blob IDs will be reconciled in the migration verification step.

| Source path | Source blob SHA | Destination path |
|---|---|---|
| `CHATGPT/ATVETELI_TESZTEK.md` | `24bc92c0d1cc81f2954c7c4396bb7aac091b3151` | `legacy-chatgpt/ATVETELI_TESZTEK.md` |
| `CHATGPT/FEJLESZTESI_UTITERV.md` | `1fa5fabcaec2cd7c91cebfb20d91d3a281a28818` | `legacy-chatgpt/FEJLESZTESI_UTITERV.md` |
| `CHATGPT/FELTOLTOTT_KEZDEMENYEK_AUDIT_2026-11-23.md` | `801d3e159d1f555a1a61660bb70bc581d2d8b85b` | `legacy-chatgpt/FELTOLTOTT_KEZDEMENYEK_AUDIT_2026-11-23.md` |
| `CHATGPT/MODELLEKNEK.md` | `6b2d922de1aa87c729df15b68adfaad8ea0e7601` | `legacy-chatgpt/MODELLEKNEK.md` |
| `CHATGPT/MUSZAKI_AUDIT_2026-11-22.md` | `401a97142380d0cc4cd6af7dc2cfd775c6f3393f` | `legacy-chatgpt/MUSZAKI_AUDIT_2026-11-22.md` |
| `CHATGPT/README.md` | `4812fe3de20405ff2440137200855e1ab84bd0a0` | `legacy-chatgpt/README.md` |
| `CHATGPT/host_reference_chat.py` | `3bb1da645963e7edae69c3e327055f6849a821c9` | `legacy-chatgpt/host_reference_chat.py` |

## Selected CleanDisplay baseline — verified locally, not committed to GitHub
- Original file: `PIOCO_AI_English_16K_CleanDisplay.t81`
- Official version-labelled local copy: `PICO_AI_ZX81_16K_v0.1.0.t81`
- Size: 225,941 bytes
- SHA-256: `6d2025bd66435ed51540efeb7e098292926a0f8b2ce9a489103a2fe3d33faea5`
- The version-labelled T81 is a byte-for-byte copy; only its filename changed.

### Companion build archive
- Original: `PIOCO_AI_English_16K_CleanDisplay_artifact.zip`
- Version-labelled local copy: `PICO_AI_ZX81_16K_v0.1.0_build.zip`
- Archive size: 36,049 bytes
- Archive SHA-256: `69433d00ac07a9c116fc9ddb8878666f5025d29dded0b5d023f65fb9c2a58234`
- Its internal `ports/zx81/pio16_release/PIOCO_AI_English_16K_ROM_INPUT.t81` is 225,941 bytes and has the same SHA-256 as the selected CleanDisplay T81; the two are byte-identical despite different filenames.
- The archive also contains `rboot16.P/.bin` and `rtchat16.P/.bin`; individual hashes are in `BASELINE.md`.
- The archive does not contain a complete source tree or full reproducible build recipe. The identity of the packaged T81 is established; full source-to-binary reproducibility is not.

### Internal historical strings
The baseline binaries retain older internal strings `PIOCO AI PROFILE OK` and `tinyllm v0.5.4`. No machine-code patch was made. The next rebuild must put `PICO AI ZX81` and the matching version number into the boot screen through the source/build process.

## Other binary files identified but NOT migrated
- `PIOCO_AI_English_16K_IYBootstrap_Final2_artifact(1).zip` — 35,961 bytes; SHA-256 `15f33b7c545a30edb58211710f47a295eabad94c034c764326de555726ee9729`. This is a separate build, not the selected baseline.
- Its internal `PIOCO_AI_English_16K_ROM_INPUT.t81` is 225,115 bytes and differs from the selected 225,941-byte CleanDisplay tape. Do not mix the two.
- A local continuity archive was prepared at `/mnt/data/PICOAI_ChatGPT3_Continuity_Bundle.zip` (47,179 bytes; SHA-256 `e4bfcb74d0b9c1b81da9e70100563ba0324ba5efa55e708c7a12a0c13f4a4eeb`). It contains the two originally uploaded files unchanged, but is not committed to this GitHub branch.

## Explicitly not migrated
- `EightyOne_V141.zip` is an emulator distribution / test tool, not a ChatGPT-authored PICO AI deliverable. It remains with the user.
- No source-repository files were deleted, renamed or modified.
- No files from `chatgpt-1`, `chatgpt-2`, GLM, Grok or other model workspaces were copied or changed.

## Destination verification
Each copied file was fetched from the destination branch and its Git blob SHA compared to the source repository blob SHA. All seven comparisons matched exactly:

| File | Destination blob SHA | Result |
|---|---|---|
| `ATVETELI_TESZTEK.md` | `24bc92c0d1cc81f2954c7c4396bb7aac091b3151` | MATCH |
| `FEJLESZTESI_UTITERV.md` | `1fa5fabcaec2cd7c91cebfb20d91d3a281a28818` | MATCH |
| `FELTOLTOTT_KEZDEMENYEK_AUDIT_2026-11-23.md` | `801d3e159d1f555a1a61660bb70bc581d2d8b85b` | MATCH |
| `MODELLEKNEK.md` | `6b2d922de1aa87c729df15b68adfaad8ea0e7601` | MATCH |
| `MUSZAKI_AUDIT_2026-11-22.md` | `401a97142380d0cc4cd6af7dc2cfd775c6f3393f` | MATCH |
| `README.md` | `4812fe3de20405ff2440137200855e1ab84bd0a0` | MATCH |
| `host_reference_chat.py` | `3bb1da645963e7edae69c3e327055f6849a821c9` | MATCH |

This confirms the copied UTF-8 files are identical Git objects. It does not validate any executable or cassette behavior.
