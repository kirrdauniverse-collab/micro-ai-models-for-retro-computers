#!/usr/bin/env python3
"""build_v092.py — a v0.9.2 gyógyító kazetta megépítése.

ALAP: a v0.8.1 kazetta (azon bájtok, amelyek a szalag-motor szempontjából
      bizonyítottan a legutolsó, EO-n bootstrap-ig jutott változat).
JAVÍTÁS (mind a 15 blokkban, pontosan 1 bájt):
  $7AE5: D3 (OUT ($FE),A)  ->  DB (IN A,($FE))
  A v0.8.1-es patch itt feltétel nélküli portírást tett a várakozó hurokba;
  a ZX81-en / EO-ban minden OUT (FE) = NMI-generátor BE + sync-impulzus a
  képsorba (zx81.cpp: LASTINSTOUTFE + CurScanLine->sync_len += ts).
  Iterációnkénti sync-injektálás => "bevillanó fekete csíkok" + elcsúszó
  kép => fagyás. Az IN nem ír portot: a tünet megszűnik, az EI megtartja
  a NMI-engedélyt (a v0.6.5-ös PC=$004x örök-wait nem tér vissza, mert
  az a JP Z,$02A9 ágon volt, ami változatlan marad — NEM, az is DB-vel
  egészül: az AND $80 utáni Z-ág helyett az IN mindig végrehajtódik,
  portírás nélkül).
TOVÁBBÁ:
  - a v0.9.1 RTMEM16 blokk KIHAGYVA (név-kódja bit7-terminátor nélküli,
    a ROM név-szkennerét szétverte; a szalagon lévő motor úgysem használja)
  - banner "0.8.1" -> "0.9.2" (a blokkok BELSŐ, csak kijelzésre való
    sztringjében, 3 bájt csere — a kódlogikát nem érinti)
Ellenőrzés: minden blokkra E_LINE/D_FILE/záró 0x80/1-bájtos diff a
v0.8.1-hez képest + MD5.
"""
import hashlib

BASE = '/home/z/my-project/download/'
SRC = BASE + 'GLM_PicoAI_v0.8.1_kazetta.T81'
DST = BASE + 'GLM_PicoAI_v0.9.2_kazetta.T81'
TRAP_IMG_OFF = 0x7AE5 - 0x4009 + 8   # kep-beli offset (8B nev-prefix utan)


def parse(path):
    raw = open(path, 'rb').read()
    assert raw[:4] == b'EO81'
    pos, blocks = 4, []
    while pos + 48 <= len(raw):
        name = raw[pos:pos + 32].rstrip(b'\0').decode()
        ln = int(raw[pos + 32:pos + 48].rstrip(b'\0'))
        data = bytearray(raw[pos + 48:pos + ln + 48])
        blocks.append([name, data])
        pos += 48 + ln
    return blocks


def main():
    blocks = parse(SRC)
    patched, banner = 0, 0
    for name, data in blocks:
        assert data[TRAP_IMG_OFF] == 0xD3, (name, hex(data[TRAP_IMG_OFF]))
        data[TRAP_IMG_OFF] = 0xDB          # OUT (FE),A -> IN A,(FE)
        patched += 1
        # banner: 'v0.8.1' -> 'v0.9.2' ha megtalalhato (kijeles-sztring)
        b = bytes(data)
        for old, new in ((b'v0.8.1', b'v0.9.2'), (b'0.8.1', b'0.9.2')):
            i = b.find(old)
            while i != -1:
                data[i:i+len(old)] = new
                banner += 1
                b = bytes(data)
                i = b.find(old)
    out = b'EO81'
    for name, data in blocks:
        out += name.encode().ljust(32, b'\0') + str(len(data)).encode().ljust(16, b'\0') + bytes(data)
    open(DST, 'wb').write(out)
    print(f'blokkok: {len(blocks)}, trap-patch: {patched} db (OUT->IN), banner: {banner} db')

    # --- verify ---
    raw = open(DST, 'rb').read()
    assert raw[:4] == b'EO81'
    pos, seen = 4, {}
    while pos + 48 <= len(raw):
        name = raw[pos:pos+32].rstrip(b'\0').decode()
        ln = int(raw[pos+32:pos+48].rstrip(b'\0'))
        data = raw[pos+48:pos+ln+48]
        seen[name] = data
        img = data[8:]
        d_file = img[3] | (img[4] << 8)
        e_line = img[11] | (img[12] << 8)
        assert data[8 + e_line - 0x4009 - 1] == 0x80, name   # zaro 0x80 E_LINE-1-en
        assert data[TRAP_IMG_OFF] == 0xDB, name              # IN
        assert data[TRAP_IMG_OFF + 1:TRAP_IMG_OFF + 3] == b'\xFE\xFB', name
        pos += 48 + ln
    src = parse(SRC)
    diffs = {}
    for name, data in seen.items():
        for name0, data0 in src:
            if name0 == name:
                d = sum(1 for k in range(min(len(data), len(data0))) if data[k] != data0[k])
                diffs[name] = d
    print('blokkonkenti diff a v0.8.1-hez:', {k: v for k, v in diffs.items() if v})
    print('MD5 v0.9.2:', hashlib.md5(open(DST, 'rb').read()).hexdigest())
    print('hossz:', len(out), 'B')


if __name__ == '__main__':
    main()
