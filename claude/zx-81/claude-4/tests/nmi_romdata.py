# Reproduce the user's exact input: N, date 25 11, time 8 48, name SAFI, gender F.
import sys; sys.path.insert(0, '/home/claude/rt16/release/tests')
import nmi_run
from z80emu import Z80
from run_app import run
LOG = {'hit': None, 'trail': [], 'outs': []}
_s = Z80.step
def _watch(self):
    LOG['trail'].append((self.pc, self.sp)); del LOG['trail'][:-40]
    if LOG['hit'] is None and 0x80 <= self.pc <= 0x9F:
        LOG['hit'] = (self.t, hex(self.pc), [(hex(p), hex(s)) for p, s in LOG['trail']])
    return _s(self)
Z80.step = _watch
D = lambda n: 28 + n
Z = lambda ch: ord(ch) - ord('A') + 38
keys  = [('k', 51)]                                   # N
keys += [('k', D(2)), ('k', D(5)), ('k', 0), ('k', D(1)), ('k', D(1)), ('raw', [(6,0)])]   # 25 11 ENTER
keys += [('k', D(8)), ('k', 0), ('k', D(4)), ('k', D(8)), ('raw', [(6,0)])]               # 8 48 ENTER
keys += [('k', Z('S')), ('k', Z('A')), ('k', Z('F')), ('k', Z('I')), ('raw', [(6,0)])]     # SAFI ENTER
keys += [('k', Z('F'))]                               # gender F
c, syms = run(keys, maxi=int(sys.argv[1]))
print('pc', hex(c.pc), 'sp', hex(c.sp), 'halted', c.halted, 'iff', c.iff, 't', c.t)
print('first entry into ROM data 80-9F:', LOG['hit'])
print('CDFLAG now', hex(c.mem[0x403B]))
