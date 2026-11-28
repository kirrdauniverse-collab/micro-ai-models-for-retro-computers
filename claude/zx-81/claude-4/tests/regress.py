import os as _os
RT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
import sys; sys.path.insert(0,RT+'/tests')
from run_app import *
def word(s):
    out=[]
    for ch in s:
        if ch==' ': out.append(('k',0))
        elif ch.isdigit(): out.append(('k',28+int(ch)))
        else: out.append(('k',38+ord(ch)-ord('A')))
    return out
ENTER=('raw',[(6,0)])
setup = [('k',38), ('k',51)] + word('1') + [ENTER] + word('21 11') + [ENTER] + word('9') + [ENTER] + word('ZIGGY') + [ENTER] + [('k',43)]
results = {}
c,s = run(setup+word('HELLO')+[ENTER]+word('HEAD')+[ENTER]+word('QUIT')+[ENTER], maxi=400000000)
sc = screen(c)
results['setup+chat+quit'] = any(l.startswith('> HELLO') for l in sc) and any('EMLEKEZEM' in l for l in sc) and any('SAVE' in l for l in sc)
results['state name'] = ''.join(zx2ch(c.mem[0x7F00+3+k]) for k in range(6)) == 'ZIGGY '
row0={0x7B01+k: c.mem[0x7B01+k] for k in range(33)}
c2,s2 = run([('k',38)]+word('1')+[ENTER]+word('25 11')+[ENTER]+word('9')+[ENTER]+[('k',51)]+word('QUIT')+[ENTER], maxi=400000000, state=row0)
sc2 = screen(c2)
results['restore greet'] = any('SZIA ZIGGY' in l for l in sc2)
results['restore asks pain'] = any('FAJ MEG' in l for l in sc2)
results['pain cleared'] = c2.mem[0x7F00+16] == 0
c3,s3 = run([('k',38)]+word('1')+[ENTER]+word('25 11')+[ENTER]+word('9')+[ENTER]+[('k',51)]+word('RAIN')+[ENTER]+word('QUIT')+[ENTER], maxi=400000000, state=row0)
results['topic prompt'] = any('LOAD "WEATHER"' in l or 'WEATHE' in l for l in screen(c3))
# v1.1.0: header rows, inverse chat header rows, clock (run without QUIT: the
# top rows keep the packed state after QUIT, by design)
ch, sh = run(setup+word('HELLO')+[ENTER], maxi=400000000)
scr = screen(ch)
results['header row 1'] = scr[1].startswith('HOM1 NEM:F GOND:BE')
results['header row 0'] = scr[0].startswith('21.11 ')
hdr_rows = [r for r in range(64) if ch.mem[0x6200+r*32+2] == 14+64]
results['chat header'] = len(hdr_rows) >= 1
results['clock set'] = (ch.mem[sh['CLK_MIN']] | ch.mem[sh['CLK_MIN']+1] << 8) in (9*60, 9*60+1, 9*60+2, 9*60+3, 9*60+4)
for k,v in results.items(): print('%-20s %s' % (k, 'OK' if v else 'FAIL'))
