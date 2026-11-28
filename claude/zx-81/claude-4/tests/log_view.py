import os as _os
RT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
import sys; sys.path.insert(0,RT+'/tests')
from run_app import run, zx2ch
from header_view import word, ENTER, setup
def show(c, s):
    head = c.mem[s['LOGHEAD']]
    for r in range(0, 12):
        row = (head - 11 + r) % 64
        cells = [c.mem[0x6200 + row*32 + k] for k in range(32)]
        txt = ''.join(('~' if v >= 64 else '') + zx2ch(v if v < 64 else v-64) for v in cells)
        print('%2d %s' % (row, txt.rstrip()))
if __name__ == '__main__':
    c,s = run(setup+word('HELLO')+[ENTER]+word('HEAD')+[ENTER]+word('QUIT')+[ENTER], maxi=400000000)
    print('DFILE row0:', ''.join(zx2ch(c.mem[0x7B01+k]) for k in range(32)))
    show(c, s)
