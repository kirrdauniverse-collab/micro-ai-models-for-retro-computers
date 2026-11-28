import os as _os
RT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
import sys; sys.path.insert(0,RT+'/tests')
from run_app import run, screen
def word(s):
    out=[]
    for ch in s:
        if ch==' ': out.append(('k',0))
        elif ch.isdigit(): out.append(('k',28+int(ch)))
        else: out.append(('k',38+ord(ch)-ord('A')))
    return out
ENTER=('raw',[(6,0)])
setup = [('k',38), ('k',51)] + word('1') + [ENTER] + word('21 11') + [ENTER] + word('14 05') + [ENTER] + word('ZIGGY') + [ENTER] + [('k',43)]
c,s = run(setup+word('HELLO')+[ENTER]+word('HEAD')+[ENTER], maxi=400000000)
for i,l in enumerate(screen(c)): print('%2d|%s|' % (i,l))
print('NOUT', c.mem[s['NOUT']], 'GFR', c.mem[s['GFR']] | c.mem[s['GFR']+1]<<8, 'TOT', c.mem[s['SESS_TOK']] | c.mem[s['SESS_TOK']+1]<<8)
print('DFILE+1 :', [c.mem[0x7B01+k] for k in range(32)])
print('HDRB    :', [c.mem[s['HDRB']+k] for k in range(32)])
print('HDRB sym:', hex(s['HDRB']), 'HB_P', hex(c.mem[s['HB_P']] | c.mem[s['HB_P']+1]<<8))
