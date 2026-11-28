# MILO v0.2 manifest

Model: MILO — Micro Intelligent Language Organism
Workstream: ChatGPT-1
Target: Sinclair ZX81, 16K RAM
Branch: milo/zx81-v0.2

Base runtime: MILO v0.1 / historical AI16 control image
Engine origin: $4082
D_FILE: $7908
Knowledge blob base: $5918

New runtime features:
- /time HH MM
- /remind N
- expanded topic catalogue
- knowledge and games packs
- short-story variants
- Safar Sándor / Mistral / KIRRDA identity content
- clearer unknown-topic handling

Known limitation:
Interactive chess, multi-player quiz and full adventure state are seeded but not yet complete state machines.