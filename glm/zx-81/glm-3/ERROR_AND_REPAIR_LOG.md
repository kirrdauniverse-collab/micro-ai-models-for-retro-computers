# Hiba- és javítástörténet — GLM-3 vonal (v0.5.4 → v0.9.2)

Megjegyzés: ez a dokumentum a régi munkahely (`ZX81-AI-micro-language-model/GLM3`)
`HIBA_ES_JAVITAS_TORTENET.md` fájljának átnevezett példánya (központi kötelező
sablon szerint; forrás: `aefdee3`). Összeállítva 2026-11-27, az
`allapot/STATE.md` 2–15. meneteiből és a `dokumentacio/` változásnaplóiból.
Minden kazetta MD5-e: `kazettak/MD5SUMS.txt`, SHA-256: `SHA256SUMS.txt`,
teljes leltár: `TELJES_LELTAR.txt`.

## 0. Kontextus: a konténer és a két örök szabály

- **.T81 konténer** (EightyOne forrásból, tzxload.cpp): fájl elején `EO81` mágia
  (KÖTELEZŐ — nélküle az emulátor elutasítja), blokkonként `[32 B név \0-pad]
  [16 B ASCII hossz \0-pad][kép 0x4009-től]`; az EO az adat végét az utolsó
  0x80-as bájtig vágja vissza; blokkonként 5000 ms pause.
- **Szabály 1:** gépi kód csak REM (0xEA) után állhat, FOR (0xEB) után soha.
- **Szabály 2:** szöveget csak PRINT (0xF5) ír; a PLOT (0xF6) csak pontot rajzol.
- **KULCSTÉNY:** az RTBASE16 lánc-betöltési lépés (boot után a chat-motor
  betöltése) élőben **soha nem ment el hibátlanul** — a teljes javítósorozat
  ezt az utat célozza.

## 1. Verziótáblázat — élő EO-próbákkal

| Verzió | Kazetta (MD5) | Élő EO-próba eredménye | Gyökérok → javítás |
|---|---|---|---|
| v0.4.5 | `rt16_base.p` (15 889 B, .P-korszak — nem maradt meg) | **MŰKÖDÖTT** — az utolsó felhasználó által megerősített változat | — |
| v0.5.0–0.5.3 | nem maradt meg | Reset / hibajelentések, egyiket sem erősítette meg működőként | — |
| v0.5.4 | nem maradt meg (GLM-2-vonal) | „Részben használható" | A nem-boot blokkok E_LINE-ja túllógott + az EO blokkonként 131–186 B-ot levágott (össz. 2092 B) → a v0.6.5 builder ezt javította |
| v0.6.5 | `1162414c907f7a0b13c5cc2b4999c0de` (227 923 B, 15 blokk) | Betöltés + profilkérdések OK; az RTBASE16 blokk után 2–3 grafikus karakter, a felső sor kiúszik, fehér kép, **PC = $004x** | A motor `$7AE0`-s farokcsapdája: NMI-off ág → ROM DISPLAY-5 örök NMI-várás → javítás v0.8.1 (OUT FE) → v0.9.2 (IN FE) |
| v0.7.0 | `kazettak/elozmenyek_v0.7.0_elott/ZX81PICO.T81` (39 009 B) | Intro után fehér képernyő | A boot ML a RAMTOP-ot a 0x4026-ra írta (= LAST-K!) → a NEW RAM-FILL-je letörölte a teljes 16K-t → javítás: RAMTOP EQU 0x4004 (v0.7.1) — assembly-vonal |
| v0.7.1 | `160b23b5c258b428bd37d021cbc96f3d` (39 009 B) | „4/2" hibakód (OUT OF RAM, a BASIC 2. során) | E_LINE (0x7100) és RAMTOP (0x715F) közt ~90 B → javítás: E_LINE 0x7040 + USR BC-visszatérés + IY=0x4000 + valódi billentyűmátrix (v0.7.2) |
| v0.7.2 | `8f7025f1a6fd25b7e2ddc326a0df20e9` (38 433 B) | Ismét „4/2" | A build_t81.py token-konstansai hibásak (OCR-sérült tábla) → javítás-kísérlet: v0.7.3 — HIBÁS |
| v0.7.3 | `fae288550aa51884df6560f7c260ef8b` (38 433 B) | **VISSZAVONVA** — használhatatlan | Minden blokk FOR (0xEB) tokennel indul (REM = 0xEA helyett), PRINT helyén PLOT (0xF6). A helyes token-tábla: `dokumentacio/GLM_PicoAI_v0.8.0_valtozas_attekintes.txt` |
| v0.8.0 | `d7f154b6130871c801c05a896ce71d18` (227 923 B) | **„Semmi se változott, ugyanaz a hiba"** — grafikus karakterek, fehér kép, PC = $004x (a felhasználó saját szavai, 10. menet) | patch_v080: a program-vég 0x76 → 0x80 + CH_ADD javítás (45 bájt). A javítás valós, de NEM a gyökérok: a $7AE0-csapda maradt |
| v0.8.1 | `abbf634478e97f7c0b44ebfd852c6a5b` (227 923 B) | Önmagában soha nem volt élesben tesztelve; az első éles próba a v0.9.1-en keresztül történt | patch_v081: `$7AE5: CA A9 02 → D3 FE FB` (OUT ($FE); EI) mind a 15 blokkban + banner. Utólag bizonyított: a feltétel nélküli OUT(FE) az EO sync-generátora |
| v0.9.0 | kazetta (230 281 B, 16 blokk) nem maradt meg; forráscsomag igen | 0/0 több sorral feljebb + sötét négyzet | A builderből hiányzott a 8 B-os kazettanév-prefix (bit7 terminátorral), 18 soros D-FILE-kísérlet, VARS-elrendezés → javítás: v0.9.1 = bizonyított v0.8.1-blokkok |
| v0.9.1 | kazetta törölve a kézbesítésből (bátonként rekonstruálható) | „Már az első blokk betöltésnél bevillanó fekete csíkok… és lefagy" | A v0.8.1-es OUT(FE)-patch + az RTMEM16 blokk név-kódjának hiányzó bit7-terminátora (0x22 vs 0xA2) |
| v0.9.2 | `6f5fc138e66e2ccdd52b982fffdb9003` (227 923 B, 15 blokk) | **FÜGGŐBEN** — A/B/C próba | `$7AE5: D3 → DB` (IN A,($FE) — nem ír portot, nincs sync-injektálás); RTMEM16 elhagyva; banner 0.9.2 |

