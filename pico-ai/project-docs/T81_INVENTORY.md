# T81 inventory — consolidated forensic index

## ChatGPT ZX81 stable/modular line

| File | Size | SHA | Role |
|---|---:|---|---|
| ports/zx81/rtframe_empty.t81 | 968 | 0669e0f8aded2e23b2963427e2fa33500672f572 | bare 16K load regression |
| ports/zx81/rtframe_ok.t81 | 1009 | 24e8fbf8c743d0f680bfd675ae33759f0fd2714b | known-good loader/USR/D_FILE regression |
| tests/PICO_V1_8_RAMTEST.T81 | 941 | d18401ef480464ab448dbb764a1892df1f5b3179 | V1.8 RAM write/read regression |
| ports/zx81/mistral_zx81ai16.t81 | 15437 | efe29d5348782139a891a71f42c2b853847e75c4 | AI16 foundation; last clearly recorded positive AI runtime milestone |
| dist/PICO_AI_R3_16K.t81 | 15437 | 4277a74636e9bffeb2593e7491f27c43aaabe6af | first R3 comparison target after AI16 |
| dist/PICO_AI_R4_16K.t81 | 15437 | b6169bb37b9697a80b65b3d8ae5652bb96b10516 | R4 line |
| dist/PICO_ZX81_16K.t81 | 15437 | b6169bb37b9697a80b65b3d8ae5652bb96b10516 | alias of R4 binary |
| dist/r5/PICO_AI_R5_ALL.T81 | 25974 | 8169bf6c50af303a529cd921b0b7f32db5968fee | single combined R5 tape |
| dist/r5/PICO_BOOT_R5.T81 | 1349 | 2982d80bc533ae299fae9243d5d83a4b9a8d90a0 | diagnostic boot block |
| dist/r5/PICO_SETUP_R5.T81 | 1349 | e2278e863c179c4a69bd9ee645e7c52816062358 | setup block |
| dist/r5/PICO_ENGINE_R5.T81 | 12399 | f04c81f4f101065eab97aa0d654d85dd27528798 | engine block |
| dist/r5/PICO_SCIENCE_R5.T81 | 2723 | 38429ad2d2fa4e696ebb780acccbcae90b317ea5 | topic block |
| dist/r5/PICO_ASTRONOMY_R5.T81 | 2821 | 97feb666a16b7ae07b9c4f9ffe7994b3077d27f0 | topic block |
| dist/r5/PICO_HISTORY_R5.T81 | 2662 | c9cfaf3802e3b54592f26c830c25c19473d4156d | topic block |
| dist/r5/PICO_PROGRAMMING_R5.T81 | 2695 | 3eefb696b82471df2f34e57a491f6f2da5b80e69 | topic block |
| ports/zx81/retro_tinyllm.t81 | 43877 | 76991cad2a7a62bbfb1d4356d89d9c055f373078 | earlier large cassette; not the 16K baseline |

## Breakpoint

The R3/R4 .P artifact is known to have been identical in the earlier debugging record, so a same-sized T81 does not prove a different engine.

Use this forensic pair first:
1. mistral_zx81ai16.t81 — known-good control.
2. PICO_AI_R3_16K.t81 — first later-line candidate.

Do not modify either file before comparison.
