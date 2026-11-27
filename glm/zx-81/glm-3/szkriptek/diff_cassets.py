#!/usr/bin/env python3
"""diff_cassets.py — a v0.6.5 / v0.8.0 / v0.8.1 / v0.9.1 kazetták
blokkjainak bájtszintű összehasonlítása.

Cél: pontosan felsorolni, MIT változtattak a patch-ek a boot-blokkban,
és a v0.9.1 vs v0.8.1 eltérést (elméletileg csak a RTMEM16).
"""
import sys

BASE = '/home/z/my-project/download/'


def parse(path):
    raw = open(path, 'rb').read()
    assert raw[:4] == b'EO81', path
    pos, blocks = 4, {}
    order = []
    while pos + 48 <= len(raw):
        name = raw[pos:pos + 32].rstrip(b'\0').decode()
        ln = int(raw[pos + 32:pos + 48].rstrip(b'\0'))
        data = raw[pos + 48:pos + ln + 48]
        blocks[name] = data
        order.append(name)
        pos += 48 + ln
    return order, blocks


def sysvars_of(data):
    """blokk-adat = [8 név-kód] + [kép] — sysvars a 8. bájttól."""
    img = data[8:]
    def w(o): return img[o] | (img[o + 1] << 8)
    return {
        'E_PPC': w(1), 'D_FILE': w(3), 'DF_CC': w(5), 'VARS': w(7),
        'E_LINE': w(11), 'CH_ADD': w(13), 'STKBOT': w(17),
        'CDFLAG@4044': img[0x4044 - 0x4009],
        'kep_hossz': len(img), 'zarobajt': img[-1],
        'prog_vege_0x76_0x80': None,  # kesobb
    }


def diff_boot(a, b, label):
    print(f'== {label}: {len(a)} B vs {len(b)} B')
    if len(a) != len(b):
        print(f'   HOSSZ-KULONBSEG: {len(a)} -> {len(b)}')
    n = min(len(a), len(b))
    diffs = [i for i in range(n) if a[i] != b[i]]
    print(f'   kulonbozo bajtok: {len(diffs)}')
    # csoportositott kiiras
    runs, cur = [], []
    for i in diffs:
        if cur and i == cur[-1] + 1:
            cur.append(i)
        else:
            if cur: runs.append(cur)
            cur = [i]
    if cur: runs.append(cur)
    for r in runs[:20]:
        lo, hi = r[0], r[-1]
        addr = 0x4009 + lo - 8  # kep-cim (a 8 nev-kod utan)
        print(f'   @{lo} (cim 0x{addr:04X}): {a[lo:hi+1].hex()} -> {b[lo:hi+1].hex()}')
    return diffs


def main():
    o65, b65 = parse(BASE + 'GLM_PicoAI_v0.6.5_kazetta.T81')
    o80, b80 = parse(BASE + 'GLM_PicoAI_v0.8.0_kazetta.T81')
    o81, b81 = parse(BASE + 'GLM_PicoAI_v0.8.1_kazetta.T81')
    o91, b91 = parse(BASE + 'GLM_PicoAI_v0.9.1_kazetta.T81')

    print('blokk-listak:')
    print(' v0.6.5:', o65[:4], '... osszesen', len(o65))
    print(' v0.8.0:', o80[:4], '... osszesen', len(o80))
    print(' v0.8.1:', o81[:4], '... osszesen', len(o81))
    print(' v0.9.1:', o91[:4], '... osszesen', len(o91))

    print('\n### BOOT-blokk (RTBOOT01)')
    print(' v0.6.5 sysvars:', {k: (hex(v) if isinstance(v, int) else v) for k, v in sysvars_of(b65['RTBOOT01']).items()})
    print(' v0.9.1 sysvars:', {k: (hex(v) if isinstance(v, int) else v) for k, v in sysvars_of(b91['RTBOOT01']).items()})
    diff_boot(b65['RTBOOT01'], b80['RTBOOT01'], 'boot v0.6.5 -> v0.8.0 (0x76/CH_ADD patch)')
    diff_boot(b80['RTBOOT01'], b81['RTBOOT01'], 'boot v0.8.0 -> v0.8.1 (OUT FE EI patch)')
    diff_boot(b81['RTBOOT01'], b91['RTBOOT01'], 'boot v0.8.1 -> v0.9.1 (elvileg semmi)')

    print('\n### CHAT-blokk (RTBASE16)')
    diff_boot(b65['RTBASE16'], b80['RTBASE16'], 'base v0.6.5 -> v0.8.0')
    diff_boot(b80['RTBASE16'], b81['RTBASE16'], 'base v0.8.0 -> v0.8.1 (csapda+banner)')
    diff_boot(b81['RTBASE16'], b91['RTBASE16'], 'base v0.8.1 -> v0.9.1 (elvileg semmi)')

    # a v0.9.1 uj RTMEM16 nev-terminatoranak ellenorzese
    m = b91['RTMEM16']
    print('\n### RTMEM16 (v0.9.1 uj blokk)')
    print(' elso 8 bajt:', m[:8].hex(), ' hossz:', len(m))
    print(' utolso nev-kod bajt:', hex(m[6]), '(bit7-es varhato: 0xA2)')
    # osszehasonlitasul egy mukodo blokk elso 8 bajtja
    print(' RTBOOT01 elso 8 bajt:', b91['RTBOOT01'][:8].hex())
    print(' RTBASE16 elso 8 bajt:', b91['RTBASE16'][:8].hex())


if __name__ == '__main__':
    main()
