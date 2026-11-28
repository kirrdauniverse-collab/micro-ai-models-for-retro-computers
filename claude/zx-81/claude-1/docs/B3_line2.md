# B3 javítás: a 2. BASIC-sor (RAND USR 16514)

A jelenlegi sor (11 B törzs): `F9 D4 C5 0B 1D 22 21 1D 20 0B 76`  → hibás.
Javított sor (14 B törzs):   `F9 D4 1D 22 21 1D 20 7E 00 00 82 40 00 76`

Sorfejléc: `00 02` (sorszám) + `0E 00` (hossz 14, little-endian).

Lépések a képépítőben (`tools/t81build16.py`):
1. A 2. sor törzsének cseréje a fenti 14 bájtra.
2. A 2. sor után a kitöltő nullák közül 3 törlése (a képben 71 nulla van a sor és a
   modell `$7000` címe között, ezért a modell címe nem változik).
3. A rendszerváltozókat NEM kell módosítani, ha a 3 bájt a nullákból jön le (a
   VARS / D_FILE címek nem mozdulnak). Ellenőrizni kell, hogy a VARS (`$7E19`) és a
   D_FILE (`$7B00`) változatlan maradt.

Megjegyzés: a 2. sor törzsét a 16K-s képben a `$6FA9`-es környéken találod (fájl-offset
`0x2FA0`). A `0x76`-os sorvégi bájt után a második `0x76` üres sort jelent, azt hagyni kell.
