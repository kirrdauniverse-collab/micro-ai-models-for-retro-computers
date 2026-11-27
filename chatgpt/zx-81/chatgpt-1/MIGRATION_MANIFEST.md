# ChatGPT 1 — ZX81 migration manifest

## Scope

This workspace is **ChatGPT 1 only**.

Source repository:
- `kirrdauniverse-collab/ZX81-AI-micro-language-model`

Source workspace:
- `CHATGPT1/`

Destination:
- `kirrdauniverse-collab/micro-ai-models-for-retro-computers/chatgpt/zx-81/chatgpt-1/`

## Safety rules

- The legacy `CHATGPT1/` tree is the historical control and must remain untouched.
- No GLM, GROK, Mistral, or other model material is to be migrated as part of this step.
- `chatgpt-2` remains a separate reserved workspace.
- Binary files must be transferred byte-for-byte; do not convert them through UTF-8 text APIs.
- Every migrated artifact must retain its original path in this manifest and its source Git blob SHA where available.
- Do not delete source files after migration.
- Migration is not considered complete until source and destination inventories can be reconciled.

## Source areas identified

### Control / project documentation
- `CHATGPT1/README.md`
- `CHATGPT1/PROJECT_INDEX.md`
- `CHATGPT1/BREAKPOINT.md`
- `CHATGPT1/ERROR_AND_REPAIR_LOG.md`
- `CHATGPT1/T81_INVENTORY.md`
- `CHATGPT1/.gitignore`

### PICO / Retro TinyLLM working tree
- `CHATGPT1/RETRO_TINYLLM/dist/`
- `CHATGPT1/RETRO_TINYLLM/docs/`
- `CHATGPT1/RETRO_TINYLLM/ports/`
- `CHATGPT1/RETRO_TINYLLM/tests/`
- `CHATGPT1/RETRO_TINYLLM/tools/`

Known control artifacts include:
- `dist/PICO_AI_R3_16K.p` — blob SHA `df926773d7d78dcf0a370c6b95028edbc581c253`
- `dist/PICO_AI_R3_16K.t81` — blob SHA `4277a74636e9bffeb2593e7491f27c43aaabe6af`
- `dist/PICO_AI_R4_16K.p` — blob SHA `011dbc9f0ef29701b190340f19ce97842a10d69b`
- `dist/PICO_AI_R4_16K.t81` — blob SHA `b6169bb37b9697a80b65b3d8ae5652bb96b10516`
- `tests/PICO_V1_8_RAMTEST.T81` — blob SHA `d18401ef480464ab448dbb764a1892df1f5b3179`

### Other model-owned material in the legacy workspace

The legacy `CHATGPT1/GLM/` and `CHATGPT1/GROK1/` directories are **not part of this migration**. They are explicitly excluded and must not be copied, renamed, edited, or deleted.

## Current migration state

**PREPARATION ONLY**

The destination workspace structure exists, but the actual ChatGPT 1 source tree has not yet been fully copied.

The GitHub connector can transfer UTF-8 text safely. It cannot safely decode arbitrary binary repository blobs as UTF-8. Therefore `.T81`, `.P`, and other binary artifacts require a byte-preserving transfer route before they can be marked migrated.

## Next migration phases

1. Inventory every file below `CHATGPT1/RETRO_TINYLLM/`.
2. Separate text/source files from binary artifacts.
3. Copy text/source/documentation into the destination.
4. Transfer binary artifacts byte-for-byte using a binary-capable route.
5. Produce destination inventory with source path, destination path, size, and hash.
6. Reconcile inventories.
7. Only then declare ChatGPT 1 migration complete.

