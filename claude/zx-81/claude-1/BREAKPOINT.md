# BREAKPOINT.md – claude/zx-81/claude-1

## Hol tart a fejlesztés (2026-11-25)

### Elvégzett munka
1. A B2 checksum hiba azonosítva és javítva (v7, v9)
2. A B3 BASIC sor hiba azonosítva és javítva (v9)
3. ROM rutinok ellenőrizve (`verify_findings.py`)
4. A v2_root.t81 (GLM build) elemzése
5. Charset eltolás azonosítva (B4)
6. D-file cursor inicializálás feltérképezve (0x422D)
7. hal_putchar és rt_model_load disassemblálva
8. SLOW/FAST trampoline kísérlet (0x5C77-es szabad terület)

### Legfontosabb nyitott kérdés
**A T81 betöltés után a display azonnal sérül.** Ez a probléma minden módosított
változatban megjelenik, de az eredeti GLM-es T81-ben nem.

### Következő lépések (prioritás szerint)
1. **Izolálni:** Melyik byte-változtatás okozza a display sérülést?
   - Tesztelni: v7 (B2 only, 2 bájt) `.p` fájlként direktbe töltve
   - Ha a `.p` rendben van de T81-ből nem: a T81 betöltés a hibás
   - Ha a `.p` is sérül: az engine fut és ront
2. **EightyOne T81 forrás ellenőrzése:** a t81load.c-ben megnézni pontosan
   hova tölti a payloadot és hogyan kezeli a prefix bájtokat (FF 00 vs 00 01)
3. **Display cursor init:** a 0x422D és 0x422B változókat bootkor nullázni
   vagy a D-file kezdőcímére állítani, még az első hal_putchar előtt
4. **Ha minden más nem segít:** az engine SLOW módba állítása már a boot
   elején (0x4095 előtt), hogy a display folyamatosan aktív legyen

### A trampoline probléma
A CALL 0x0F28 (SLOW) hívása `JP 0x0207`-tel folytatódik a ROM-ban.
0x0207 a ZX81 display scan rutin – ez nem egyszerű mód-váltás!
A közvetlen `FD CB 3B F6` (SET 6,(IY+0x3B)) biztonságosabb alternatíva.
Ezt a v9-ben még nem próbáltuk ki.

### Javasolt próba (nem elvégzett)
```
; Trampoline at 0x5C77 – direct CDFLAG bit set, no ROM call:
FD 21 00 40  LD IY,0x4000      ; ensure IY correct
FD CB 3B F6  SET 6,(IY+0x3B)   ; SLOW: NMI enable
CD D9 6B     CALL 0x6BD9        ; hal_getchar
E5           PUSH HL
FD 21 00 40  LD IY,0x4000
FD CB 3B B6  RES 6,(IY+0x3B)   ; FAST: NMI disable
E1           POP HL
C9           RET
; Total: 22 bytes
```