## 2. A VÁLTOZATLAN TÜNET ALAPFÁJLJA — v0.6.5

**`kazettak/GLM_PicoAI_v0.6.5_kazetta.T81` (MD5 `1162414c907f7a0b13c5cc2b4999c0de`, 227 923 B)**

Bizonyítéklánc, hogy ettől a fájltól maradt a hibajelenség változatlan a
javítások ellenére:

1. **9. menet (v0.6.5 élő próba):** a betöltés és a profilkérdések lefutottak;
   a gép kérte a kazetta tekerését az RTBASE16 blokkhoz; ENTER után a blokk
   betöltött — majd 2–3 grafikus karakter, a legfelső sor kiúszása, fehér kép,
   PC $004x.
2. **10. menet (v0.8.0 élő próba):** a 45 bájtos jelző-javítás (0x76→0x80 +
   CH_ADD) után a felhasználó jelentése szó szerint: *„Semmi se változott,
   ugyanaz a hiba… beragadt a PC 004x tartományban."* — a tünet v0.6.5→v0.8.0
   között VÁLTOZATLAN maradt, miközben a kazetta bájtjai megváltoztak
   (MD5-ök különböznek: `d7f154b6…` vs `1162414c…`).
3. **13. menet:** a v0.9.1-es „fekete csíkos" tünet (első blokkra fagyás) ugyan-
   ennek a `$7AE0`-s farokcsapda-családnak a következménye — a v0.8.1-es
   „javítás" (OUT FE) új tünetet adott, nem orvoslást; a v0.9.2 (IN FE) vár a
   próbára. Az RTBASE16-lánc-lépés élőben soha nem ment el.

→ **Innentől a re-vizsgálat kiindulópontja a v0.6.5**, vele összevetve a
v0.9.2-t. Az EO-debuggerben a `$7AE0–$7AE5` (farokcsapda) és az RTBASE16
betöltése utáni PC-út követendő.

## 3. A tünetek családfája

- **PC = $004x örök-wait** (v0.6.5, v0.8.0): a motor `$7AE0`-s farokcsapdája
  NMI-off esetén a ROM DISPLAY-4 → DISPLAY-5 (`LD R,A / LD A,$DD / EI / JP (HL)`)
  útján örökké NMI-t vár.
- **Fekete csíkok + fagyás** (v0.9.1): a `$7AE5`-ös OUT ($FE) iterációnként
  sync-impulzust injektál az aktuális képsorba (EO-forrás: zx81.cpp,
  LASTINSTOUTFE) → soronkénti szinkron, széteső kép, fagyás.
- **Elcsúszott 0/0 + sötét négyzet** (v0.9.0): hiányzó 8 B-os kazettanév-prefix
  (a ROM LOAD a kép első 8 bájtját névként olvasta → 8 B elcsúszás) + a 18 soros
  D-FILE-kísérlet + rossz VARS-elrendezés.
- **„4/2" OUT OF RAM** (v0.7.1, v0.7.2): E_LINE és RAMTOP közti munkaterület-hiány.
- **Fehér képernyő** (v0.7.0): RAMTOP-írás a LAST-K címére → NEW RAM-FILL letörölt
  mindent.
- **Reset** (v0.5.0): tévesen törölt EO81-mágia → az emulátor nem ismerte fel a
  fájlt; ill. a szemét-adat a D_FILE-mutatóba került.
- **„Részben használható"** (v0.5.4): E_LINE-túllógás + az EO 2092 B-os levágása →
  IN-BYTE időtúllépés → INITIAL letakarította a program elejét.

## 4. Amit a ChatGPT-vonal párhuzamosan tett (nem keverendő)

- **A ChatGPT-vonal központi helye:** `chatgpt/zx-81/chatgpt-1/` (ez a központi
  repó; előzménye a régi `ZX81-AI-micro-language-model` repó `CHATGPT1/`
  könyvtára). Az ő BREAKPOINT-juk: az utolsó ismert-jó futás a
  `mistral_zx81ai16.t81` (AI16, HELLO-üdvözlésig jutott), az első tartós-hiba
  jelölt a `PICO_AI_R3_16K.t81` — ugyanaz az „alapfájl vs. utóda" módszertant.
- A retro-tinyllm repó CI-ja (`build-r5`, `PICO_BOOT_R5.p: line1 is not REM`)
  a ChatGPT-vonal R5 builderét érinti: a piros CI óta nem épül új R5-artefakt,
  ezért onnan tesztelni a régi fájlt jelenti (külső ok, nem modellhiba).
- A két vonal kazettái formailag eltérnek (R5: 7 blokkos kombinált szalag,
  GLM-3: 15 blokkos multi-load) — az eredmények összemérésekor ezt figyelembe
  kell venni.
