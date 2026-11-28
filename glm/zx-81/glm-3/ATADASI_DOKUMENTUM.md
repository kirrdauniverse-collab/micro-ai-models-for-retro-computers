# ÁTADÁSI DOKUMENTUM — glm-3 / zx-81

**Cél:** tiszta indulás a fejlesztéshez az új munkaterületen.
**Dátum:** 2026-11-28 · **Példány:** GLM-3 (GLM / z.ai) · **Munkaterület:**
`glm/zx-81/glm-3/` a `micro-ai-models-for-retro-computers` központi repóban.
**Előzmények:** migráció 2026-11-27 (`0b5f44a`); forrás:
`ZX81-AI-micro-language-model/GLM3` @ `aefdee3` (történeti példány,
`ATKÖLTÖZTETVE.md` jelzéssel — semmi nem törlődött).
**A tulajdonos e heti döntései:** ① az a modell legyen a folytatás alapja,
amitől kezdve a javítások gyanúsan hatástalanok voltak; ② a többit archiváljuk;
③ írás szigorúan csak a saját munkaterületemen.

---

## 1. A DÖNTÉS — melyik modelltől folytatunk

**ALAPFÁJL: `kazettak/GLM_PicoAI_v0.6.5_kazetta.T81`**
**MD5 `1162414c907f7a0b13c5cc2b4999c0de` · 227 923 bájt · 15 blokk**

Ettől a verziótól kezdve a javítások nem éreztették hatásukat — a tünet
változatlan maradt, miközben a kazetta bájtjai változtak:

| Lépés | Mit javítottunk | Élő eredmény |
|---|---|---|
| **v0.6.5** (9. menet) | — (az első .T81 újrakiadás a v0.5.4 levágási hibái után) | betöltés + profilkérdések OK → az RTBASE16 blokk után grafikus karakterek, a felső sor kiúszik, fehér kép, **PC = $004x** |
| v0.8.0 (10. menet) | 45 bájtos jelző-javítás (program-vég 0x76→0x80 + CH_ADD) | a tulajdonos szavaival: *„Semmi se változott, ugyanaz a hiba"* — ugyanaz a PC=$004x; az MD5 `d7f154b6…` ≠ `1162414c…`, tehát a fájl tényleg más lett, a viselkedés nem |
| v0.8.1 (11–12. menet) | `$7AE5: CA A9 02 → D3 FE FB` (OUT ($FE); EI) mind a 15 blokkban | önmagában sosem éles-tesztelve; a ráépülő v0.9.1 fekete csíkokat adott — az OUT(FE) sync-impulzust injektál a képsorba |
| v0.9.1 (13. menet) | 8 B név-prefix + bit7 terminátor + RTMEM16 blokk | *„Már az első blokk betöltésnél bevillanó fekete csíkok… és lefagy"* |
| v0.9.2 (14. menet) | `D3 → DB` (IN A,($FE)); RTMEM16 elhagyva | **élő próba FÜGGŐBEN** (A/B/C) |

**A minta:** három különböző „javítás" (jelző-bájt, OUT(FE), név-prefix) és négy
különböző MD5 — de az RTBASE16 lánc-lépés élőben **egyszer sem** ment el. A
közös gyökérajánló a motor `$7AE0`-s farokcsapda-családja (NMI-off ág → ROM
DISPLAY-5 örök NMI-várás). Ezért:

> **A fejlesztés innentől a v0.6.5-ös alapfájlról folytatódik, re-vizsgálattal
> (`$7AE0–$7AE5` + az RTBASE16-lánc utasítás-szintű követése élő EO-ban), a
> v0.9.2-vel összevetve.**

Hivatkozások: `ERROR_AND_REPAIR_LOG.md` 1–2. fejezet (teljes bizonyítéklánc),
`allapot/STATE.md` 9–10. menet (az élő próbák szó szerinti jegyzőkönyve).

## 2. Az archiválás — mi mozdult hová (2026-11-28)

A döntés szerint az ALAPFÁJL (v0.6.5) és az AKTUÁLIS FEJ (v0.9.2) maradt
aktív; minden más verzióanyag az `archive/` alá került **`git mv`-vel — semmi
nem törlődött, a tartalom bájazonos** (8/8 kazetta MD5+méret ellenőrizve a
mozgatás előtti friss méréshez; kártya: `archive/MD5SUMS.txt`).

