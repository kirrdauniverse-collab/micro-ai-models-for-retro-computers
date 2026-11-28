import os as _os
RT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
import sys; sys.path.insert(0,RT+'/tests')
from run_app import run, setup as _s, zx2ch
from header_view import word, ENTER, setup
mem, syms = _s()
qs = ['SZIA', 'HOGY VAGY', 'MESELJ VICCET', 'MI A HOMERSEKLET']
keys = setup
for q in qs: keys = keys + word(q) + [ENTER]
c,s = run(keys, maxi=900000000)
head = c.mem[s['LOGHEAD']]
for r in range(0, 24):
    row = [c.mem[0x6200 + r*32 + k] for k in range(32)]
    if all(v==0 for v in row): continue
    print('%2d %s' % (r, ''.join(zx2ch(v if v<64 else v-64) if v else ' ' for v in row).rstrip()))
