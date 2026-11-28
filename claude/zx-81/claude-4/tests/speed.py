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
setup = [('k',38), ('k',51)] + word('1') + [ENTER] + word('21 11') + [ENTER] + word('9') + [ENTER] + word('ZIGGY') + [ENTER] + [('k',43)]
c0,s = run(setup, maxi=400000000)
t0 = c0.t
c,s = run(setup+word('HELLO')+[ENTER], maxi=400000000)
t1 = c.t
print('NOUT', c.mem[s['NOUT']], 'chat T', t1-t0, 'sec@3.25MHz', round((t1-t0)/3.25e6,2))
print('sec per char', round((t1-t0)/3.25e6/max(1,c.mem[s['NOUT']]),3))
