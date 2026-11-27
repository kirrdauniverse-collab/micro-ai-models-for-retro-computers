# ChatGPT 1 — ZX81 migration status

## Status: MIGRATED

The ChatGPT 1 ZX81 PICO AI project artifacts have been copied into the new model-first repository.

Destination workspace:

`chatgpt/zx-81/chatgpt-1/`

Project payload:

`pico-ai/`

Migration commit:

`9867e5fd28f5a8a6856fd7ced0ce44d99f632151`

### Migrated

- ChatGPT 1 project documentation and historical control notes.
- PICO / Retro TinyLLM build outputs.
- ZX81 assembly sources.
- R5 modular sources.
- AI16 source and control artifacts.
- T81 and P files.
- Test artifacts.
- Build and validation tools.

The transferred Git blobs retain the same SHA values as the source repository, providing a byte/content identity check for the migrated artifacts.

### Explicitly excluded

- GLM material.
- GROK material.
- Mistral-owned work outside the ChatGPT 1 project payload.
- ChatGPT 2 workspace.

### Legacy policy

The original `CHATGPT1/` workspace in `ZX81-AI-micro-language-model` remains untouched and is retained as the historical control copy.

Nothing was deleted from the source repository.

### Next step

Future ChatGPT 1 development should take place in this new workspace. The legacy copy should be treated as a read-only forensic reference unless a deliberate archival change is required.
