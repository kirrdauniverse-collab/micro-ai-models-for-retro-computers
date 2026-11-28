# MILO v0.2 — ZX81 16K / ChatGPT-1

MILO v0.2 is the first ChatGPT-1 evolution of the working v0.1 runtime.

## What changed

- Short stories now have multiple variants.
- Added author/lineage identity: MILO was designed around Safar Sándor's plan; the original runtime/model lineage is credited to Mistral.
- Added KIRRDA knowledge.
- Added knowledge topics: health, philosophy, learning, elementary school, secondary school, art, music, astronomy, programming, cars, motorcycles, retro computers and ZX81.
- Added a separate games pack with number guessing, riddles, true/false, chess discussion and a text-adventure seed.
- `/topics` now exposes the larger topic catalogue.
- `/time HH MM` sets MILO's conversational clock.
- `/remind N` schedules a short live reminder (1–5 minutes).
- Header/status labels now identify MILO v2 and the knowledge/game packs.
- Unknown questions now give a clearer response instead of silently steering into an unrelated topic.

## Important scope note

The chess, multi-player true/false and full text-adventure state machines are not yet full game engines in v0.2. They are seeded as topics and interaction starters. The next step is to make those modes stateful.

## Build

The build uses the known-good v0.1 T81/P image as a template for the system-variable/D-FILE area, then replaces the machine-code REM line, the parked knowledge image, and the autostart pointer.

## Files

- `MILO_v0.2_ZX81.asm` — engine source
- `MILO_v0.2_ZX81_KB.py` — compact knowledge/game banks
- `MILO_v0.2_ZX81_BUILD.py` — reproducible builder
- `MILO_v0.2_ZX81.t81` — generated one-file cassette image
- `MILO_v0.2_ZX81.p` — generated P image