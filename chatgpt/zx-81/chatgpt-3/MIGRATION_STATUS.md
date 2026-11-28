# ChatGPT 3 — migration status

## Status: PARTIAL — PICO AI baseline selected, binary transfer to GitHub remains outstanding

### Completed
- Assigned this independent workspace as `chatgpt-3`; `chatgpt-1` already exists and `chatgpt-2` is reserved.
- Copied all seven UTF-8 files from the legacy `CHATGPT/` directory into `legacy-chatgpt/`.
- Created the required workspace documentation.
- Compared all seven destination Git blob IDs with their original source blob IDs; all seven match exactly (see `MIGRATION_MANIFEST.md`).
- Isolated all changes on branch `migration/chatgpt-3-pio-co-ai-zx81`; `main` and all other model workspaces are untouched.
- Selected the CleanDisplay build as the official ChatGPT-3 baseline; exact T81 and ZIP-inner-T81 SHA-256 identity is verified locally. See `BASELINE.md`.
- Adopted **PICO AI** as the official product name for new work.
- Adopted the versioned filename convention `PICO_AI_ZX81_16K_vMAJOR.MINOR.PATCH`.
- Created local, byte-identical version-labelled copies `PICO_AI_ZX81_16K_v0.1.0.t81` and `PICO_AI_ZX81_16K_v0.1.0_build.zip`.

### Baseline artifacts — local, not yet committed to this GitHub branch
- `PICO_AI_ZX81_16K_v0.1.0.t81` — 225,941 B; SHA-256 `6d2025bd66435ed51540efeb7e098292926a0f8b2ce9a489103a2fe3d33faea5`.
- `PICO_AI_ZX81_16K_v0.1.0_build.zip` — 36,049 B; SHA-256 `69433d00ac07a9c116fc9ddb8878666f5025d29dded0b5d023f65fb9c2a58234`.
- The archive's internal T81 is byte-identical to the selected CleanDisplay file.
- The ZIP also contains `rboot16.P/.bin` and `rtchat16.P/.bin`; individual SHA-256 values are recorded in `BASELINE.md`.

### Boot-screen naming outstanding
The current binary still contains historical internal strings `PIOCO AI PROFILE OK` and `tinyllm v0.5.4`. Its current boot/runtime binaries have no corresponding editable source or complete build recipe in the companion ZIP. They have not been patched. The next rebuild must display `PICO AI ZX81` and the matching version number, generated from one shared build version constant.

### Not completed
- The baseline T81 and ZIP have not been transferred into GitHub.
- The GitHub content-write path used for text documents does not directly consume local binary files. The local copies are preserved; no false binary-migration claim is made.
- A full source-to-binary reproducible build for CleanDisplay is not established by the companion ZIP alone.

### Required to finish
Add the exact baseline T81 and its companion build archive to `chatgpt/zx-81/chatgpt-3/artifacts/` through a byte-preserving Git upload route. Verify committed bytes against the SHA-256 values in `BASELINE.md`.

### Test status
The baseline selection and byte-level identity checks have been performed. No fresh emulator or real-hardware test is claimed by this migration update.
