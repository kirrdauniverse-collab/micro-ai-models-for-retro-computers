# GLM STATE — következő menetnek

```yaml
project: "ZX81 AI micro language modell (Pico AI)"
repo_dir: /home/z/my-project/GLM/repo
repo_remote_name: "ZX81 AI micro language modell"
github_account: kirrdauniverse-collab
github_push: "nincs hozzáférés a sandboxból — git bundle + publish.sh a repó gyökerében"
phase: "3. fázis KÉSZ: motor lefordul + ZX81PICO.T81 elkészült és fut a szimulátorban; 4. fázis = futásidejű hibakeresés (lásd status_v2 + next_steps)"
current_version: v0.1.0-dev

# --------------------------------------------------------------- ÁLLÁS
status_summary: |
  A motor teljes Z80 forrása elkészült és a saját assemblerrel LEFORDUL:
  7243 bájt, org=0x4082, vég=0x5CCD (parancs:
  python3 tools/asm.py engine/main.z80 -o engine/build/engine.bin).
  A szótár (2560 B) és a 3 PK01 tudáscsomag (base/astronomy/science)
  a tools/kbtrain.py-vel legenerálva: engine/build/ alatt.
  AMI MÉG KELL (következő menet): build_t81.py megírása/összekötése,
  szimulátoros futtatás + hibajavítás, boot.z80, dist/ZX81PICO.T81,
  demo-átirat, archaeo.py, bundle frissítése.

next_steps:
  1: "tools/build_t81.py: engine.bin + dict.bin + <téma>.pk -> EO81/.P/.T81
      képek (a docs/03_formatumok.md és a régi t81build16.py receptje
      szerint: sysvars 116 B, 1 REM <kód>, 2 IF USR.. LOAD, 3 IF USR.. SAVE,
      4 RAND USR; SHORT kép 0x7120-ig, FULL a D_FILE-fal 0x7E19+1-ig;
      a NAMESLOT DW (0xDEAD 0xB1 0x5C bűnjel-párra keresve) patchelése
      a 2-es sor név-mezőjének címére)"
  2: "engine/boot.z80: PICOBOOT blokk (splash + útmutató + profil) — a
      main.z80 ask_profile-ja már megvan, a boot ugyanezt hívja"
  3: "szimulátoros teszt: python3 tools/zx81sim.py <t81> --script ...;
      a D_FILE-őrszem minden írást ellenőriz; várhatóan néhány futásidejű
      hiba (regiszter-menti), a naplóval (a .lst) kereshető"
  4: "docs/02 D_FILE-szabály + config.z80 címek maradéka: a képernyő-őrszem
      betesztelése élesben"
  5: "dist/ANYAGOK: ZX81PICO.T81 + .P fájlok + demo átirat a download/-ba"

engine_status:
  assembles: true
  size_bytes: 7243
  memory_map_v01:
    code: "0x4082-0x5CCD (7243 B)"
    dict: "0x5F00-0x6900 (2560 B: HI 0x5F00, FL 0x6000, OF 0x6100, ST 0x6300)"
    kb: "0x6900-0x7120 (2084 B hely — a base csomag 2016 B ✓)"
    reserve: "0x7120-0x7160 (64 B)"
    learn: "0x7160-0x73E0 (640 B)"
    chat_ring: "0x73E0-0x7A60 (~1,7 KB)"
    dfile: "0x7B00 (793 B)"
    vars_end: "0x7E19 VARS 0x80"
  modules:
    config.z80: kész
    tables.z80: kész (KEYCHR, ASCIIZX, WEEKTAB, NAMETAB, NAMESLOT-bűnjel)
    screen.z80: kész (putcell-őr, konzol, görgetés, think_bar)
    keys.z80: kész (8x5-ös szkenn + eseménydekódolás)
    state.z80: kész (6 bites csomagolás, RNG, óra, tanult-zóna, események)
    token.z80: kész (hash-keresés, toldalék, fuzzy, szám, tanult)
    gen.z80: kész (bigram-séta, hőmérséklet, reasoning, medencék, triggerek)
    date.z80: kész (hétköznap-számítás, óra, „hány napos vagyok")
    main.z80: kész forrásban (chat-ciklus, szerkesztő, gyűrű, BASIC-átadás)
    boot.z80: HIÁNYZIK (következő menet)
  known_gaps:
    - "futásidejű teszt még nem volt (a szimulátor kész, de nem futott rajta)"
    - "a bekészített getnum/gn_bs egyszerűsített (backspace csak kurzort léptet)"
    - "AGE_REPLY: a bot kora napokban; a felhasználó születési éve csak tárolódik"
    - "ring: rc_compact a felét dobja el; scroll 4 oldal (RINGPG max 3)"

hard_facts:   # ellenőrzött ZX81 tények — NEM változtatandók vakon
  image_base: 0x4009
  sysvars: {VERSN: 0x4009, E_PPC: 0x400A, D_FILE: 0x400C, DF_CC: 0x400E,
            VARS: 0x4010, DEST: 0x4012, E_LINE: 0x4014, CH_ADD: 0x4016,
            X_PTR: 0x4018, STKBOT: 0x401A, STKEND: 0x401C, BREG: 0x401E,
            MEM: 0x401F, LAST_K: 0x4021, DF_SZ: 0x4022, SPWORD: 0x4026,
            DFILE_COPY: 0x4029, FRAMES: 0x4034}
  rom: {CLS: 0x0A2A, SLOW: 0x0F2B, SET_FAST: 0x02E7, KEYBOARD: 0x02BB,
        DISPLAY: 0x0229, INPUT_CMD: 0x0EE9, LOAD: 0x0340, SCROLL: 0x0C0E}
  charset: {letters: "0x26-0x3F", digits: "0x1C-0x25", inverse_bit: 0x80,
            newline: 0x76, FORBIDDEN: "0x40-0x75, 0x77-0x7F, 0xC0-0xFF"}
  dfile: "793 B = 0x76 + 24*(32+0x76); sor r cellái: D_FILE+1+33*r"
  basic_line: "cimszam BE u16, hossz LE u16, torzs, 0x76; szam utan 0x7E+5B FP"
  eo81: "EO81 mágia; blokk: nev[32] + hossz[16 ASCII] + adat (kép 0x4009-től)"
  keyboard: "8x5 mátrix (rows FE..7F); SHIFT=15-ös nyers kód; RUBOUT=39;
             space = SHIFT+NEWLINE (motor-konvenció)"

key_tools:
  assembler: tools/asm.py        # mukodik, korutteszt zold
  simulator: tools/zx81sim.py    # selftest zold; chat-teszt kovetkezik
  trainer: tools/kbtrain.py      # mukodik: dict.bin + 3 csomag legeneralva
  builder: tools/build_t81.py    # NEM ESETT MEG MEG — kovetkezo menet
  archaeo: tools/archaeo.py      # nem keszult (a docs/04 diagnzis kesz)
```
