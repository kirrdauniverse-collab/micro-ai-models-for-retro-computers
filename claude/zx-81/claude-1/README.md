# claude/zx-81/claude-1 – ZX81 AI projekt (Claude Sonnet 4.6, 1. munkaterület)

**Modell:** Claude Sonnet 4.6 (claude-1)  
**Gép:** Sinclair ZX81 (16 KB RAM)  
**Projekt:** retro-tinyllm 16K – kis karakterszintű nyelvi modell ZX81-en  
**Állapot:** Aktív hibakeresés (2026-11-25)  
**Repó forrás:** Sáfár Sándor (kirrdauniverse-collab)

## Összefoglalás

A projekt célja a `retro-tinyllm v0.4.0-16k` motor futtatása ZX81-en, egyetlen `.t81`
kazettafájlból töltve. A GLM és Gemini modellek által elkezdett munkát vettem át,
majd bináris patcheléssel javítottam a betöltési hibákat.

## Ismert hibák és állapot

Lásd `docs/ERROR_AND_REPAIR_LOG.md` és `docs/BREAKPOINT.md`.

A modell betöltése javítva (B2), de a D-file / display inicializálás még nem stabil.
A legutóbbi tesztelésre kész verzió: **v9**.

## Könyvtárszerkezet

```
claude-1/
  README.md               – ez a fájl
  MIGRATION_MANIFEST.md   – honnan kerültek ide a fájlok
  MIGRATION_STATUS.md     – a költöztetés állapota
  PROJECT_INDEX.md        – fájlleltár
  ERROR_AND_REPAIR_LOG.md – ismert hibák és javítások
  BREAKPOINT.md           – fejlesztési állapot
  binaries/
    t81/   – kazettafájlok (EightyOne emulátorhoz)
    p/     – nyers .P képfájlok (ZX81 standard)
  reference/
    engine/  – az eredeti C-motor forrása (retro-tinyllm v0.4.0-16k)
    app16.c  – ZX81 portfájl
    hal_zx81.c – hardware abstraction layer
  models/
    base_f.bin  – RTLM modell (Class F, 2666 bájt, vocab=45)
  tests/
    golden_base_f.txt – referencia tesztvektorok
  tools/
    verify_findings.py – ROM és modell ellenőrző szkript
  docs/
    B2_checksum_length.md – B2 hiba és javítás leírása
    B3_line2.md           – B3 hiba és javítás leírása
```
