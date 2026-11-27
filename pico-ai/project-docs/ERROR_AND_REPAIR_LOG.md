# PICO ZX81 — ChatGPT error and repair log

This is the consolidated working log for the ChatGPT line. It deliberately separates verified hardware/emulator facts from hypotheses.

## Early machine-code validation

### V1.3
RET test produced C/20. Root cause: incorrect VAL/numeric token encoding.

### V1.4
RET test produced B/20. Numeric representation was still wrong.

### V1.5
Numeric encoding corrected. Result: 0/0. This proved the basic path:
T81 -> P image -> BASIC -> RAND USR -> Z80 -> RET -> BASIC.

### V1.6
RAM write/read experiment failed with C/20.

### V1.7
Canonical RET regression restored: 0/0.

### V1.8
RAM write/read regression succeeded; byte 0x5A was written and read back.

## AI16 foundation

The stable ZX81 branch documents the AI16 build as the promising real machine-code foundation:
- engine origin $4082 (16514)
- 16K image checked against $8000
- one T81 image containing BASIC, engine and parked data
- file: `ports/zx81/mistral_zx81ai16.t81`

The user subsequently reported that this line finally started and greeted HELLO. This is the last clearly recorded positive runtime milestone before the R3/R4 redesign line.

## R3/R4 regression family

The stable branch later produced:
- `dist/PICO_AI_R3_16K.t81`
- `dist/PICO_AI_R4_16K.t81`
- `dist/PICO_ZX81_16K.t81`

The R3/R4 work added or changed D-file scratch, thinking UI, compacted memory layout and runtime text conversion. The repository history records repeated fixes for D-file corruption, matcher pointer preservation, ASCII/ZX81 conversion and stack balancing. R3 was also checked as identical to an earlier binary in the prior debugging record, so this line must be examined by actual binary comparison rather than trusting filenames.

## R5 modular redesign

The modular R5 line changed architecture substantially:
- separate BOOT / SETUP / ENGINE / topic blocks inside one T81
- active topic at $4800
- protected engine at $4F00
- intended RAMTOP $4F00
- profile/history in protected RAM
- topic blocks overwrite the replaceable active-topic area

R5.1 then replaced the RAMTOP-changing first-stage boot with a diagnostic BASIC boot because the previous boot flashed/froze before useful output.

The latest R5.1 boot source deliberately does not execute CLEAR/RAMTOP changes. It requires the BASIC line 1 REM token and then waits for ENTER.

## Known R5.1 build fixes

1. Removed unstable first-stage CLEAR 20224/RAMTOP manipulation.
2. Restored mandatory REM token on line 1.
3. Removed a duplicated broken builder tail.
4. CI structural build passed.

This does NOT prove emulator or real-ZX81 runtime success.

## Safety rules for future debugging

- Never change multiple independent layers at once.
- First reproduce the last known-good binary.
- Then compare exactly one binary/image/T81 change.
- Keep the .P image beside every .T81.
- Verify ZX81 tokens and all pointer relationships before runtime tests.
- Do not use D_FILE as scratch without proving the exact row/character layout.
- Do not assume a successful CI build means a real ZX81 load is valid.
- Never substitute separate T81 files for the user's required single multi-load T81 workflow.
