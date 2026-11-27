# PICO ZX81 stable branch

This branch is the consolidated ZX81 16K line for the PICO project.

## What is already verified on the EightyOne emulator

- V1.5 canonical USR/RET test: 0/0
- V1.8 RAM write/read test: returns to BASIC and byte 0x5A is preserved
- Therefore the proven loader path is:
  T81 -> P-file -> BASIC -> RAND USR 16514 -> Z80 at 0x4082 -> RET -> BASIC

## Fixes carried forward from the earlier promising AI16 branch

1. The BASIC line-2 token sequence is built from real ZX81 tokens:
   RAND / USR / VAL / quotes, followed by the five-byte numeric representation of 16514.
2. The engine origin is 0x4082 (16514).
3. The 16K image is checked against the 0x8000 RAM limit by the builder.
4. The AI16 branch already contains the earlier B2 model-checksum correction and B3 line-2 token correction described in its history.
5. This branch adds a standalone structural validator and a known-good RAM regression cassette.

## Current AI build

The existing AI16 engine is kept intact rather than replacing it with another BASIC demo. The target remains a real Z80 machine-code engine with its model/data parked inside the 16K image.

The ready-to-download AI image is:

- `dist/PICO_ZX81_16K.t81`
- `dist/PICO_ZX81_16K.p`

They are aliases of the existing AI16 build from the parent branch, so the binary itself is not silently changed.

## Regression test

- `tests/PICO_V1_8_RAMTEST.T81`

This is the small test that was actually run successfully in EightyOne:
it writes 0x5A, reads it back, and returns to BASIC.

## Important

The AI16 binary has not been claimed as a finished intelligent PICO model. It is the promising machine-code foundation. The next engineering step is to make its runtime pass the same small, isolated tests that the loader now passes before expanding the generator.

