import sys; sys.path.insert(0, '/home/claude/rt16/release/tests')
import nmi_run
from run_app import run, screen
keys = [('k',c) for c in (45,42,49,49,52)] + [('raw',[(6,0)])] + [('k',43)] + [('raw',[(6,0)])]   # HELLO ENTER, F ENTER
c, syms = run(keys, maxi=int(sys.argv[1]))
print('pc', hex(c.pc), 'sp', hex(c.sp), 'halted', c.halted, 'iff', c.iff, 't', c.t)
print('first bad:', nmi_run.BAD['hit'])
