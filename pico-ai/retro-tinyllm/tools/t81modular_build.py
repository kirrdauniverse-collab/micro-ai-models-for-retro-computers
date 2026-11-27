#!/usr/bin/env python3
"""Build the PICO R5 modular cassette set.

Files:
  PICO_BOOT_R5.T81        tiny installer / splash, sets RAMTOP=0x4F00
  PICO_ENGINE_R5.T81      protected engine + CORE bank + help pages
  PICO_<TOPIC>_R5.T81    self-starting topic overlay at 0x7400

The profile lives at 0x7D00 and is intentionally outside every P-file's
E_LINE, so loading the engine or a topic cannot overwrite it.
"""
from pathlib import Path
import sys, re

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
sys.path.insert(0,str(ROOT/"tools"/"ai16"))
from t81frame import SYSVARS, Z, PROG, be16, le16, zx_digits
from zx81ai_r5_kb import CORE_ADDR, TOPIC_ADDR, CORE_LIMIT, TOPIC_LIMIT, bank_bytes, CORE as CORE_RECORDS, PACKS, enc

RAMTOP=0x4F00
ENGINE=0x4F00
TOPIC_STAGE=0x4800
CORE_ADDR_R5=0x6900
HELP=(0x6F00,0x6F80,0x7000)
WORK_END=0x7400
TOPIC_END=0x7A40
PROFILE=0x7D00
DFILE=0x4200
ENGINE_SRC=ROOT/"ports/zx81/modular/zx81ai_r5.asm"
SETUP_SRC=ROOT/"ports/zx81/modular/setup_r5.asm"

def image(lines, blobs, dfile=DFILE):
    prog=b''.join(be16(n)+le16(len(t)+1)+t+b'\x76' for n,t in lines)
    prog += b'\x76'
    prog_end=PROG+len(prog)
    for addr,data in blobs:
        if addr<PROG: raise ValueError("blob below BASIC program")
    vars_=dfile+793
    vars_end=vars_+1
    top=max([prog_end,vars_end]+[a+len(d) for a,d in blobs])
    eline=top
    img=bytearray(eline-Z)
    img[:116]=SYSVARS
    def put(addr,data):
        img[addr-Z:addr-Z+len(data)]=data
    put(PROG,prog)
    for addr,data in blobs: put(addr,data)
    put(dfile,b'\x76'+(bytes(32)+b'\x76')*24)
    put(vars_,b'\x80')
    img[3:5]=le16(dfile)
    img[5:7]=le16(dfile+1)
    img[7:9]=le16(vars_)
    img[11:13]=le16(eline)
    img[13:15]=le16(eline+4)
    img[17:19]=le16(eline+5)
    img[19:21]=le16(eline+5)
    img[32:34]=le16(dfile)
    return bytes(img),eline

def tape_block(name,img):
    """One EO81 program block, without the file-level EO81 header."""
    return name.encode().ljust(32,b'\0')[:32]+str(len(img)).encode().ljust(16,b'\0')+img

def tape(name,img,out):
    data=b'EO81'+tape_block(name,img)
    Path(out).write_bytes(data)
    Path(out).with_suffix('.p').write_bytes(img)

def multi_tape(blocks,out):
    """Build one EightyOne T81 containing several selectable program blocks."""
    data=b'EO81'+b''.join(tape_block(name,img) for name,img in blocks)
    Path(out).write_bytes(data)

def put_row(code, msg, row):
    b=enc(msg)
    if len(b)>32: raise ValueError(msg)
    # ld de,msg ; ld b,len ; loop ld a,(de), ld (hl),a, inc de, inc hl, djnz
    # then add hl,33-len
    start=len(code)
    code += bytearray((0x11,0,0x00,0x06,len(b),0x1A,0x77,0x13,0x23,0x10,0xF9))
    code += bytearray((0x01,(33-len(b))&255,(33-len(b))>>8,0x09))
    return start

