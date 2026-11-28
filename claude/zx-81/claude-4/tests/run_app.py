import os as _os
RT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
import sys
sys.path.insert(0,RT+'/tools'); sys.path.insert(0,RT+'/tests')
from z80asm import Asm
from z80emu import Z80
import build_image as B
ROWBYTE = [0xFE,0xFD,0xFB,0xF7,0xEF,0xDF,0xBF,0x7F]
class Stop(Exception): pass
def setup():
    mem, end = B.assemble(RT+'/models/base_f.bin',RT+'/ref/engine/rt_lut.h',0)
    a = Asm(); a.assemble('\n'.join(B.zxify(open(_os.path.join(RT,f)).read()) for f in B.SRC),'app')
    return mem, a.syms
def keytab(syms, mem):
    # ZX code -> (row,bit) unshifted, and shifted variants
    kt = {}; kts = {}
    t = syms['KEYTAB']; ts = syms['KEYTABS']
    for i in range(40):
        r, b = divmod(i, 5)
        kt.setdefault(mem.get(t+i), (r,b)); kts.setdefault(mem.get(ts+i), (r,b))
    return kt, kts
def run(keys, extra_init=None, maxi=400_000_000, state=None, hooks=None):
    """keys: list of ('k', zxcode) | ('s', zxcode) (shifted) | ('raw', [(row,bit)...])"""
    mem, syms = setup()
    kt, kts = keytab(syms, mem)
    img = B.p_image(mem)
    c = Z80()
    for i,v in enumerate(img): c.mem[0x4009+i] = v
    if state: 
        for a,v in state.items(): c.mem[a]=v
    seq = []
    for k in keys:
        if k[0]=='k': seq.append({kt[k[1]]})
        elif k[0]=='s': seq.append({(0,0), kts[k[1]]})
        else: seq.append(set(k[1]))
    st = {'cur':set(), 'seq':seq, 'done':False}
    def pin(port):
        hi = port>>8; v=0xFF
        if hi in ROWBYTE:
            r = ROWBYTE.index(hi)
            for (rr,bit) in st['cur']:
                if rr==r: v &= ~(1<<bit)
        return v
    c.port_in = pin
    def feed(cpu):
        if st['cur']: return False
        if st['seq']:
            st['cur'] = st['seq'].pop(0); return False
        raise Stop()
    def release(cpu):
        st['cur']=set(); return False
    c.hooks[syms['GK_W']] = feed
    c.hooks[syms['GK_T']] = release
    for a,f in (hooks or {}).items(): c.hooks[a]=f
    c.sp = 0x7FF0; c.push(0x7FFE); c.pc = 16514
    try:
        c.run(max_insns=maxi, until=0x7FFE)
    except Stop:
        pass
    return c, syms
def screen(c):
    lines=[]
    for r in range(24):
        base = 0x7B01 + r*33
        lines.append(''.join(zx2ch(c.mem[base+k]) for k in range(32)))
    return lines
ZXCH = {18:'>',0:' ',27:'.',26:',',15:'?',14:':',22:'-',24:'/',23:'*',21:'+',20:'=',16:'(',17:')',11:'"'}
def zx2ch(v):
    if 38<=v<=63: return chr(ord('A')+v-38)
    if 28<=v<=37: return chr(ord('0')+v-28)
    return ZXCH.get(v, '#' if v else ' ')
if __name__=='__main__':
    print('build ok')
