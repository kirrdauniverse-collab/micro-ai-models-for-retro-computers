# Billentyűk és parancsok (v1.1.0)

## ZX81 billentyűzet a csevegőben

| Billentyű | Hatás |
|---|---|
| Betűk, számok, szóköz | beírás (csak a ZX81 karakterkészlete: nagybetűk, számok, `, . ? : - * + = ( ) > "`) |
| `ENTER` | a sor elküldése; a válasz a naplóban jelenik meg |
| `SHIFT+0` | DEL: utolsó karakter törlése |
| `SHIFT+8` | DEL: ugyanaz (tartalék, ha a Backspace más kódot ad) |
| `SHIFT+F` | GYORS mód BE/KI (alapértelmezés KI; a fejléc 2. sora mutatja) |
| `SHIFT+7` | görgetés felfelé (4 sor) |
| `SHIFT+6` | görgetés lefelé (4 sor) |
| `SHIFT+1` … `SHIFT+4` | hőmérsékleti szint (1 = hideg, 4 = meleg); alapértelmezés: 1 |
| `SHIFT+9` | gondolkodás (greedy) BE/KI; alapértelmezés: BE |
| `SHIFT+N` / `SHIFT+M` / `SHIFT+C` | `,` / `.` / `?` — a ZX81 billentyűzet szerinti írásjelek |

## Parancsok (a sor egészeként)

| Parancs | Hatás |
|---|---|
| `HELP` | a kézikönyv rövid változata |
| `NEW` | új beszélgetés: a modell kontextusa törlődik, a név és az esemény marad |
| `QUIT` | kilépés: az állapot mentődik, és a program BASIC-be tér vissza; mentés: `SAVE "RTCHAT"` |

## Kulcsszavak (a sorban bárhol)

| Szó | Hatás |
|---|---|
| `HEAD`, `PAIN` | fájdalom-esemény a mai nappal |
| `HAPPY` | öröm-esemény |
| `LOVE` | szerelem-esemény |
| `TIRED` | fáradtság-esemény |
| `RAIN`, `SUN` | WEATHER téma kérése (`LOAD "WEATHER"`) |
| `DOG`, `CAT` | ANIMALS téma kérése |
| `JOKE` | JOKES téma kérése |
| `NUMBER` | NUMBERS téma kérése |

Az esemény a következő indításkor 1–7 napon belül visszakérdez: `FAJ MEG A FEJED? (Y/N)`.
Az `N` válasz törli az eseményt.
