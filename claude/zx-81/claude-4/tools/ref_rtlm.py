import os as _os
RT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
# Bit-exact Python reference of ref/engine/rt_engine.c (RTLM v2, class F).
import sys, struct
sys.path.insert(0, RT+'/tools')
EXP = None

def load_lut(path):
    src = open(path).read()
    import re
    vals = re.findall(r'\b(\d+)\b', src[src.index('RT_EXP_LUT[256]'):].split('{',1)[1].split('}',1)[0])
    return [int(v) for v in vals]

def parse(blob):
    assert blob[0:4] == b'RTLM'
    f = struct.unpack_from('<13H', blob, 4)
    ver, flags, vocab, ctx, emb, h1, h2, sh_e, sh1, sh2, sh_o, temp_sh = f[:12]
    assert ver == 2 and h2 == 0
    p = 92
    m = {'vocab': vocab, 'ctx': ctx, 'emb': emb, 'h1': h1, 'temp_sh': temp_sh}
    n = vocab * emb
    m['E'] = struct.unpack_from('%db' % n, blob, p); p += n
    m['SH1'] = blob[p:p+h1]; p += h1
    n = h1 * (ctx*emb + 1)
    m['W1'] = struct.unpack_from('%db' % n, blob, p); p += n
    m['SHO'] = blob[p:p+vocab]; p += vocab
    n = vocab * (h1 + 1)
    m['WO'] = struct.unpack_from('%db' % n, blob, p); p += n
    assert p + 2 == len(blob), (p, len(blob))
    return m

def forward(m, ctx):
    ctx_n, emb, h1, V = m['ctx'], m['emb'], m['h1'], m['vocab']
    x = []
    for c in ctx:
        x += list(m['E'][c*emb:(c+1)*emb] if False else m['E'][c*emb:(c+1)*emb])
    n_in = ctx_n * emb
    h = []
    for o in range(h1):
        base = o * (n_in + 1)
        acc = sum(x[i] * m['W1'][base+i] for i in range(n_in))
        acc += 128 * m['W1'][base+n_in]
        acc >>= m['SH1'][o]
        h.append(min(max(acc, 0), 127))
    lg = []
    for o in range(V):
        base = o * (h1 + 1)
        acc = sum(h[i] * m['WO'][base+i] for i in range(h1))
        acc += 128 * m['WO'][base+h1]
        lg.append(acc >> m['SHO'][o])
    return lg

def sample(lg, temp_sh, greedy, seed, lut):
    V = len(lg)
    mx = lg[0]; best = 0
    for i in range(1, V):
        if lg[i] > mx: mx = lg[i]; best = i
    if greedy: return best
    w = []
    for i in range(V):
        d = (mx - lg[i]) >> temp_sh
        k = min(d >> 3, 255)
        w.append(lut[k])
    s = sum(w)
    if s == 0: return best
    x = seed[0]
    x = (x ^ ((x << 13) & 0xFFFFFFFF)) & 0xFFFFFFFF
    x = (x ^ (x >> 17)) & 0xFFFFFFFF
    x = (x ^ ((x << 5) & 0xFFFFFFFF)) & 0xFFFFFFFF
    seed[0] = x
    r = x % s
    acc = 0
    for i in range(V):
        acc += w[i]
        if r < acc: return i
    return best

if __name__ == '__main__':
    lut = load_lut(RT+'/ref/engine/rt_lut.h')
    m = parse(open(RT+'/models/base_f.bin','rb').read())
    ok = bad = 0; maxabs = 0
    for line in open(RT+'/tests/golden_base_f.txt'):
        if '|' not in line: continue
        a, rest = line.split('|', 1)
        ctx = [int(t) for t in a.split()]
        am, lgw, sw = [int(t) for t in rest.split('|')[:3]]
        lg = forward(m, ctx)
        maxabs = max(maxabs, max(abs(v) for v in lg))
        seed = [1234]
        got_s = sample(lg, m['temp_sh'] if False else 2, False, seed, lut)
        am_got = sample(lg, 0, True, [0], lut)
        if am_got == am and lg[am] == lgw and got_s == sw: ok += 1
        else:
            bad += 1
            if bad < 4: print('BAD', line.strip(), am_got, lg[am_got], got_s)
    print('ok', ok, 'bad', bad, 'max|logit|', maxabs, 'lut', len(lut))