| Régi hely | Új hely | Mi |
|---|---|---|
| `kazettak/GLM_PicoAI_v0.7.1_kazetta.T81` | `archive/kazettak/` | „4/2" OUT OF RAM (assembly-vonal) |
| `kazettak/GLM_PicoAI_v0.7.2_kazetta.T81` | `archive/kazettak/` | ismét „4/2" |
| `kazettak/GLM_PicoAI_v0.7.3_kazetta.T81` | `archive/kazettak/` | VISSZAVONVA — hibás tokenek (FOR/PLOT) |
| `kazettak/GLM_PicoAI_v0.8.0_kazetta.T81` | `archive/kazettak/` | a változatlan tünet második bizonyítéka |
| `kazettak/GLM_PicoAI_v0.8.1_kazetta.T81` | `archive/kazettak/` | OUT(FE)-csapdapatch (sosem önállóan éles-tesztelve) |
| `kazettak/elozmenyek_v0.7.0_elott/` (13 fájl) | `archive/elozmenyek_v0.7.0_elott/` | `ZX81PICO.T81` (v0.7.0), `PICOBASE/PICOASTR/PICOSCIN .p`, korábbi naplók, v0.1-dev bundle |
| `forraskod_csomagok/GLM_PicoAI_v0.7.1…v0.9.0_…zip` (6 zip) | `archive/forraskod/` | az archivált verziók forráscsomagjai |

**Aktív maradt:** `kazettak/` = v0.6.5 (ALAPFÁJL) + v0.9.2 (aktuális fej) +
`MD5SUMS.txt` (két soros kártya); `forraskod_csomagok/` = a v0.6.5-ös
forráscsomag. Korrekció a leltárhoz: a forrászip-sorozat valójában
**v0.6.5→v0.9.0-ig** terjed (7 zip); a **v0.9.2-hez nincs külön zip** — annak
forrása a `motor_v090/` + `szkriptek/build_v092.py` útvonal (ez az élő
build-módszer). Az archívumban semmi nem „rossz" — csak nem ez az aktív vonal;
bármelyik elem visszavehető, ha a vizsgálat kéri.

## 3. Verziótörténet egy táblázatban (sors jelöléssel)

| Verzió | MD5 | Élő EO-próba | Sors |
|---|---|---|---|
| v0.4.5 | `rt16_base.p` (.P-korszak, nem maradt meg) | **MŰKÖDÖTT** — az utolsó megerősített | elveszett |
| v0.5.0–0.5.4 | nem maradt meg | reset / „részben használható" | elveszett (GLM-2-vonal) |
| v0.7.0 | `d261a543…` (`ZX81PICO.T81`, 39 009 B) | fehér képernyő (RAMTOP a LAST-K címre írva) | archív |
| v0.7.1 | `160b23b5…` (39 009 B) | „4/2" OUT OF RAM | archív |
| v0.7.2 | `8f7025f1…` (38 433 B) | ismét „4/2" | archív |
| v0.7.3 | `fae28855…` (38 433 B) | VISSZAVONVA (hibás tokenek) | archív |
| v0.8.0 | `d7f154b6…` (227 923 B) | „ugyanaz a hiba" (PC=$004x) | archív |
| v0.8.1 | `abbf6344…` (227 923 B) | sosem önállóan tesztelve | archív |
| v0.9.0 | kazetta nem maradt meg (zip megvan) | 0/0 elcsúszva + sötét négyzet | archív (zip) |
| v0.9.1 | kazetta törölve a kézbesítésből | fekete csíkok + fagyás | nincs |
| **v0.6.5** | **`1162414c…` (227 923 B)** | **a változatlan tünet alapfájlja** | **AKTÍV ALAPFÁJL** |
| **v0.9.2** | `6f5fc138…` (227 923 B) | függőben (A/B/C) | **AKTÍV FEJ** |

## 4. Az örök szabályok és buktatók (új menet előtt kötelező olvasmány)

1. **`EO81` mágia** a fájl elején — nélküle az EightyOne elutasítja a fájlt.
2. Blokk szerkezete: `[32 B név \0-pad][16 B ASCII hossz \0-pad][kép 0x4009-től]`;
   az EO az adat végét az utolsó 0x80-as bájtig vágja vissza; blokkonként
   5000 ms pause.
3. **Gépi kód csak REM (0xEA) után állhat**, FOR (0xEB) után soha (v0.7.3 lecke).
4. **Szöveget csak PRINT (0xF5) ír**; a PLOT (0xF6) csak pontot rajzol
   (v0.7.3 lecke).
5. **RAMTOP = 0x4004** — a 0x4026 a LAST-K címe! (v0.7.0 lecke: a NEW RAM-FILL
   letörölte a teljes 16K-t.)
6. Az E_LINE–RAMTOP közti munkaterület méretezése döntő (v0.7.1–0.7.2 „4/2"
   OUT OF RAM leckéje).
7. **8 bájtos kazettanév-prefix bit7-terminátorral blokkonként** — a hiánya
   8 bájtos elcsúszást ad (v0.9.0 lecke); a blokknév utolsó bájtjának bit7=1
   kell legyen (v0.9.1 RTMEM16 leckéje: 0x22 vs 0xA2).
