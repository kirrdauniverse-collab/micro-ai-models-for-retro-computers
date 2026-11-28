import sys
# Same user input, but NO display NMI at all: does the program's own logic reach the
# model output without writing into $7EC4-$7EEF?
sys.path.insert(0, '/home/claude/rt16/release/tools')
import sys; sys.path.insert(0, '/home/claude/rt16/release/tests')
from z80emu import Z80
import run_app
from run_app import run
from z80emu import Z80 as _Z
HITS = []
_wb = _Z.wb
def _wb_trap(self, a, v):
    a &= 0xFFFF
    if 0x7EC4 <= a <= 0x7EEF and len(HITS) < 40: HITS.append((hex(self.pc), hex(a), hex(v), hex(self.sp), self.t))
    return _wb(self, a, v)
_Z.wb = _wb_trap
D = lambda n: 28 + n
Z = lambda ch: ord(ch) - ord('A') + 38
keys = [('k',51)] + [('k',D(2)),('k',D(5)),('k',0),('k',D(1)),('k',D(1)),('raw',[(6,0)])] \
     + [('k',D(8)),('k',0),('k',D(4)),('k',D(8)),('raw',[(6,0)])] \
     + [('k',Z('S')),('k',Z('A')),('k',Z('F')),('k',Z('I')),('raw',[(6,0)]),('k',Z('F')),('raw',[(6,0)])] \
     + [('k',Z('H')),('k',Z('E')),('k',Z('L')),('k',Z('L')),('k',Z('O')),('raw',[(6,0)])]
# disable the NMI model: pretend the display interrupt never fires
import nmi_run
_step_nmi_off = _Z.step
def _step_plain(self):
    self.next_nmi = 1 << 60
    return _step_nmi_off(self)
_Z.step = _step_plain
c, syms = run(keys, maxi=int(sys.argv[1]))
want = [44,52,51,41,52,49,48,52,41,52,50]
print('pc', hex(c.pc), 'sp', hex(c.sp), 'halted', c.halted, 't', c.t)
print('GONDOLKODOM in D-file at', bytes(c.mem[0x7B00:0x7E19]).find(bytes(want)))
print('writes into $7EC4-$7EEF:')
for h in HITS[:40]: print(h)
