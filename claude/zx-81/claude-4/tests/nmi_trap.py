import sys; sys.path.insert(0, '/home/claude/rt16/release/tests')
import nmi_run
from z80emu import Z80
from run_app import run
TRAP = {'hit': None, 'trail': []}
_s = Z80.step
def _watch(self):
    TRAP['trail'].append((self.pc, self.sp)); del TRAP['trail'][:-16]
    if TRAP['hit'] is None and self.sp <= 0x7EF0 and self.mem[self.sp] == 0x30 and self.mem[(self.sp+1) & 0xFFFF] == 0xDD:
        TRAP['hit'] = (self.t, [(hex(p), hex(s)) for p, s in TRAP['trail']])
    return _s(self)
Z80.step = _watch
keys = [('k',c) for c in (45,42,49,49,52)] + [('raw',[(6,0)])] + [('k',43)] + [('raw',[(6,0)])]
c, syms = run(keys, maxi=int(sys.argv[1]))
print('pc', hex(c.pc), 'sp', hex(c.sp), 'halted', c.halted, 'iff', c.iff, 't', c.t)
print('first DD30 on stack:', TRAP['hit'])
