# ERROR_AND_REPAIR_LOG – claude-4

## Ismert hibák és javítások

1. **Lassú válasz (~3 s/karakter)** – javítva v1.1.0 (FAST csak az előrehaladásnál), ~0,4 s/karakter.
2. **Értelmetlen válaszok** – részben javítva (alapbeállítások: greedy, TSH 1). A minőség a modell korlátja.
3. **Fehér kép / lefagyás a névbevitel után** – a valódi gépen (v1.0.0, v1.1.0–1.1.1, később 1.1.2–1.1.4 is) jelentkezik. Több ok lett kizárva vagy valószínűsítve:
   - FAST mód (kijelző ki) – javítva v1.1.2-ben (SLOW alapértelmezés), de a lefagyás megmaradt.
   - MARGIN/DF_SZ sysvar – javítva v1.1.3, valódi hatás nem igazolt.
   - Fekete csík a sor végén (D-file $80) – javítva v1.1.4.
   - Verem-sérülés: az emulátorban a `$7EC4` körüli írás nem volt bizonyítható (a nyomkövetés normál PUSH-okat is rögzített). Nyitott.
   - Az emulátor kijelző-NMI modellje (`tests/nmi_run.py`) saját közelítés; a ROM-NMI egyenkénti lépkedése helyes, de a teljes futásban a modell hibás lehet. Nyitott.
4. **Diagnosztika (v1.1.5-diag)** – canary a `$7E40–$7EC3` tartományban, `CK` jel. Valódi gépen még nem jött eredmény.
5. **GitHub CI (`build-r5`)** – a hiba egy másik (R5/PICO) fa ellenőrzésénél: `line1 is not REM`. Nem ennek a projektnek a buildje.

## Nem igazolt javítás
Egyik verzióról sincs igazolás, hogy a valódi gépen a lefagyás megszűnt.
