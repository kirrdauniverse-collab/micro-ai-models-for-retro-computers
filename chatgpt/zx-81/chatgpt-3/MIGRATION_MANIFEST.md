# ChatGPT 3 — migration manifest

## Destination
`chatgpt/zx-81/chatgpt-3/` in `kirrdauniverse-collab/micro-ai-models-for-retro-computers`, branch `migration/chatgpt-3-pio-co-ai-zx81`.

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

## Binary files identified but NOT migrated
- `PIOCO_AI_English_16K_CleanDisplay(1).t81` — 225,941 bytes; SHA-256 `6d2025bd66435ed51540efeb7e098292926a0f8b2ce9a489103a2fe3d33faea5`.
- `PIOCO_AI_English_16K_IYBootstrap_Final2_artifact(1).zip` — 35,961 bytes; SHA-256 `15f33b7c545a30edb58211710f47a295eabad94c034c764326de555726ee9729`.

The ZIP contains a distinct `PIOCO_AI_English_16K_ROM_INPUT.t81` (225,115 bytes) plus build outputs. It is not assumed byte-identical to the separately supplied CleanDisplay tape.

A local continuity archive was prepared at `/mnt/data/PICOAI_ChatGPT3_Continuity_Bundle.zip` (47,179 bytes; SHA-256 `e4bfcb74d0b9c1b81da9e70100563ba0324ba5efa55e708c7a12a0c13f4a4eeb`). It contains the two uploaded files unchanged, but is **not committed to this GitHub branch** because the available GitHub write action has no direct local-binary upload input. No text conversion or false byte-preservation claim is being made.

## Explicitly not migrated
- `EightyOne_V141.zip` is an emulator distribution / test tool, not a ChatGPT-authored PICO AI deliverable. It remains with the user.
- No source-repository files were deleted, renamed or modified.
- No files from `chatgpt-1`, `chatgpt-2`, GLM, Grok or other model workspaces were copied or changed.
