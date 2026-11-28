# MILO v0.1 — ZX81 16K

MILO (Micro Intelligent Language Organism) is the new name of the former PICO model line.

## v0.1 control build

The included T81/P pair is the known-good AI16 runtime image, rebranded at the cassette level as MILO v0.1. The machine-code payload is intentionally unchanged so this first MILO artifact remains a clean runtime control.

Known source lineage: former AI16 / PICO ZX81 line.

IMPORTANT: the source file carries the new MILO header, but the historical AI16 binary and the source are not claimed byte-for-byte identical; the old binary is preserved as the runtime control until the next reproducible build.

## Naming rule

All new MILO artifacts use MILO_v<version>_....

Historical PICO/AI16/R3/R4/R5 files remain untouched for forensic comparison.


## Handoff status

**PREPARED FOR HANDOFF — NOT YET RELEASE-ACCEPTED.**

The current P image is 15428 bytes, so it must not be assumed byte-identical to the historical 15385-byte AI16 control. The build script also still contains historical AI16/PICO paths and must be audited before it can be called a reproducible MILO build.

See `MILO_v0.1_HANDOFF.md` and `MILO_v0.1_MANIFEST.md` before making further code changes.
