# BREAKPOINT — glm-3 (zx-81) fejlesztési állapot

Dátum: 2026-11-28. Példány: GLM-3 (GLM / z.ai). Munkaterület: `glm/zx-81/glm-3/`.

**ÁTADÁS (2026-11-28):** a tulajdonos döntése szerint a fejlesztés a **v0.6.5-ös
ALAPFÁJL**-ról folytatódik (re-vizsgálat), az aktuális fej a **v0.9.2**; minden
más verzióanyag az `archive/` alá került (`git mv`, bájazonosan, semmi törlés).
A teljes átadás — döntés, bizonyítéklánc, örök szabályok, munkarend:
**`ATADASI_DOKUMENTUM.md`** (innen indulj).

## Hol tartunk

- **ALAPFÁJL:** `kazettak/GLM_PicoAI_v0.6.5_kazetta.T81`
  (MD5 `1162414c907f7a0b13c5cc2b4999c0de`, 227 923 B) — a változatlan tünet
  kiindulója.
- **Aktuális fej:** `kazettak/GLM_PicoAI_v0.9.2_kazetta.T81`
  (MD5 `6f5fc138e66e2ccdd52b982fffdb9003`, 227 923 B, 15 blokk).
  **ÉLŐ EO-PRÓBÁJA FÜGGŐBEN:**
  A) fagyás/csík nélkül megjelenik-e a profilkérdés;
  B) az RTBASE16 lánc-betöltés után elindul-e a chat;
  C) /quit viselkedése.

## Miért a v0.6.5 az alapfájl (rövid bizonyítéklánc)

1. 9. menet ÉLŐ próba (v0.6.5): betöltés + profilkérdések OK → az RTBASE16
   blokk után grafikus karakterek, a felső sor kiúszik, fehér kép, PC = $004x.
2. 10. menet ÉLŐ próba (v0.8.0, a 45 bájtos jelző-javítás után): a felhasználó
   szavaival *„Semmi se változott, ugyanaz a hiba"* — a tünet v0.6.5→v0.8.0
   között változatlan maradt, miközben az MD5 megváltozott.
3. A v0.9.1-es „fekete csíkos" tünet ugyanennek a `$7AE0`-s farokcsapda-
   családnak a folytatása; az RTBASE16 lánc-lépés élőben SOHA nem ment el.

## Következő lépések

1. **Re-vizsgálat a v0.6.5 alapfájlról:** a `$7AE0–$7AE5` farokcsapda és az
   RTBASE16-lánc utasítás-szintű követése élő EO-ban, a v0.9.2-vel összevetve.
   Első konkrét lépés: a v0.6.5 15. (motor-) blokkjának disassembly-ja
   `trap_disasm.py`-nal, a `$7AE0` környezetében.
2. **A v0.9.2 élő EO-próbája** (A/B/C fent) — a felhasználónál.
3. retro-tinyllm CI („line1 is not REM") — a ChatGPT-vonal ügye, nem glm-3;
   javításhoz a `t81modular_build.py` + checker forrása kell.

## Előírások (forenszikai szabályok)

- A v0.6.5 és a v0.9.2 kazetta az összevetés lezárásáig **NEM módosítható**.
- Az archív elemek (`archive/`) visszavételével dolgozni csak új
  verziószámmal, másolatként szabad — az eredeti érintetlen marad.
- A ChatGPT-vonal párhuzamos vizsgálata: `chatgpt/zx-81/chatgpt-1/` (központi
  repó; előzmény: a régi repo `CHATGPT1/BREAKPOINT.md`, AI16 vs R3) — nem
  keverendő a glm-3 vonallal; hivatkozás csak pontos útvonallal.
- Írás kizárólag a `glm/zx-81/glm-3/` könyvtárban (tulajdonosi utasítás).
- További részletek: `ERROR_AND_REPAIR_LOG.md` (hibák + javítások),
  `allapot/STATE.md` (menetnaplók, 1–16. menet).
