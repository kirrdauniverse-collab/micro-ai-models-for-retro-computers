# PROJECT_INDEX.md – claude/zx-81/claude-1

## Bináris fájlok (binaries/)

### T81 kazettafájlok (EightyOne emulátorhoz)
| Fájl | Leírás | Állapot |
|---|---|---|
| ZXAI_v3_...B2fix.t81 | B2 javítás, 16K verzió | Fut, "no model" |
| ZXAI_v4_...t81 | B2+charset javítás | Display hiba |
| ZXAI_v5_...B2CS.t81 | B2+charset, v2_root alapon | Fut, "no model" |
| ZXAI_v6_...t81 | Modell eltolás (+2 bájt) | Lefelé szaladó nullák |
| ZXAI_v7_...t81 | B2 (csak 2 bájt), 16K alap | Fut, "no model" majd fehér |
| ZXAI_v8_...t81 | B2+SLOW trampoline | Azonnal display hiba |
| ZXAI_v9_...t81 | B2+IY-safe trampoline+B3 | Tesztelés alatt |

### P fájlok (közvetlen betöltés)
Minden t81-hez tartozó .p fájl: az RTCHAT blokk nyers képe.

## Referencia (reference/)
| Fájl | Tartalom |
|---|---|
| engine/rt_model.c | Modell betöltő – B2 hiba itt van (len=0x0B00) |
| engine/rt_engine.c | Forward pass: embed+hidden+output |
| engine/rt_charset.c | 45 karakteres szótár |
| hal_zx81.c | Billentyűzet, D-file írás, panic handler |
| app16.c | Főprogram (rt_app_boot+rt_app_run) |

## Modell (models/)
| Fájl | Leírás |
|---|---|
| base_f.bin | RTLM v2, vocab=45, ctx=8, emb=10, h1=16, h2=0, 2666B, chk=0xEB9D |

## Eszközök (tools/)
| Fájl | Leírás |
|---|---|
| verify_findings.py | Ellenőrzi a ROM rutinokat, modell fejlécet, checksumot |

## Ismert ROM rutinok
| Cím | Rutin | Ellenőrizve |
|---|---|---|
| 0x0F23 | FAST (NMI ki) | Igen |
| 0x0F28 | SLOW (NMI be) – helyes belépés | Igen |
| 0x0F2B | NEM belépés – utasítás közepe | Igen |
| 0x02BB | Keyboard scan (LAST_K → 0x4028) | Igen |
| 0x0010 | PRINT-A (RST 10h) | Igen |
