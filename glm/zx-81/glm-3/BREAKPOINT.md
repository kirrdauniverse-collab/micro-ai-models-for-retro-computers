# BREAKPOINT — glm-3 (zx-81) fejlesztési állapot

Dátum: 2026-11-27. Példány: GLM-3 (GLM / z.ai). Munkaterület: `glm/zx-81/glm-3/`.

## Hol tartunk

- Legfrissebb kazetta: `kazettak/GLM_PicoAI_v0.9.2_kazetta.T81`
  (MD5 `6f5fc138e66e2ccdd52b982fffdb9003`, 227 923 B, 15 blokk).
  **ÉLŐ EO-PRÓBÁJA FÜGGŐBEN:**
  A) fagyás/csík nélkül megjelenik-e a profilkérdés;
  B) az RTBASE16 lánc-betöltés után elindul-e a chat;
  C) /quit viselkedése.

## Előírt kiindulópont a re-vizsgálathoz

Alapfájl: **`kazettak/GLM_PicoAI_v0.6.5_kazetta.T81`**
(MD5 `1162414c907f7a0b13c5cc2b4999c0de`, 227 923 B). Ettől a verziótól maradt
a hibajelenség változatlan a javítások ellenére:

1. 9. menet ÉLŐ próba (v0.6.5): betöltés + profilkérdések OK → az RTBASE16
   blokk után grafikus karakterek, a felső sor kiúszik, fehér kép, PC = $004x.
2. 10. menet ÉLŐ próba (v0.8.0, a 45 bájtos jelző-javítás után): a felhasználó
   szavaival *„Semmi se változott, ugyanaz a hiba"* — a tünet v0.6.5→v0.8.0
   között változatlan maradt.
3. A v0.9.1-es „fekete csíkos" tünet ugyanennek a `$7AE0`-s farokcsapda-
   családnak a folytatása; az RTBASE16 lánc-lépés élőben SOHA nem ment el.

## Következő lépések

1. **Re-vizsgálat a v0.6.5 alapfájlról:** a `$7AE0–$7AE5` farokcsapda és az
   RTBASE16-lánc utasítás-szintű követése élő EO-ban, a v0.9.2-vel összevetve.
2. **A v0.9.2 élő EO-próbája** (A/B/C fent) — a felhasználónál.
3. retro-tinyllm CI („line1 is not REM") — a ChatGPT-vonal ügye, nem glm-3;
   javításhoz a `t81modular_build.py` + checker forrása kell.

## Előírások (forenszikai szabályok)

- A v0.6.5 és a v0.9.2 kazetta az összevetés lezárásáig **NEM módosítható**.
- A ChatGPT-vonal párhuzamos vizsgálata: `chatgpt/zx-81/chatgpt-1/` (központi
  repó; előzmény: a régi repo `CHATGPT1/BREAKPOINT.md`, AI16 vs R3) — nem
  keverendő a glm-3 vonallal; hivatkozás csak pontos útvonallal.
- Új fejlesztés mindig új verziószámmal; a bizonyítottan működő (v0.4.5
  volt az utolsó megerősített) és a kísérleti változatok szétválasztva
  (lásd `PROJECT_INDEX.md` tesztállapot-összefoglaló).
- További részletek: `ERROR_AND_REPAIR_LOG.md` (hibák + javítások),
  `allapot/STATE.md` (menetnaplók).
