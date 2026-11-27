# PICO ZX81 — investigation breakpoint

## Last clearly known-good runtime milestone

ports/zx81/mistral_zx81ai16.t81 on branch pico/zx81-stable-2026-11.

Recorded .P SHA: 4bcbbcf756c6472862550ebef87b05c5029e9dab (15385 B).
Recorded .T81 SHA: efe29d5348782139a891a71f42c2b853847e75c4 (15437 B).
The project conversation records this AI16 line actually reaching the HELLO greeting.

## First later-line persistent-failure candidate

dist/PICO_AI_R3_16K.t81
Recorded .P SHA: df926773d7d78dcf0a370c6b95028edbc581c253 (15385 B).
Recorded .T81 SHA: 4277a74636e9bffeb2593e7491f27c43aaabe6af (15437 B).

This is the first R3 comparison target after the AI16 success. R4 then changed again:
- R4 .P: 011dbc9f0ef29701b190340f19ce97842a10d69b
- R4 .T81: b6169bb37b9697a80b65b3d8ae5652bb96b10516
- PICO_ZX81_16K.t81 is an exact alias of the R4 T81.

Therefore the clean test is not to start by repairing R5. First compare the AI16 control against R3. If R3 reproduces the persistent failure, the regression is narrowed to the AI16 -> R3 change set.

## Immediate forensic comparison

1. AI16 .P vs R3 .P byte-for-byte.
2. AI16 .T81 vs R3 .T81 container structure.
3. D_FILE pointer and actual D-file rows.
4. E_LINE / CH_ADD / STKBOT / STKEND / VARS relations.
5. engine origin and end.
6. every absolute address used by the engine.
7. every byte written to D_FILE during boot/thinking.
8. RAMTOP and stack placement.
9. T81 block name, length field and payload boundaries.
10. Only then replay R4 and R5 changes one layer at a time.

Do not modify the two control artifacts before the comparison.