def boot_code():
    """Safe diagnostic first-stage loader.

    Deliberately does NOT change RAMTOP. It proves that the P-file, BASIC
    program and display file are alive before any memory protection step.
    """
    def q(text):
        return bytes((0xF5, 0x0B)) + enc(text) + bytes((0x0B,))
    def inp(letter):
        return bytes((0xEE, enc(letter)[0], 0x0D))

    return [
        (1, b'\xEA'),
        (10, q("PICO R5.1 SAFE BOOT")),
        (20, q("RAMTOP IS UNCHANGED")),
        (30, q("PRESS ENTER TO CONTINUE")),
        (40, inp("A")),
        (50, q("BOOT IS WORKING")),
        (60, q("TYPE NEW THEN LOAD AGAIN")),
        (70, q("NEXT BLOCK IS SETUP")),
    ]


def engine_stub():
    return bytes((0xC3,ENGINE&255,ENGINE>>8))

def topic_stub(pack_id):
    # Topic data itself is the replaceable RAM area below RAMTOP.
    # LOAD overwrites it on the next topic load. The stub only records
    # the pack id and transfers control to the protected engine.
    vpack=0x7CC4
    return bytes((
        0x3E, (pack_id+1)&255,
        0x32, vpack&255, vpack>>8,
        0xC3, ENGINE&255, ENGINE>>8
    ))


def assemble_source(path, expected_org):
    import importlib.util
    spec=importlib.util.spec_from_file_location("oldbuild",ROOT/"tools"/"t81ai16_build.py")
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    text=mod.preprocess(str(path))
    tmp="/tmp/"+Path(path).stem+".src"
    Path(tmp).write_text(text)
    from z80._asm import Asm
    from z80._source import SourceFile
    c=Asm().assemble(SourceFile(tmp)); c.resolve()
    blocks=c.encode()
    org=min(a for a,_ in blocks)
    data=b''.join(b[1] for b in blocks if b[0]>=0x4000)
    if org!=expected_org: raise SystemExit(f"{path.name} org 0x{org:04X} != 0x{expected_org:04X}")
    return data

def assemble_engine():
    src=ENGINE_SRC.read_text()
    # Reuse the proven assembler/preprocessor from the legacy builder.
    import importlib.util
    spec=importlib.util.spec_from_file_location("oldbuild",ROOT/"tools"/"t81ai16_build.py")
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    text=mod.preprocess(str(ENGINE_SRC))
    tmp='/tmp/pico_r5_engine.src'
    Path(tmp).write_text(text)
    from z80._asm import Asm
    from z80._source import SourceFile
    c=Asm().assemble(SourceFile(tmp)); c.resolve()
    blocks=c.encode()
    data=b''.join(b[1] for b in blocks if b[0]>=0x4000)
    org=min(a for a,_ in blocks)
    if org!=ENGINE: raise SystemExit(f'R5 engine org 0x{org:04X} != 0x{ENGINE:04X}')
    return data

