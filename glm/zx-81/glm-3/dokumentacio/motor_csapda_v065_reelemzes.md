# A $7AE0-s farokcsapda-család re-elemzése a v0.6.5 ALAPFÁJL-on

Dátum: 2026-11-28 · Példány: GLM-3 · Munkaterület: `glm/zx-81/glm-3/`
Feladat: `ATADASI_DOKUMENTUM.md` 7. fejezet 1. pontjának **statikus fele** —
a v0.6.5 15 blokkjának $7AE0 környéki vizsgálata a hiteles ROM-referenciával
(`refs/zx81.rom` + Logan & O'Hara `refs/zx81rom.txt`), a v0.9.2-vel bájt-szinten
összevetve. Eszköz: `szkriptek/motor_reelemzes_17.py` (önszámolt,
környezetfüggetlen futás; a régi `trap_disasm.py` kézi dekóderére épülő
ellenőrzéssel párhuzamosan).

## 0. Azonnali tények (minden állítás bájt-szinten ellenőrzött)

1. **A vizsgált régió mind a 15 blokkban azonos.** A $7A40–$7AF4 szekció
   (a teljes motor display-berendezés) a v0.6.5-ben **mind a 15 blokk
   képében bájtazonos**; a v0.9.2-ben is az. A két verzió közt a régióban
   **csak 3 bájt** tér el: $7AE5–$7AE7. Ezért az átadási dokumentum
   „a v0.6.5 15. (motor-) blokkjának disassembly-ja” mondatával bármelyik
   blokkra érvényes — a 15. (RT-VERSE) is ugyanazt a bájtsort hordozza;
   az élőben futó példány az **RTBASE16** (a chat-motor betöltött képe).
2. A csapda-octett ($7AE0–$7AE5) minden blokkban:
   v0.6.5 = `3A 3B 40 E6 80 CA`, v0.9.2 = `3A 3B 40 E6 80 DB` —
   tehát a dokumentált patch ($7AE5: `CA A9 02` → `DB FE FB`) pontosan
   ennyi: a **FAST-ág egyetlen JP-je** cserélődött le.
3. A v0.6.5→v0.9.2 **teljes** kazetta-diff blokkonként (a motor_reelemzes_17
   D-szekció): RTBOOT01 = 6 B ($4016–$4017 CH_ADD, $54BA programvég-jel,
   $7AE5–$7AE7 trap); a többi 14 blokk = 8 B ($4016–$4017, $56E6–$56E8
   banner „v0.6.5”→„v0.9.2”, $75B5 programvég-jel, $7AE5–$7AE7 trap).
   **Ennyi az egész** — minden korábbi „javítás” e 6–8 bájtban foglaltatik.

## 1. A motor display-berendezése: a teljes lánc térképe

A motor a ZX81 ROM display-gépezetét **teljes egészében klónozta** RAM-ba,
abszolút címzéssel (a ROM IY-relatív címzése helyett). A szekció
$7A40–$7AF4-ig terjed, és a ROM-mal bájt-szinten párhuzamosítható:

| Motor (RAM) | ROM-párhuzam | Funkció |
|---|---|---|
| $7A40 `FD E5` PUSH IY | — | IY mentése |
| $7A42 `FD 21 00 40` LD IY,$4000 | — | IY = sysvar-bázis (a ROM $0F2B miatt) |
| $7A46 `CD 2B 0F` CALL $0F2B | $0F2B SLOW | `SET 6,(CDFLAG)` — slow-display elérhető |
| $7A49–$7A4C LD HL,$7AC9 / PUSH HL | ROM IX=$0281 minta | a display-közbülépítő **horgony** a veremre |
| $7A4D–$7A52 LD A,($403B) / AND $80 / JR Z,$7A5B | — | CDFLAG bit7 teszt (0 = FAST) |
| $7A54–$7A59 LD HL,$4034 / LD A,(HL) / CP (HL) / JR Z,$7A58 | DISPLAY-1 FRAMES | FAST: ugri; SLOW: FRAMES-várakozás (NMI frissíti) |
| $7A5B–$7A5E POP IX / POP IY / RET | — | **IX = $7AC9** kilépéskor (a ROM NMI-CONT `JP (IX)`-ja ezt látja) |
| $7A60–$7A74 LD HL,($4034) … RET NC | $0229 DISPLAY-1 | frame-counter ($4034 = FRAMES, címegyezés) |
| $7A75–$7AAF CALL $02BB … OUT ($FF),A | $023E DISPLAY-2 | KEYBOARD, LAST-K ($4025), DEBOUNCE ($4027) — címegyezés |
| $7AB0–$7AB4 LD HL,($400C) / SET 7,H | $0279 | HL = D_FILE\|$8000 |
| $7AB5 CALL $7ADA | $027E CALL DISPLAY-3 | lásd 2. szakasz |
| $7AB8–$7ABF LD A,R / LD BC,$1901 / LD A,$F5 / CALL $02B5 | $0281–$0288 | ROM DISPLAY-5 hívás (JP (HL) → a kijelzőfájlba) |
| $7AC2–$7AC6 DEC HL / CALL $7ADA / JP $7A60 | $028B–$028F | alsó rész + ciklus |
| $7AC9–$7AD7 (ugyanaz LD A,R-től) | — | a **horgony-cél**: közvetlen alsó-rész belépés |
| $7ADA–$7AF1 (a csapda) | $0292 DISPLAY-3 | lásd 2. szakasz |
| $7AF2 `C3 E1 41` JP $41E1 | — | kilépés a motor billentyű-rutinjába (nincs literális hivatkozás: közvetett) |

**Beépítési pontok** (F-szekció): RTBOOT01 @$4C27 és RTBASE16 @$5244:
`PUSH BC / PUSH BC / DEC SP / CALL $7A40` (+4 NOP padding). Más literális
hivatkozás nincs ($7A60/$7AC9/$7ADA/$7AF2/$41E1-re se JP, se CALL, se
LD IX/LD HL forma). A `JP (IX)` (DD E9) a motor saját kódjában **0-szor**
fordul elő — az IX=$7AC9 horgonyt tehát csak a **ROM NMI-CONT** ($006F→
`JP (IX)`) léptetheti életbe, ha NMI indul és IX éppen $7AC9.

## 2. A csapda boncolása — $7ADA (a ROM $0292 DISPLAY-3 klónja)

```
7ADA: DD E1       POP IX          ; a CALL $7ADA visszatérési címe → IX
                                  ;   (RTBASE16-úton $7AB8, horgony-úton $7AD7)
7ADC: 3A 28 40    LD A,($4028)    ; MARGIN (=ROM IY+$28) → C
7ADF: 4F          LD C,A
7AE0: 3A 3B 40    LD A,($403B)    ; CDFLAG (=ROM IY+$3B)
7AE3: E6 80       AND $80         ; bit7 = 0 → FAST mód
7AE5: CA A9 02    JP Z,$02A9      ; *** FAST-ág → ROM DISPLAY-4 ***
7AE8: 79          LD A,C          ;  – SLOW-ág: a ROM DISPLAY-3 margó-pulzusának
7AE9: ED 44       NEG             ;    szó szerinti mása
7AEB: 3C          INC A
7AEC: 08          EX AF,AF'
7AED: D3 FE       OUT ($FE),A
7AEF: C3 A4 02    JP $02A4        ; ROM restauráló farok: POP HL/DE/BC/AF/RET
7AF2: C3 E1 41    JP $41E1        ; (alternatív kilépés, közvetett cél)
```

ROM-hitel (bájt-pontos, a `refs/zx81.rom` $0290–$02C0 szakaszból):
$0292 DISPLAY-3 `POP IX / LD C,(IY+$28) MARGIN / BIT 7,(IY+$3B) CDFLAG /
JR Z,$02A9 / LD A,C / NEG / INC A / EX AF,AF' / OUT ($FE),A / POP HL / POP DE /
POP BC / POP AF / RET`; $02A9 DISPLAY-4 `LD A,$FC / LD B,$01 / CALL $02B5 /
DEC HL / EX (SP),HL / EX (SP),HL / JP (IX)`; $02B5 DISPLAY-5
`LD R,A / LD A,$DD / EI / JP (HL)`.

A klón **egy-kettőre pontos** (MARGIN=$4028, CDFLAG=$403B, FRAMES=$4034,
LAST-K=$4025, DEBOUNCE=$4027, D_FILE=$400C — mind címegyezőek a ROM-mal),
a $02A4-es restauráló-farokra és a $02A9-es FAST-ágra egyenes JP-vel ugrik.

## 3. A halálút rekonstrukciója — miért PC=$004x

1. A motor **FAST módban** fut (ez a motor természetes üzemmódja; CDFLAG
   bit7 = 0 — a ROM $02E7 SET-FAST szemantikája szerint ilyenkor az NMI-
   generátor KIKAPCSOLT).
2. A display-berendezés bármely útja eléri a $7ADA csapdát (a $7AB5/$7AC3/
   $7AD4 CALL-ok; mindkét hívó RTBOOT01-ben és RTBASE16-ben fut).
3. $7AE3 `AND $80` → Z=1 (FAST) → **`JP Z,$02A9` → ROM DISPLAY-4**:
   `LD A,$FC / LD B,$01 / CALL $02B5` → **DISPLAY-5**: `LD R,A / LD A,$DD /
   EI / JP (HL)`.
4. FAST módban NMI nincs, tehát a DISPLAY-5 által megkívánt NMI-vezérelt
   kijelző-gépezet (a Logan & O'Hara szerinti soronkénti NMI-szinkron)
   **nem indul el**; a CPU a `JP (HL)`-lel oda ugrik, ahol a motor HL-je
   áll. Ez az HL a hívási helytől függ:
   - $7AB5/$7AC3 úton: D_FILE\|$8000 (=$FB00…), **csakhogy a RTBASE16
     betöltött képe $7AF5-nél végződik** (a 0x80 programvég-jelnél az EO
     levág), miközben a D_FILE-mutató $7B00-ra céloz — vagyis a
     kijelzőfájl területe az RTBOOT01 **maradványbájtjait** tartalmazza
     (a multi-load azokat nem írja felül). A kijelzőfájl-bájtok mint
     „kód” végrehajtása ($76 = HALT!) → téblábas futás.
   - a $7AC9 horgony-úton: az interpreter aktuális HL-je (tetszőleges).
5. A futás a ROM-ba csúszva a **$0038–$0047-es INT-restart bájtsorra** ér,
   amelynek $0041–$0044 része (`ED 4F FB E9` = `LD R,A / EI / JP (HL)`)
   HL=$0041 mellett **örök önhurok** ($0041→$0044→$0041…); a $0045–$0047
   (`POP DE / RET Z / JR $0041`) ugyanide gyűr vissza. Ez a ROM egyetlen
   stabil PC=$004x attraktora — **ez a mért tünet**.
6. A látvány szintén egyezik: a DISPLAY-5 `LD R,A`-ja a ULA videó-
   címszámlálóját (R-regiszter) írja keret közepén → 2–3 grafikus karakter,
   a felső sor kiúszása; az örök várás → fehér/fagyott kép.

**Súlyos következtetés a klónról:** a ROM saját folyásában a DISPLAY-3
bit7=0 ága gyakorlatilag halott kód (a DISPLAY-1-be csak akkor jutunk,
ha a SLOW/FAST rutin előbb `SET 7,(CDFLAG)`-et végzett, az NMI-vezérelt
úton pedig bit7 épp 1). A motor klónja ezt az ágat viszi át éles
FAST-környezetbe — ott, ahol a ROM-mechanika feltétele (NMI) nem áll fenn.
**Ez a $7AE0-s farokcsapda-család gyökere**, és ez magyarázza, hogy a
tünet változatlan maradt a javításoktól függetlenül.

## 4. Miért voltak „gyanúsan hatástalanok” a javítások — bájt-szintű magyarázat

A teljes diff (3. pont a 0. szakaszban) megmutatja, hogy a korábbi
javítások **egyetlen bájtot sem írtak a $7ADA–$7AF1 halálágban**:

| Verzió-lépés | Mi változott (mért) | Miért nem hatott |
|---|---|---|
| v0.8.0 (45 B „jelző-javítás”) | programvég-jel 0x76→0x80 @$54BA (RTBOOT01) és @$75B5 (RTBASE16) + CH_ADD @$4016–$4017 | BASIC-metaadat; a $7ADA FAST-ág érintetlen → tünet változatlan (10. menet) ✓ |
| v0.8.1 (OUT FE) | $7AE5: `CA A9 02`→`D3 FE FB` | ÉLES ELEMBEN SOSEM PRÓBÁLTÁK ÖNÁLLÓAN; az ág elvileg át lett volna irányítva, de az OUT($FE) az EO-ban LASTINSTOUTFE sync-injektálást vált ki — a ráépülő v0.9.1 csíkjainál ez látszott |
| v0.9.1 (név-prefix + RTMEM16) | név-prefixek + RTMEM16 blokk | a bit7-terminátor hiánya (0x22 vs 0xA2) betöltési elcsúszást adott — a tünet itt betöltési idejű volt |
| v0.9.2 (IN FE) | $7AE5: `D3 FE FB`→`DB FE FB` | az első tényleges halálág-patch (lásd 5. szakasz) |

Tehát a „három különböző javítás, négy MD5, változatlan tünet” minta
**nem gyanús valami misztikus dolog**: az első három javítás objektíven
nem érte el a hibás utasításutat. A v0.6.5 alapfájl-választás ezért
módszertanilag helyes — és a re-elemzés megerősítette.

## 5. A v0.9.2-patch szemantikája és a reziduum

v0.9.2-ben $7AE5–$7AE7 = `DB FE FB` = `IN A,($FE) / EI`:

- a **DISPLAY-4/5 halálág megszűnik** (nincs JP a $02A9-re) — minden ág
  a SLOW-farokra esik: margó-pulzus (`OUT ($FE),A` @$7AED) + `JP $02A4`
  restaurálás;
- az `IN A,($FE)` olvasás az EO-ban biztonságos (nem injektál sync-et) —
  az olvasott érték úgyis elveszik ($7AE8 `LD A,C` felülírja);
- `EI` FAST módban hatástalan (ULA nem generál INT-et);
- **reziduum:** az `OUT ($FE),A` @$7AED a fall-through úton **minden
  CALL $7ADA alkalmával lefut** (display-ciklusonként 2×). Ha az EO
  LASTINSTOUTFE-logikája hívásonként sync-impulzust injektál az aktuális
  képsorba, csík-előfordulás várható — **ezt dönti el az élő A-próba**.
  Megjegyzés: az EO-injekció v0.9.1-es tünetét betöltési idejű, név-
  prefixhibás folyás okozta; a v0.9.2 chat-idejű, szabályos pulzusa
  „képenként 1-2 sync” lehet, ami FAST-módban normális is lenne.

## 6. Az élő EO-utasítás-követés törzsadatai (a tulajdonos EO-debuggeréhez)

Cél: a 3. szakasz halálútjának **élő igazolása** a v0.6.5-ön, és a v0.9.2
A/B/C-próbájának lebonyolítása. Javasolt töréspontok (a 15 blokk bármelyikén,
a régió blokkok közt azonos):

| BP | Cím | Mit nézni |
|---|---|---|
| 1 | $7ADA | IX, HL, SP-tető; CDFLAG ($403B) bit7 — 0 kell legyen (FAST) |
| 2 | $7AE5 | ellenőrzés: AND $80 után Z=1 |
| 3 | $02A9 (DISPLAY-4) | HA IDE ÉRÜNK: a halálág élőben megerősítve; HL-jegyzés |
| 4 | $02BA (DISPLAY-5 JP (HL)) | **HL értéke** → hová ugrik ($FB00-Maradvány? ROM?) |
| 5 | $0041 / $0044 | az örök hurok igazolása; HL=$0041? |
| őrző | $403B (CDFLAG), $4034 (FRAMES), $400C (D_FILE), $4028 (MARGIN) | mód-váltás nyomon |

Várt eredmény v0.6.5-ön: BP3/BP4/BP5 sorrendben üt — ezzel a bizonyíték
zárul. v0.9.2-n: BP3-nak soha nem szabad elütnie; A-próbánál figyelni a
csíkokra (reziduum), B: az RTBASE16 után elindul-e a chat, C: /quit.

## 7. Jelölt javítások — CSAK az A/B/C próbák után, új verziószámmal

Az összevetés lezárásáig a v0.6.5 és a v0.9.2 nem módosítható (munkarend).
Ha az A-próba csíkot mutat (reziduum), a legkisebb v0.9.3-jelöltek:

1. **1 bájtos:** $7AE5: `CA A4 02` (JP Z,$02A4) — a FAST-ág pulzus nélkül,
   egyenesen a restauráló-farokra tér vissza; SLOW-ág változatlan. Nincs
   port-írás FAST-ban, nincs DISPLAY-4/5, nincs EO-sync-injektálás.
   Kockázat: valós HW-en FAST-módban elmarad a margó-pulzus (EO-n elvileg
   felesleges, valós ULA-n a kép stabilitása a kérdés).
2. **2 bájtos:** $7AED: `D3 FE`→`00 00` (NOP NOP) — a fall-through pulzus
   szűnik; a SLOW-mód margó-pulzusa is eltűnik (SLOW nem használt út a
   motorban) — durvább, de minden EO-injekciót megszüntet.
3. Súlyosabb átalakítás (külön tervezés): a $7A40 élesítőt FAST-ágban
   NMI-mentes „pulzus nélküli kilépésre” rendezni és a $7AB0 flow-t
   kiiktatni — csak ha 1-2 bebizonyosodik elégtelennek.

## 8. Számíthatóság

- Elemző szkript: `szkriptek/motor_reelemzes_17.py` (A–F szekciók;
  futtatás a munkaterület gyökeréből: `python3 szkriptek/motor_reelemzes_17.py`).
- Kazetta-MD5-ök: `kazettak/MD5SUMS.txt` (v0.6.5 `1162414c…`,
  v0.9.2 `6f5fc138…`) — a vizsgálat során ellenőrizve, változatlanok.
- ROM-referencia: `refs/zx81.rom` (8192 B) + `refs/zx81rom.txt`
  (Logan & O'Hara, DISPLAY-3/4/5: 0292/02A9/02B5, NMI: 0066, INT: 0038,
  SLOW: 0F2B, SET-FAST: 02E7).
- A régi `trap_disasm.py` értelmezése megerősítést nyert; a z80dis.py
  DD/FD-prefix utasításoknál 1 bájtos túlfogyasztást mutat (pl. `FD E5`
  után; a nyers bájt-sort mindig vele együtt olvasni) — a jelentés minden
  DD/FD-es sorát nyers bájtokból igazoltam.
