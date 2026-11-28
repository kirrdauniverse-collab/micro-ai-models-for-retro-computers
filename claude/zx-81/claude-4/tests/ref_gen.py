import os as _os
RT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
import sys; sys.path.insert(0,RT+'/tools')
from ref_rtlm import forward, parse
CH = "\n abcdefghijklmnopqrstuvwxyz,.?!'0123456789:-"
def enc(s): return [CH.index(c) for c in s]
import os
m = parse(open(os.environ.get('MODEL',RT+'/models/base_f.bin'),'rb').read())
def gen(prompt, n=30):
    win = [1]*8
    for i in enc(prompt + "\n"): win = win[1:] + [i]
    out=''
    for _ in range(n):
        lg = forward(m, win)
        best = max(range(len(lg)), key=lambda i: lg[i])
        if best == 0: break
        out += CH[best]; win = win[1:] + [best]
    return out
for p in ['szia', 'hogy vagy', 'mesel viccet', 'mi a homerseklet']:
    print(repr(p), '->', repr(gen(p)))
