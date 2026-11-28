# Cricket-81 (Claude-4) – ZX81 mikro-AI

Modell: Claude (Haiku 5.5), munkaterület: `claude/zx-81/claude-4`.
Gép: ZX81 16K. Cél: egy kis, int8-as nyelvi modell futtatása Z80 assemblyben, EightyOne emulátorban és valódi ZX81-en.

Név: **Cricket-81** (magyarul: tücsök-81). A fájlnevekben: `Cricket81_Claude-4_v<verzió>`.

## Fő komponensek
- `src/` – Z80 assembly (app1–app7, engine.asm). A build: `tools/make_dist.py`.
- `tools/` – build (`build_image.py`, `make_dist.py`), emulátor (`z80emu.py`), assembler (`z80asm.py`).
- `tests/` – emulátoros tesztek (regress.py, minimal/, nmi_*.py, loader_test.py).
- `dist/` – kész kimenetek (.P és .t81), verziónként.
- `models/`, `ref/` – modellfájlok és referencia-kimenetek.
- `CHANGELOG.md` – verziótörténet v1.0.0-tól.

## Állapot
Lásd `MIGRATION_STATUS.md` és `BREAKPOINT.md`.
