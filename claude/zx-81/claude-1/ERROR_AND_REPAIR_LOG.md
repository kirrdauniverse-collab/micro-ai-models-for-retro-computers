# ERROR_AND_REPAIR_LOG.md – claude/zx-81/claude-1

## B1 – SLOW hívás rossz cím
- **Hely:** 48K GLM kép, 0x40BE: `CALL 0x0F2B`
- **Ok:** 0x0F2B a SLOW rutin közepe, nem belépési pontja
- **Javítás:** `CALL 0x0F28`
- **Állapot:** Az eredeti 16K kódban is `CALL 0x0F2B` van, de az emulátor ezzel együtt fut

## B2 – Modell betöltő rossz hossz → "no model - bad cassette"
- **Hely:** 16K verzió, 0x4FE8-0x4FEA: `LD HL, 0x0B00` (2816)
- **Ok:** Modell valódi mérete 2666 (0x0A6A), checksum ezért nem egyezik
- **Javítás:** 0x4FE9=0x6A, 0x4FEA=0x0A (`LD HL, 0x0A6A`)
- **Állapot:** JAVÍTVA v7-től. A model checksum (0xEB9D) egyezik.

## B3 – 2. BASIC sor hibás → STOP (9/2)
- **Hely:** 0x6FA9: `F9 D4 C5 0B 1D 22 21 1D 20 0B 76` (len=11)
- **Ok:** Hiányzó 0x7E szám-marker, érvénytelen tokenek
- **Javítás:** `F9 D4 1D 22 21 1D 20 7E 00 00 82 40 00 76` (len=14), EOP=0x76 eltolva
- **Állapot:** JAVÍTVA v9-ben

## B4 – Charset eltolás
- **Hely:** Modell charset (model+28): `\n abc...` vs engine: ` abc...`
- **Ok:** Az első karakter különböző (0x0A vs 0x20)
- **Javítás:** Modell charset felülírva engine charsettel, checksum újraszámolva
- **Állapot:** Egyes verziókban alkalmazva, de mellékhatásokat okozott

## B5 – D-file / display azonnal kiakad (T81 betöltéskor)
- **Hely:** Minden általunk gyártott T81 változat
- **Ok:** Nem tisztázott. Lehetséges okok:
  1. A SLOW/FAST trampoline (CALL 0x0F28) a ROM display scan rutinba ugrik ami IY-t igényel
  2. Az engine D-file cursor inicializálása hibás (0x422D=0 → ROM területre ír)
  3. Az EightyOne T81 betöltője eltérő offset-en tölti a payloadot
- **Állapot:** NYITOTT – a legfontosabb megoldandó probléma

## B6 – v2_root.t81: modell cím eltolás
- **Hely:** v2_root képben RTLM a 0x6FFE-n, de engine 0x7001-et keres (D_FILE=0x7B01 → 0x7B01+0xF500=0x7001)
- **Javítás:** RTLM +2 bájttal eltolva (0x7000-re), D_FILE=0x7B00
- **Állapot:** Alkalmazva v6-ban, de más hibákat okozott

## Tanulságok
- Az eredeti rt16_topics.t81 (Gemini/GLM build) az EightyOne-ban fut, "no model" hibát ad de nem crashel
- Minden bináris módosítás újabb hibát okozott
- A display inicializálás és a T81 betöltés pontos mechanizmusa még nem teljesen feltárt
- A ZX81 motor forráskódja (C) nem egyezik az emulátor viselkedésével sysvar kezelés terén
