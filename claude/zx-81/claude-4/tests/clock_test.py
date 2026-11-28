import os as _os
RT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
import sys; sys.path.insert(0,RT+'/tests')
from run_app import run, setup as _s, zx2ch
from header_view import word, ENTER, setup
mem, syms = _s()
def on_open(cpu):
    v = (cpu.mem[0x4034] | cpu.mem[0x4035]<<8)
    v = (v - 4500) & 0xFFFF            # FRAMES counts down: 90 s pass
    cpu.mem[0x4034] = v & 255; cpu.mem[0x4035] = v >> 8
    return False
c,s = run(setup+word('HELLO')+[ENTER]+word('HEAD')+[ENTER]+word('QUIT')+[ENTER], maxi=400000000,
          hooks={syms['CH_OPEN']:on_open})
for r in range(0,24):
    row = c.mem[0x6200+r*32:0x6200+r*32+32]
    if any(v>=64 for v in row[:12]) and row[2]==14:
        print('LOG row', r, ''.join(zx2ch(v-64) for v in row[:5]))
print('CLK_MIN', c.mem[s['CLK_MIN']] | c.mem[s['CLK_MIN']+1]<<8, 'CLK_FR', c.mem[s['CLK_FR']] | c.mem[s['CLK_FR']+1]<<8)
