# ZX81 display NMI model: fires at $0066 every ~207 T-states (I=$1E).
import sys, os
RT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RT + '/tools'); sys.path.insert(0, RT + '/tests')
from z80emu import Z80
_orig_init = Z80.__init__
def _init(self):
    _orig_init(self); self.i = 0x1E; self.next_nmi = 207
Z80.__init__ = _init
_orig_step = Z80.step
def _step(self):
    if self.t >= getattr(self, 'next_nmi', 0) and not (0x66 <= self.pc <= 0x7F):
        self.next_nmi = self.t + 207
        self.halted = False
        self.push(self.pc)
        self.pc = 0x66
    return _orig_step(self)
Z80.step = _step
# Watch for the bad-flow symptom: PC leaving program/ROM into the D-file or unmapped RAM.
BAD = {'hit': None, 'trail': []}
_step2 = Z80.step
def _step_watch(self):
    BAD['trail'].append((self.pc, self.sp)); del BAD['trail'][:-12]
    if BAD['hit'] is None and (0x7B00 <= self.pc <= 0x7E18 or 0x8000 <= self.pc):
        BAD['hit'] = (hex(self.pc), self.t, [(hex(p), hex(s)) for p, s in BAD['trail']])
    return _step2(self)
Z80.step = _step_watch
