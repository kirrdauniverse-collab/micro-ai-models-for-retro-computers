# ChatGPT 3 — migration status

## Status: PARTIAL — baseline selected, binary transfer to GitHub remains outstanding

### Completed
- Assigned this independent workspace as `chatgpt-3`; `chatgpt-1` already exists and `chatgpt-2` is reserved.
- Copied all seven UTF-8 files from the legacy `CHATGPT/` directory into `legacy-chatgpt/`.
- Created the required workspace documentation.
- Compared all seven destination Git blob IDs with their original source blob IDs; all seven match exactly (see `MIGRATION_MANIFEST.md`).
- Isolated all changes on branch `migration/chatgpt-3-pio-co-ai-zx81`; `main` and all other model workspaces are untouched.
- Selected the CleanDisplay build as the official ChatGPT-3 baseline; exact T81 and ZIP-inner-T81 SHA-256 identity is verified locally. See `BASELINE.md`.

### Baseline artifacts — local, not yet committed to this GitHub branch
- `PIOCO_AI_English_16K_CleanDisplay.t81` — 225,941 B; SHA-256 `6d2025bd66435ed51540efeb7e098292926a0f8b2ce9a489103a2fe3d33faea5`.
- `PIOCO_AI_English_16K_CleanDisplay_artifact.zip` — 36,049 B; SHA-256 `69433d00ac07a9c116fc9ddb8878666f5025d29dded0b5d023f65fb9c2a58234`.
- The archive's `ports/zx81/pio16_release/PIOCO_AI_English_16K_ROM_INPUT.t81` is byte-identical to the selected CleanDisplay T81.
- The ZIP also contains `rboot16.P/.bin` and `rtchat16.P/.bin`; their individual SHA-256 values are recorded in `BASELINE.md`.

### Not completed
- The baseline T81 and ZIP have not been transferred into GitHub.
- The GitHub content-write path used for text documents does not directly consume local binary files. The local copies are preserved; no false binary-migration claim is made.
- A full source-to-binary reproducible build for CleanDisplay is not established by the companion ZIP alone.

### Required to finish
Add the exact baseline T81 and its companion build archive to `chatgpt/zx-81/chatgpt-3/artifacts/` through a byte-preserving Git upload route. Verify the committed bytes against the SHA-256 values in `BASELINE.md`.

### Test status
The baseline selection and byte-level identity check have been performed. No fresh emulator or real-hardware test is claimed by this migration update. Historical test claims from prior sessions remain historical until rerun.
