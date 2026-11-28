# PICO AI — 3. hibaüldöző menet állapotjelentés (2026-11-23)

## Mi volt a jelensés
A felhasználó jelentése: a kazetta első betöltése után a gép azonnal
"resetel". (Az 1. javítás — az EO81-mágia törlése — nem volt elég.)

## Amit ez a menet fel tárt (döntő előrelépés)

### 1. Megépült a VALÓDI ROM-szimulátor
`tools/romsim.py`: a hiteles 8K ZX81 ROM fut a szimulátorban — a gép
hideg indulástól (RAM-CHECK, inicializálás, szerkesztő) a valódi
ROM-kóddal épül fel. Ez lett volna a hiányzó láncszem: eddig a
python-szimulátor a BASIC-sorokat SOSEM futtatta, csak a gépi kódot.

### 2. A Z80 magban kritikus hibát találtam és javítottam
Az FD-CB utasításdekóder off-by-one hibája: a `RES n,(IY+d)` opcode-
ját rossz bájtról olvasta — a ROM `RES 1,(IY+1)` (TV-flag) utasítása
SET-té torzult, ettől a szerkesztő kimenete a nyomtató-pufferbe
futott és felülírta a RAMTOP-ot.

### 3. A ROM-ból levezetett valódi rendszer-változó-térkép
Az eddigi tévképzetek (Spectrum-os/ZX80-as emlékek) helyett:
- RAMTOP a 0x4004-en (POKE 16388!) — a .P képen KÍVÜL
- CDFLAG a 0x403B-en (7. bit videó, 6. bit SLOW)
- LAST-K a 0x4025, MODE a 0x4027, FLAGS a 0x402D
- A ZX81 `USR`-ja BC-vel tér vissza (nem A-val!)
- A ZX81 BASIC számliteráljai 0x7E+5 bájtos FP farkat követelnek
- `LOAD ""` Spectrum-izmus: ZX81-en `LOAD "PICOBOOT"` a helyes

### 4. A bizonyított v0.5.4-es blokk-minta (a követendő út)
- `1 REM <összes ML>` + `2 IF USR 16514 = 1 THEN LOAD "KÖVETKEZŐ"`
- Minden blokk ML-e induláskor: LD IY,$4000 + videó vissza (CDFLAG)
- Nincs BASIC PRINT/INPUT/NEW (az én boot-BASIC-em ezért volt hibás)
- A képben: [program][D_FILE][VARS-jelző][E_LINE] sorrend (LOC-ADDR!)

## Mi maradt nyitva
A szerkesztő kijelző-kibővítése a LOC-ADDR 0x0929-es hurokjában akad
a ROM-szimulációban (a hurok körülményeit kell felvenni: ki hívta,
mekkora B-vel). Utána: a PICOBOOT/PICOBASE újraírása a fenti mintára
és a teljes lánc (boot → LOAD → motor → chat → /save) ROM-szintű
tesztje, majd a kazetta újraépítése és kézbesítése.

**A Kazetta (dist/ZX81PICO.T81) ebben az állapotban MÉG NEM működik
valódi gépen/emulátorban — kérlek, ne ezzel próbálkozz!**
A következő menet a fenti terv szerint fejezi be.