8. **Ne írj a $FE portra feltétel nélkül a farokcsapdában** — az EO-ban
   sync-impulzust injektál az aktuális képsorba (v0.9.1 fekete-csík lecke);
   az `IN A,($FE)` olvasás biztonságos (v0.9.2 megoldása).
9. A helyes ZX81 token-tábla: `dokumentacio/GLM_PicoAI_v0.8.0_valtozas_attekintes.txt`
   (a build_t81.py konstansai OCR-sérültek voltak — v0.7.3 lecke).
10. Kulcstény: az **RTBASE16 lánc-lépés élőben soha nem ment el** — minden
    eddigi javítás ezt az utat célozza; enélkül nincs chat.

## 5. Környezet, eszközök, nyilvántartások

- **Toolchain:** `toolchain/GLM_z88dk_2.5_zx81_toolchain.tar.gz` (z88dk 2.5 +
  SDCC 4.2, zx81 clib). Építés: `python3 szkriptek/build_v092.py` — a
  szkriptek a fejlesztő-sandbox abszolút útvonalait használják
  (`/home/z/my-project/...`); más környezetben a fejlécekben átírandók.
- **Ellenőrzés/diagnosztika:** `szkriptek/verify_*.py`, `tape_blocks_report.py`,
  `diff_cassets.py`, `trap_disasm.py`, `z80dis.py`, `rom_cdf.py`,
  `rom_regions.py`, `romsim_*`, `load_diag*.py`; ROM-hivatkozás: `refs/`
  (hiteles 8K ROM + disassembly).
- **Régi eszközök:** `eszkozok_regi_repo/` (asm.py, build_t81.py, zx81sim.py,
  t81_validate.py, kbtrain.py).
- **Nyilvántartások (mozgatás utáni állapot):** `TELJES_LELTAR.txt`
  (197 fájl / 30 566 918 bájt, méret+MD5), `SHA256SUMS.txt`,
  `kazettak/MD5SUMS.txt` (aktív: 2 kazetta), `archive/MD5SUMS.txt` (24 fájl /
  3 593 321 bájt), `PROJECT_INDEX.md`, `MIGRATION_MANIFEST.md` /
  `MIGRATION_STATUS.md`, `allapot/STATE.md` (1–16. menet),
  `ERROR_AND_REPAIR_LOG.md`, `BREAKPOINT.md`.

## 6. Munkarend (a tulajdonos utasításai alapján)

- Írás **kizárólag** a `glm/zx-81/glm-3/` könyvtárban. A glm-1 / glm-2 és
  minden más modell vagy gép területe tiltott.
- Más munkájára csak pontos útvonallal + verzióval hivatkozunk (pl. a
  ChatGPT-vonal: `chatgpt/zx-81/chatgpt-1/`).
- Új fejlesztés mindig **új verziószámmal**; a v0.6.5 és a v0.9.2 kazetta az
  összevetés lezárásáig nem módosítható.
- A régi repó (`ZX81-AI-micro-language-model`) történeti példány — a
  munkaterület már mindent tartalmaz, oda már nem is kell visszatérni.

## 7. Nyitott kérdések és a KÖVETKEZŐ MENET

1. **Re-vizsgálat a v0.6.5 alapfájlról:** a `$7AE0–$7AE5` farokcsapda és az
   RTBASE16-lánc utasítás-szintű követése élő EO-debuggerben, a v0.9.2-vel
   összevetve. Első konkrét lépés: a v0.6.5 15. (motor-) blokkjának
   disassembly-ja `trap_disasm.py`-nal, a `$7AE0` környezetében.
2. **A v0.9.2 élő EO-próbája** (a tulajdonosnál): A) fagyás/csík nélkül
   megjelenik-e a profilkérdés; B) az RTBASE16 után elindul-e a chat;
   C) /quit viselkedése.
3. retro-tinyllm CI („line1 is not REM") — a ChatGPT-vonal ügye, nem glm-3.

## 8. A tulajdonosi utasítások nyoma (idézetekkel)

- Élő próbák (9. és 13. menet): *„Semmi se változott, ugyanaz a hiba"*;
  *„Már az első blokk betöltésnél bevillanó fekete csíkok… és lefagy"* — a
  tünet-állandóság kulcsbizonyítékai.
- 2026-11-28: *„keresd meg azt a modellt, amítől kezdve gyanúsan nem voltak
  hatásai a javításoknak és azzal fogjuk folytatni. A többit archiváld!"* →
  v0.6.5 ALAPFÁJL + archiválás (1–2. fejezet).
- 2026-11-28: *„csak a te munkakönyvtáradban szigorúan!"* → 6. fejezet
  munkarend.

**Átadás vége — innen tiszta lappal indítható a fejlesztés. Első lépés: a
7. fejezet 1. pontja.**
