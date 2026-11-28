import os as _os
RT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
import sys; sys.path.insert(0,RT+'/tests')
from run_app import run, setup as _s
from header_view import word, ENTER, setup
mem, syms = _s()
cnt={'f':0}
def on_fwd(cpu):
    cnt['f'] += 1; return False
c0,_ = run(setup, maxi=400000000)
t0=c0.t
c,s = run(setup+word('HELLO')+[ENTER], maxi=400000000, hooks={syms['FORWARD']:on_fwd})
dt = c.t - t0
nout = c.mem[s['NOUT']]
print('forwards', cnt['f'], 'chars out', nout, 'T total', dt)
print('T per forward', dt/cnt['f'], 'frames(50Hz@3.25MHz)', dt/cnt['f']/65000)
