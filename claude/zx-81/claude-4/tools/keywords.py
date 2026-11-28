import os as _os
RT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
# Extract the ZX81 keyword table from the ROM and calibrate tokens against demo.T81 usage.
import re, sys
ROM = open(RT+'/models/zx81.rom','rb').read()
# ZX81 char codes: A=38..Z=63, 0..9=28..37
def zx(s):
    out=[]
    for ch in s:
        if 'A'<=ch<='Z': out.append(38+ord(ch)-65)
        elif '0'<=ch<='9': out.append(28+ord(ch)-48)
        elif ch=='$': out.append(29)
        elif ch==' ': out.append(0)
        else: out.append({'"':11,'(':16,')':17,'*':23,'+':21,'-':22,'=':20,';':25,',':26,'.':27,':':14,'?':15,'>':18,'<':19,'/':24}[ch])
    return out
words=['PRINT','INPUT','LET','GOTO','FOR','NEXT','TO','POKE','CODE','LEN','REM','RAND','USR','VAL','IF','THEN','LOAD','SAVE','FAST','SLOW','RANDOMISE','STOP','CLS','RUN','NEW','GO SUB','RETURN','CHR$','STR$','VAL$','LIST','AND','OR','NOT','PEEK','THEN']
for w in words:
    pat=bytes(zx(w)[:-1]+[zx(w)[-1]|0x80])
    i=ROM.find(pat)
    print(f'{w:10s} rom_at {i:#06x}' if i>=0 else f'{w:10s} -')
