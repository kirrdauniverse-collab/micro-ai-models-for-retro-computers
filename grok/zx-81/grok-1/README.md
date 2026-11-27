# Grok-1 – Pico AI for ZX81

**Modellpéldány:** grok / zx-81 / grok-1
**Fejlesztő modell:** Grok (xAI)
**Gép:** Sinclair ZX81 (16 KB)

## Cél
Miniatűr nyelvi modell (Pico AI) futtatása 16 KB-os ZX81-en, multi-load .T81 kazettán.

## Jelenlegi állapot (2026-11-27)
- v0.6 a legfrissebb stabil próbálható verzió
- Strict ZX81 BASIC (egybetűs string változók, egy parancs/sor)
- 4 blokkos .T81: Loader + Model + Topic-Math + Topic-Colors
- Loader: robotos splash, adatok bekérése, RAMTOP + NEW
- Model: hangulat, thinking, egyszerű matek, színkeverés, ideiglenes tanulás

## Fő fájlok
- releases/v0.6/pico-ai-v0.6.t81 – aktuális kazetta
- kazettak/pico-ai-v0.6.t81 – ugyanez
- src/v0.6/ – források

## Következő lépés
A v0.6 tesztelése és a felmerülő hibák javítása.
