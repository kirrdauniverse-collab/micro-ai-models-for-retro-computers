# Loader mode: RTLOAD image, keys N / 25 11 / 8 48 / SAFI / F; expect return to BASIC (pc 0x7FFE).
import sys; sys.path.insert(0, '/home/claude/rt16/release/tests')
import nmi_run
from run_app import run, screen
P = open('/home/claude/rt16/release/dist/RTLOAD_v1.1.6-diag_Claude_Haiku_5.5.P','rb').read()
state = {0x4009 + i: v for i, v in enumerate(P)}
D = lambda n: 28 + n
Z = lambda ch: ord(ch) - ord('A') + 38
keys = [('k',51)] + [('k',D(2)),('k',D(5)),('k',0),('k',D(1)),('k',D(1)),('raw',[(6,0)])] \
     + [('k',D(8)),('k',0),('k',D(4)),('k',D(8)),('raw',[(6,0)])] \
     + [('k',Z('S')),('k',Z('A')),('k',Z('F')),('k',Z('I')),('raw',[(6,0)]),('k',Z('F'))]
c, syms = run(keys, state=state, maxi=int(sys.argv[1]))
print('pc', hex(c.pc), 'sp', hex(c.sp), 'halted', c.halted)
for l in screen(c)[:12]: print(l)