def main():
    out=ROOT/"dist"/"r5"; out.mkdir(parents=True,exist_ok=True)
    blocks=[]
    # boot: BASIC deliberately performs CLEAR/RAMTOP before NEW.
    bimg,_=image(boot_code(),[])
    tape("PICO BOOT R5",bimg,out/"PICO_BOOT_R5.T81")
    blocks.append(("PICO BOOT R5",bimg))
    # setup BASIC: prompts create A$..E$, then machine code stores the profile.
    setup_code=assemble_source(SETUP_SRC,0x4082)
    if 0x76 in setup_code: raise SystemExit("setup code contains ZX81 NEWLINE/HALT byte")
    q=lambda text: bytes((0xF5,0x0B))+enc(text)+bytes((0x0B,))
    def inp(letter):
        # INPUT A$ is EE, letter-code, '$' (0x0D); image() adds NEWLINE.
        return bytes((0xEE,enc(letter)[0],0x0D))
    lines=[
      (1,b'\xEA'+setup_code),
      (10,q("DATE DDMMYY")),
      (20,inp("A")),
      (30,q("TIME HHMM")),
      (40,inp("B")),
      (50,q("YOUR NAME")),
      (60,inp("C")),
      (70,q("GENDER M OR F")),
      (80,inp("D")),
      (90,q("INSTRUCTIONS Y OR N")),
      (100,inp("E")),
      (110,b'\xF9\xD4\xC5\x0B'+zx_digits(16514)+b'\x0B'),
      (120,q("PROFILE SAVED")),
      (130,q("NOW LOAD PICO ENGINE TAPE"))
    ]
    simg,_=image(lines,[])
    tape("PICO SETUP R5",simg,out/"PICO_SETUP_R5.T81")
    blocks.append(("PICO SETUP R5",simg))
    # engine
    engine=assemble_engine()
    MEM_LIMIT=0x6900
    if ENGINE+len(engine)>MEM_LIMIT:
        raise SystemExit(f'engine overlaps profile/core: end 0x{ENGINE+len(engine):04X}')
    core=bank_bytes("CORE",CORE_RECORDS)
    if CORE_ADDR_R5+len(core)>0x6F00: raise SystemExit(f'core overflow: {len(core)}')
    helps=[enc("type a line and press enter.#i remember your profile in protected memory."),
           enc("topics are modular.#ask science, astronomy, history or programming."),
           enc("commands: /help /topics /mem /temp n /reason n /save /forget /quit.")]
    help_blobs=[]
    for addr,data in zip(HELP,helps):
        if len(data)>0x80: raise SystemExit("help overflow")
        help_blobs.append((addr,data+b'\xFF'))
    eblobs=[(ENGINE,engine),(CORE_ADDR_R5,core)]+help_blobs
    eimg,eline=image([(1,b'\xEA'+engine_stub()),(2,b'\xF9\xD4\xC5\x0B'+zx_digits(16514)+b'\x0B')],eblobs)
    if eline>TOPIC_END: raise SystemExit(f'engine image ends 0x{eline:04X}, topic/history boundary 0x{TOPIC_END:04X}')
    tape("PICO ENGINE R5",eimg,out/"PICO_ENGINE_R5.T81")
    blocks.append(("PICO ENGINE R5",eimg))
    # topics
    for name,(pid,recs) in PACKS.items():
        data=bank_bytes(name.upper(),recs)
        if TOPIC_ADDR+len(data)>=RAMTOP: raise SystemExit(f'{name} topic overflow below RAMTOP: {len(data)}')
        timg,_=image([(1,b'\xEA'+topic_stub(pid)),(2,b'\xF9\xD4\xC5\x0B'+zx_digits(16514)+b'\x0B')],[(TOPIC_ADDR,data)])
        tape("PICO "+name.upper()+" R5",timg,out/(f"PICO_{name.upper()}_R5.T81"))
        blocks.append(("PICO "+name.upper()+" R5",timg))
        print(f'{name:12s} id={pid} {len(data):4d} bytes -> 0x{TOPIC_ADDR:04X}')
    print(f'engine      0x{ENGINE:04X}..0x{ENGINE+len(engine)-1:04X} ({len(engine)} bytes)')
    print(f'core        0x{CORE_ADDR_R5:04X}..0x{CORE_ADDR_R5+len(core)-1:04X} ({len(core)} bytes)')
    print(f'profile     0x{PROFILE:04X}..0x{PROFILE+511:04X} (protected)')
    print(f'topic slot  0x{TOPIC_ADDR:04X}..0x{TOPIC_END-1:04X}')
    print(f'history     0x7A40..0x7CC3 (20 slots)')
    multi_tape(blocks,out/"PICO_AI_R5_ALL.T81")
    print(f'combined    {out/"PICO_AI_R5_ALL.T81"} ({(out/"PICO_AI_R5_ALL.T81").stat().st_size} bytes, {len(blocks)} tape files)')
if __name__=='__main__': main()
