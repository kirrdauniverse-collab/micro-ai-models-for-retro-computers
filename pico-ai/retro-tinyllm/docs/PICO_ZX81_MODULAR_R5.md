# PICO ZX81 Modular R5

R5 abandons the monolithic REM-engine layout.

## Protected 16K map

| Range | Purpose |
|---|---|
| `$4F00-$688F` | PICO Z80 engine |
| `$6900-$6EFF` | compact CORE knowledge bank |
| `$6F00-$707F` | help pages |
| `$7080-$71FF` | reserved |
| `$7200-$73FF` | volatile engine work area |
| `$4800-$4EFF` | replaceable topic knowledge loaded below RAMTOP |
| `$7A40-$7CC3` | 20 conversation-history slots |
| `$7CC4` | persistent active-topic ID |
| `$7D00-$7EFF` | persistent user profile / journal |
| `$7F00-$7FFF` | engine machine stack |

`RAMTOP=$4F00` is established by the BOOT BASIC program with `CLEAR 20224`, then the user enters `NEW`. The engine, CORE, profile and history live above RAMTOP and are therefore protected. Topic knowledge deliberately lives below RAMTOP at `$4800`; loading the next topic cassette overwrites that area, which is exactly the desired topic-switch mechanism.

## Cassette roles

1. `PICO_BOOT_R5.T81`
   - splash screen
   - executes `CLEAR 20224` to set RAMTOP
   - tells the user to type `NEW`
   - then the setup cassette is loaded manually

2. `PICO_SETUP_R5.T81`
   - collects `DDMMYY`, `HHMM`, name, gender and instructions Y/N
   - writes the persistent profile to `$7D00`
   - clears the active topic state
   - returns to BASIC and asks for the engine cassette
   - collects date/time/name/gender and optional instructions
3. `PICO_ENGINE_R5.T81`
   - loads the protected engine and CORE bank
   - does not contain the user profile
   - starts at `$4F00`

4. Topic cassettes
   - `PICO_SCIENCE_R5.T81`
   - `PICO_ASTRONOMY_R5.T81`
   - `PICO_HISTORY_R5.T81`
   - `PICO_PROGRAMMING_R5.T81`
   - each writes only `$4800-$4EFF`
   - a tiny self-starting stub sets `VPACK` and jumps back to `$4F00`

## Topic switching

The CORE contains a small topic index. When a question scores as a topic whose overlay is not active:

`TOPIC DATABASE NOT LOADED -> Y/N -> load requested cassette -> return to PICO`

All topic packs share one physical replaceable slot below RAMTOP. Loading a new topic therefore replaces only the current topic knowledge, not the protected engine, CORE, profile or history.

## Important invariant

No routine may clear `$6900-$7EFF` during normal engine initialization. Only the volatile work area and history ring may be reset deliberately.

## Build verification

The R5 CI build checks:
- BASIC/D_FILE/E_LINE structure
- D_FILE remains below RAMTOP
- protected engine entry at `$4F00`
- CORE bank signature
- all topic overlays fit their slot
- generated P/T81 files exist and have valid structure
