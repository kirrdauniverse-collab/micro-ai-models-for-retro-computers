# ChatGPT 1 — ZX81 migration status

## Status: TERRAIN PREPARED

The new model-first repository is ready for ChatGPT 1:

`chatgpt/zx-81/chatgpt-1/`

### Completed

- New repository created and structured.
- ChatGPT 1 workspace reserved as the primary ZX81 workspace.
- ChatGPT 2 workspace reserved separately.
- Migration rules documented.
- Legacy ChatGPT 1 workspace identified.
- GLM and GROK material explicitly excluded from this migration.
- Historical control artifacts and known-good hashes recorded.
- Binary-transfer limitation identified before copying any binary data.

### Not yet completed

- Full source-tree copy.
- Binary `.T81` / `.P` transfer.
- Final source/destination inventory reconciliation.
- Migration completion marker.

### Important

The legacy repository remains the authoritative historical control until reconciliation is complete. Nothing is to be deleted from it as part of this preparation.

## Workspace ownership

| Workspace | Owner | Status |
|---|---|---|
| `chatgpt/zx-81/chatgpt-1/` | ChatGPT 1 | Active migration target |
| `chatgpt/zx-81/chatgpt-2/` | ChatGPT 2 | Reserved |
| `glm/zx-81/` | GLM | Not touched |
| `grok/zx-81/` | Grok | Not touched |
| `mistral/zx-81/` | Mistral | Not touched |
