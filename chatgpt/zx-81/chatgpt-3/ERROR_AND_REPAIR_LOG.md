# ChatGPT 3 — error and repair log

This consolidates issues evidenced by the legacy ChatGPT notes and the shared PICO AI continuation conversation. It does not claim that any fix has been reproduced during migration.

## Earlier PIOCO AI technical audit (2026-11-22 / 2026-11-23)
- PIOCO v0.6 `.P` was recorded as a stable boot/splash milestone, not a finished conversational AI.
- `motor/motor0.asm` was recorded as remaining in the `MWAIT` loop; ROM INPUT, tokenizer, trigram generation, chat history and final multiload `.T81` runtime were still future work in that source line.
- The audit identified documentation/source mismatches in BOOT size, token allocation, trigram weight interpretation and `.P` versus `.T81` semantics.
- D_FILE writes must pass through one checked print funnel; binary token IDs, flags, addresses and CRC data must never be written directly to D_FILE.
- Profile persistence and the ROM stack region require strict non-overlap checks.
- No fresh EightyOne/ZEsarUX run of all candidate binaries was claimed by that audit.

## Later continuation conversation — symptoms reported
- RUN caused an immediate failure in one test build.
- Other builds reached data entry but were very slow and keyboard input was duplicated / misread; the user explicitly requested the ZX81 ROM INPUT routine.
- A later test showed the screen moving downward during entry.
- Unexpected characters appeared near the lower-right screen area; the user suspected D_FILE corruption and possible overwriting of BASIC / system data.
- The latest shared transcript says profile and conversation state were moved out of the visible D_FILE region into a hidden 144-byte area, with 72 bytes for profile state and 64 bytes for a two-line history buffer.
- That transcript reports a successful compile and nine checks, plus checks of 15 cassette blocks and 24 screen rows. These results have not been independently repeated here.

## Current status
The uploaded CleanDisplay T81 and the IYBootstrap_Final2 archive are preserved in the current conversation and in a local continuity archive, but not in this Git branch yet. No code change or emulator pass is asserted by this migration.
