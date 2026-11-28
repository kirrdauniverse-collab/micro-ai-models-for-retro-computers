# Trap every write into $7EC4-$7EEF (live stack area where the crash data appears),
# record the PC of the writing instruction. Same user input as the real test.
import sys; sys.path.insert(0, '/home/claude/rt16/release/tests')
import nmi_run
from z80emu import Z80
from run_app import run
HITS = []
_wb = Z80.wb
def _wb_trap(self, a, v):
    a &= 0xFFFF
    if 0x7EC4 <= a <= 0x7EEF and len(HITS) < 40:
        HITS.append((hex(self.pc), hex(a), hex(v), hex(self.sp), self.t))
    return _wb(self, a, v)
Z80.wb = _wb_trap
D = lambda n: 28 + n
Z = lambda ch: ord(ch) - ord('A') + 38
keys = [('k',51)] + [('k',D(2)),('k',D(5)),('k',0),('k',D(1)),('k',D(1)),('raw',[(6,0)])] \
     + [('k',D(8)),('k',0),('k',D(4)),('k',D(8)),('raw',[(6,0)])] \
     + [('k',Z('S')),('k',Z('A')),('k',Z('F')),('k',Z('I')),('raw',[(6,0)]),('k',Z('F')),('raw',[(6,0)])] \
     + [('k',Z('H')),('k',Z('E')),('k',Z('L')),('k',Z('L')),('k',Z('O')),('raw',[(6,0)])]
c, syms = run(keys, maxi=int(sys.argv[1]))
print('pc', hex(c.pc), 'sp', hex(c.sp), 'halted', c.halted, 't', c.t)
print('writes into $7EC4-$7EEF (pc, addr, value, sp, t):')
for h in HITS[:40]: print(h)
