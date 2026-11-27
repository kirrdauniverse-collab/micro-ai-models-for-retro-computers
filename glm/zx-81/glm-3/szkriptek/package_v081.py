#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v0.8.1 forráscsomag: a javított kazetta + blokkonkénti .p fájlok +
a javító/ellenőrző szkriptek + dokumentációk egy zip-be."""
import os
import sys
import zipfile

sys.path.insert(0, '/home/z/my-project/scripts')
sys.path.insert(0, '/home/z/my-project/GLM/repo/tools')
from zx81sim import load_blocks

DL = '/home/z/my-project/download'
ZIP = os.path.join(DL, 'GLM_PicoAI_v0.8.1_forraskod_csomag.zip')
T81 = os.path.join(DL, 'GLM_PicoAI_v0.8.1_kazetta.T81')

names = {'RTBOOT01': 'boot', 'RTBASE16': 'base', 'RT-TUDOM': 'tudomany',
         'RT-MAGYR': 'magyar', 'RT-HOBBI': 'hobbi', 'RT-EGESZ': 'egeszseg',
         'RT-MUNKA': 'munka', 'RT-MUVES': 'muveszet', 'RT-TANUL': 'tanulas',
         'RT-IRODA': 'iroda', 'RT-FILME': 'filmek', 'RT-PROGI': 'programozas',
         'RT-ASTRO': 'csillagaszat', 'RT-ASCII': 'asciiart', 'RT-VERSE': 'vers'}

z = zipfile.ZipFile(ZIP, 'w', zipfile.ZIP_DEFLATED)
z.write(T81, 'GLM_v081_RT16_TOPICS.T81')
for name, data in load_blocks(T81):
    # blokk .p: a név UTÁNI adat (a rendszerképtől $4009-ig)
    k = 0
    while k < len(data) and not (data[k] & 0x80):
        k += 1
    base = k + 1
    z.writestr('GLM_v081_rt16_%s.p' % names[name.strip()], bytes(data[base:]))
z.write(os.path.join(DL, 'GLM_PicoAI_v0.8.1_dokumentacio.txt'),
        'GLM_v081_dokumentacio.txt')
z.write(os.path.join(DL, 'GLM_PicoAI_v0.8.1_valtozasnaplo.txt'),
        'GLM_v081_valtozasnaplo.txt')
z.write('/home/z/my-project/scripts/patch_v081.py', 'scripts/patch_v081.py')
z.write('/home/z/my-project/scripts/verify_v081.py', 'scripts/verify_v081.py')
z.write('/home/z/my-project/scripts/z80dis.py', 'scripts/z80dis.py')
z.close()

n = len(zipfile.ZipFile(ZIP).namelist())
print('%s — %d fájl, %d bájt' % (ZIP, n, os.path.getsize(ZIP)))
