# ChatGPT 3 — PIOCO AI ZX81 breakpoint

## Workspace
`chatgpt/zx-81/chatgpt-3/`

## Latest available artifacts (local conversation files, not yet in GitHub)
1. `PIOCO_AI_English_16K_CleanDisplay(1).t81` — 225,941 B; SHA-256 is in `MIGRATION_MANIFEST.md`.
2. `PIOCO_AI_English_16K_IYBootstrap_Final2_artifact(1).zip` — 35,961 B; SHA-256 is in `MIGRATION_MANIFEST.md`.
3. The ZIP contains `ports/zx81/pio16_release/PIOCO_AI_English_16K_ROM_INPUT.t81` (225,115 B), `rboot16.P/.bin`, and `rtchat16.P/.bin`.

Treat the CleanDisplay and ROM_INPUT tapes as different candidates. Do not silently substitute one for the other.

## Last state reported in the shared conversation
The previous conversation reports that profile/history storage was moved out of visible D_FILE into a hidden area, and that compilation plus nine checks passed. It also reports a 15-block cassette and 24 screen rows checked. These are historical claims from the transcript and need to be rerun before relying on them.

## Next technical sequence
1. Add the binary continuity bundle to this workspace using a byte-preserving Git upload method and verify its SHA-256.
2. Inspect both T81 containers and block headers; compare block counts, destinations, lengths and entry points.
3. Compare the CleanDisplay tape against the ROM_INPUT tape inside the archive; do not assume same build lineage based on similar names.
4. In EightyOne V1.41, test load-only, boot, RUN/ENTER behavior, profile input, ROM INPUT character editing / backspace, keyboard repeat and screen stability.
5. Capture D_FILE, VARS, E_LINE, CH_ADD, STKBOT, STKEND, RAMTOP and IY before and after the profile entry phase.
6. Check every memory write against the display file, hidden profile/history store, BASIC workspace and machine stack; verify all D_FILE row terminators and final stop byte.
7. Re-test fast/slow modes independently; do not use accelerated emulation as proof of physical keyboard debouncing.
8. Only after this evidence is collected, make the next version in this ChatGPT-3 workspace. Preserve both supplied artifacts unchanged.

## Guardrails
- Never modify `chatgpt-1` or `chatgpt-2`.
- Do not copy / edit GLM, Grok or any other model's files.
- Keep source `.P`, `.T81`, assembly and build scripts together for every new version.
- Distinguish compile/static checks, emulator tests and real-hardware tests.
