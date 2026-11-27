#!/usr/bin/env python3
import sys,struct

Z=0x4009
RAMTOP=0x4F00
TOPIC=0x4800
TOPEND=0x4F00
PROFILE=0x7D00

def u16(b,a): return b[a-Z] | (b[a-Z+1]<<8)

def check(path):
    b=open(path,'rb').read()
    if len(b)<0x100: raise SystemExit(path+": too short")
    if b[0]!=0: raise SystemExit(path+": bad VERSN")
    d=u16(b,0x400C); v=u16(b,0x4010); e=u16(b,0x4014)
    if not (0x4100<=d<RAMTOP): raise SystemExit(path+f": D_FILE {d:04X} not below RAMTOP")
    if not (d+793<=RAMTOP): raise SystemExit(path+": display file crosses RAMTOP")
    if not (v>d): raise SystemExit(path+": VARS")
    if not (e>=v and e<=Z+len(b)): raise SystemExit(path+f": E_LINE {e:04X} invalid")
    # BASIC line 1 at fixed program address.
    p=0x407D-Z
    if b[p]!=0 or b[p+4]!=0xEA: raise SystemExit(path+": line1 is not REM")
    code_addr=0x4082-Z
    print(f"{path}: {len(b)} bytes D_FILE={d:04X} E_LINE={e:04X}")

def check_t81(path):
    b=open(path,'rb').read()
    if b[:4]!=b'EO81': raise SystemExit(path+": bad EO81 header")
    pos=4; names=[]
    while pos < len(b):
        if pos+48>len(b): raise SystemExit(path+": truncated tape block header")
        rawname=b[pos:pos+32].split(b'\0',1)[0].decode('ascii','replace')
        rawlen=b[pos+32:pos+48].split(b'\0',1)[0]
        try: n=int(rawlen.decode('ascii'))
        except Exception: raise SystemExit(path+": invalid block length")
        pos+=48
        if n<1 or pos+n>len(b): raise SystemExit(path+": invalid block payload length")
        names.append(rawname)
        pos+=n
    expected=[
      "PICO BOOT R5","PICO SETUP R5","PICO ENGINE R5",
      "PICO SCIENCE R5","PICO ASTRONOMY R5","PICO HISTORY R5",
      "PICO PROGRAMMING R5"]
    if names!=expected: raise SystemExit(path+f": tape blocks {names!r} != expected order")
    print(f"{path}: EO81 OK, {len(names)} program blocks, {len(b)} bytes")

def main():
    for p in sys.argv[1:]:
        if p.upper().endswith('.T81'): check_t81(p)
        else: check(p)
    eng=open(sys.argv[3],'rb').read()
    if eng[0x4082-Z:0x4085-Z]!=bytes((0xC3,0x00,0x4F)): raise SystemExit("engine: no protected JP 4F00")
    if u16(eng,0x4004)!=0: pass # RAMTOP is deliberately not saved in a P image.
    corepos=eng.find(b'KB1\x01',0x6800-Z,0x6F00-Z)
    if corepos<0: raise SystemExit("engine: CORE header missing")
    print(f"engine: CORE header at 0x{corepos+Z:04X}")
    if eng[0x6F00-Z]==0 and eng[0x6F01-Z]==0: raise SystemExit("engine: help area empty")
    # Topic packs must be physically below RAMTOP; this is what makes a
    # topic switch an ordinary LOAD overwrite rather than a protected write.
    for pth in sys.argv[1:]:
        if pth.upper().endswith('.T81') or 'ENGINE' in pth.upper() or 'BOOT' in pth.upper() or 'SETUP' in pth.upper():
            continue
        tb=open(pth,'rb').read()
        if len(tb) <= TOPIC-Z or len(tb) > TOPEND-Z:
            raise SystemExit(pth+": topic image does not fit below RAMTOP")
        if tb[TOPIC-Z:TOPIC-Z+4] != b'KB1\x01':
            raise SystemExit(pth+": topic KB1 header missing at 0x4800")

    print("R5 structural checks OK")
if __name__=='__main__': main()
