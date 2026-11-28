# BREAKPOINT – claude-4 (Cricket-81)

## Hol tart
- v1.1.6-diag: a betöltő (RTLOAD) és a motor (RTCHAT) külön .P képként és egy .t81 kazettán is elkészült.
- A valódi gépen a fehér kép / lefagyás a névbevitel után nem javult.

## Következő lépés
1. Valódi gépen a v1.1.6-diag tesztelése: a `CK` jel megjelenik-e, és melyik bevitelnél.
2. Ha nincs `CK`, a sérülés a canary-területen kívül van: a `$7EC4` fölötti veremterület és a D-file határok ellenőrzése.
3. A tesztelő által küldött pontos képernyőkép és a PC/Halt/Interrupts állapot a legfontosabb adat.

## Nyitott kérdések
- Melyik verzióról indultak a valódi gépen tapasztalt hibák?
- A betöltő (RTLOAD) után a RUN és a motor-betöltés valódi gépen működik-e?
