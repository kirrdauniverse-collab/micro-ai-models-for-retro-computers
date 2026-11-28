# B2 javítás: a modell-betöltő ellenőrző összege a modell méretére számoljon

Fájl: `reference/engine/rt_model.c` (ugyanez a logika lesz a B-útvonal betöltőjében).

## Mi a hiba
`rt_model_load(m, buf, len)` a `len` (= RT_APP_MODEL_MAX = 10240 a 16K-s Makefile-ban)
hosszára számolja az ellenőrző összeget, nem a modell valódi méretére (2666 B).
A tárolt összeg így rossz helyen van, és a betöltés `-7` kóddal bukik
(`app16.c:278` → "no model - bad cassette").

## Előtte (a checksum blokk)
```c
    { /* additive checksum over everything before the last two bytes */
        rt_u32 sum = 0;
        long n = len - 2;
        for (i = 0; i < n; i++)
            sum = (sum + p[i]) & 0xFFFFUL;
        if ((rt_u16)sum != rd16(p + n))
            return -7;
    }

    need = rt_model_size(&h);
    if (need > len)
        return -8;
```

## Utána
```c
    need = rt_model_size(&h);
    if (need > len)
        return -8;

    { /* additive checksum over the MODEL's own bytes: [0, need-2) */
        rt_u32 sum = 0;
        long n = need - 2;
        for (i = 0; i < n; i++)
            sum = (sum + p[i]) & 0xFFFFUL;
        if ((rt_u16)sum != rd16(p + n))
            return -7;
    }
```

## Ellenőrzés (nem futtattam emulátorban, a kredit miatt)
- `tools/verify_findings.py` Python-mása: a 2666 B-os blobra a számolt összeg 0xEB9D,
  a tárolt is 0xEB9D → PASS. A 10240 B-os hosszon 0xED25 vs 0x0000 → FAIL (a hiba).
- A C-fordításhoz z88dk kell (a 16K-s Makefile: `make -C ports/zx81`), ami ebben a
  környezetben nincs telepítve.
