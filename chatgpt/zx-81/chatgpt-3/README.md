# ChatGPT 3 — PICO AI / Sinclair ZX81

Independent ChatGPT workspace **3** for **PICO AI** on the Sinclair ZX81 (16 KB, Z80).

- Central repository: `kirrdauniverse-collab/micro-ai-models-for-retro-computers`
- Workspace: `chatgpt/zx-81/chatgpt-3/`
- Historical source repository: `kirrdauniverse-collab/PIOCO-AI-miniature-language-modell/CHATGPT/`
- Platform: `zx-81`

## Official product name and release naming

The official model name for new work in this workspace is **PICO AI**. Older source files and previous binary payloads may still contain historical `PIOCO` or `tinyllm` strings; these are not silently rewritten.

All new outputs use the versioned pattern:

`PICO_AI_ZX81_16K_vMAJOR.MINOR.PATCH.<extension>`

The current selected baseline is labelled `PICO_AI_ZX81_16K_v0.1.0`. The current T81 was copied to that filename without changing its bytes. The next actual rebuild must also show `PICO AI ZX81` and its matching version on the boot screen. See [VERSIONING.md](VERSIONING.md).

## Workspace separation

- `chatgpt-1` already exists as an independent active workspace.
- `chatgpt-2` already exists as an independent reserved workspace.
- This workspace is therefore `chatgpt-3`.
- No other model's folders, files or work were changed or copied.

## Layout

- `legacy-chatgpt/` — original documents and host reference source from the former ChatGPT workspace.
- `BASELINE.md` — selected CleanDisplay baseline and byte identities.
- `VERSIONING.md` — official PICO AI name, filename scheme and boot-screen naming requirements.
- Root status, index, migration, error and breakpoint documents describe this workspace only.

Binary continuity artifacts are inventoried locally but are not yet committed to this GitHub branch; see `MIGRATION_STATUS.md`.
