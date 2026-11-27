import sys
p = sys.argv[1]
s = open(p).read()
i = s.find('\tSECTION data_compiler')
if i >= 0:
    j = s.find('\tSECTION IGNORE', i)
    if j > i:
        s = s[:i] + s[j:]
        print(f'{p}: DEFW-duplikatum kivagva')
# string-pool: minden ___str_N-at modul-prefixxel nevezunk at (argv[2])
if len(sys.argv) > 2:
    tag = sys.argv[2]
    out = []
    n = 0
    for line in s.split('\n'):
        if '___str_' in line:
            # a talalt legnagyobb sorszamot visszuk be
            for k in range(64, -1, -1):
                tok = f'___str_{k}'
                if tok in line:
                    line = line.replace(tok, f'__s{tag}_{k}')
                    break
        out.append(line)
    s = '\n'.join(out)
open(p, 'w').write(s)
