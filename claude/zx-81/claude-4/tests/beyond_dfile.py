# Trap writes beyond the D-file ($7E19-$7FFF) and check whether the model output
# (GONDOLKODOM) appears in the display file. Same user input as the real test.
import sys; sys.path.insert(0, '/home/claude/rt16/release/tests')
import nmi_run
from z80emu import Z80
from run_app import run
HITS = []; CNT = [0]
_wb = Z80.wb
def _wb_trap(self, a, v):
    a &= 0xFFFF
    if 0x7E19 <= a <= 0x7FFF:
        CNT[0] += 1
        if len(HITS) < 60: HITS.append((hex(self.pc), hex(a), hex(v), hex(self.sp), self.t))
    return _wb(self, a, v)
Z80.wb = _wb_trap
D = lambda n: 28 + n
Z = lambda ch: ord(ch) - ord('A') + 38
keys = [('k',51)] + [('k',D(2)),('k',D(5)),('k',0),('k',D(1)),('k',D(1)),('raw',[(6,0)])] \
     + [('k',D(8)),('k',0),('k',D(4)),('k',D(8)),('raw',[(6,0)])] \
     + [('k',Z('S')),('k',Z('A')),('k',Z('F')),('k',Z('I')),('raw',[(6,0)]),('k',Z('F')),('raw',[(6,0)])] \
     + [('k',Z('H')),('k',Z('E')),('k',Z('L')),('k',Z('L')),('k',Z('O')),('raw',[(6,0)])]
c, syms = run(keys, maxi=int(sys.argv[1]))
want = [44,52,51,41,52,49,48,52,41,52,50]          # GONDOLKODOM
dfile = bytes(c.mem[0x7B00:0x7E19])
found = dfile.find(bytes(want))
print('pc', hex(c.pc), 'sp', hex(c.sp), 't', c.t, 'GONDOLKODOM in D-file at offset', found)
print('writes beyond D-file:', CNT[0])
for h in HITS[:60]: print(h)
