# CHATGPT1 — PICO ZX81 AI working archive

Created: 2026-11-26
Purpose: clean, isolated working directory for the ChatGPT branch of the PICO ZX81 micro-language-model project.

## Source snapshot

The complete content of the repository's `main` tree was copied into `CHATGPT1/` without changing the source files. This includes the previous `GLM/` and `GROK1/` trees, generated releases, source code, knowledge, tools and documentation. The copy is an archive/reference snapshot, not an instruction to mix the other model's work into future development.

## ChatGPT work sources

The later real-ZX81 machine-code work is in the separate repository:
- `kirrdauniverse-collab/retro-tinyllm`
- stable line: `pico/zx81-stable-2026-11`
- current modular line: `pico/zx81-modular-r5`

Future ChatGPT development must use one explicitly identified branch/work tree and must not silently mix binaries, builders or memory maps from another model.

## Proven facts carried forward

ZX81 16K RAM: $4000-$7FFF.
Important system variables:
- D_FILE $400C
- DF_CC $400E
- VARS $4010
- E_LINE $4014
- CH_ADD $4016
- STKBOT $401A
- STKEND $401C
- FRAMES $4034

Verified machine-code regressions:
- V1.5 canonical USR/RET: 0/0
- V1.8 RAM write/read: 0x5A survives and returns to BASIC
- AI16 foundation: the user reported a successful start and HELLO banner before the later R3/R4 line.

## Critical project rule

The user requires the complete testable cassette to be ONE .T81 file. Separate blocks may exist inside that one file. Loading a separate T81 resets the emulator and therefore is not an acceptable replacement for a combined tape.

## Current modular R5 intended map

$4800 active replaceable topic data
$4F00 protected engine/core start
$4F00 RAMTOP target
protected state above RAMTOP
engine stack near $7F00

This map is design state, not yet hardware-proven.

## Archive policy

Do not delete the old model directories until the ChatGPT1 archive and the independent error log have been checked. The old GLM directory is marked deletable by a marker file; its contents remain intact.
