# MIGRATION_STATUS – claude-4

Állapot (2026-11-28): **a fájlok átmásolva és SHA-256-tal ellenőrizve (123 fájl).**
- Az átmásolt fa a helyi munkaterület pillanatképe. A v1.1.4 commit és a v1.1.6-diag módosítások is benne vannak (utóbbi még nem commitolt a helyi repóban).
- A régi helyen (`/home/claude/rt16/release`) minden érintetlen maradt; semmi nem lett törölve.
- A git-előzmény a `history_rt16_release.bundle` fájlban van (`git bundle verify` ellenőrzés javasolt).
- Hiányzik: a régi, GitHubon lévő `retro-tinyllm` (v0.6.4) munka – az más vonal, nem ennek a modellnek a munkája, nem költöztettem.
- Nem állítom, hogy a valódi gépen a lefagyás javított: lásd `ERROR_AND_REPAIR_LOG.md`.
