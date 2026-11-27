#!/bin/bash
set -e
Z8=/tmp/build/z88dk
export PATH=$Z8/bin:$PATH ZCCCFG=$Z8/lib/config
E=/home/z/my-project/GLM/v090/engine
P=/home/z/my-project/GLM/v090/port
W=/tmp/v9build
DEFS="-DRTV9_SMALL=1 -DRT_MAX_VOCAB=48 -DRT_MAX_CTX=8 -DRT_MAX_EMB=16 -DRT_MAX_HID=48 -DRT_APP_MODEL_MAX=10240 -DRT_MEM_MAX=6 -DRT_JOURNAL_MAX=8 -DRT_LINE_MAX=64"
rm -rf $W && mkdir -p $W && cd $W

stage() {
  f=$1; n=$2
  z88dk-ucpp -I$E -iquote. -D__Z80__ -D__Z80 -DZX81 -D__ZX81__ $DEFS -D__Z88DK -D__SDCC -I"$Z8/include/arch/zx81" -isystem"$Z8/include" $f -o $n.i2
  z88dk-zpragma -autoformat < $n.i2 > $n.i
  z88dk-zsdcc --constseg CONST_compiler -mz80 --legacy-banking --no-optsdcc-in-asm --c1mode --emit-externs --no-c-code-in-asm --reserve-regs-iy --no-peep --peep-file "$Z8/lib/sdcc/sdcc_peeph.2" < $n.i -o $n.opt
  z88dk-copt -mz80 -compiler=sdcc "$Z8/lib/sdcc/sdcc_opt.1" < $n.opt > $n.a1
  z88dk-copt -mz80 -compiler=sdcc "$Z8/lib/sdcc/sdcc_opt.2" < $n.a1 > $n.a2
  z88dk-copt -mz80 -compiler=sdcc "$Z8/lib/sdcc/sdcc_opt.3" < $n.a2 > $n.a3
  z88dk-copt -mz80 -compiler=sdcc "$Z8/lib/sdcc/sdcc_opt.9" < $n.a3 > $n.asm
  python3 /home/z/my-project/scripts/cut_dup.py $n.asm $n
}

echo "== motor modulok =="
stage $P/hal_zx81.c hal
stage $P/app16.c app
stage $P/zone.c zone
stage $E/rt_charset.c charset
stage $E/rt_model.c model
stage $E/rt_engine.c engine
stage $E/rt_chat.c chat

cat > stubs.asm <<'STUBS'
	PUBLIC l_ret
	PUBLIC _heap
	PUBLIC __lc_char_cmp_bc
	PUBLIC __rodata_error_strings_head
	PUBLIC asm_malloc
	PUBLIC __lc_char_ordinal
__lc_char_ordinal:
	ld a,l
	ret
l_ret:
	ret
_heap:
	defs 6
__lc_char_cmp_bc:
	ret
__rodata_error_strings_head:
	ret
asm_malloc:
	ld hl,0
	ret
STUBS

cat stubs.asm hal.asm app.asm zone.asm charset.asm model.asm engine.asm chat.asm > motor_body.asm
echo '; empty' > zcc_opt.def
cat "$Z8/lib/target/zx81/classic/zx81_crt0.asm" motor_body.asm > motorfull.asm
z80asm -mz80 -IXIY -b motorfull.asm -L"$Z8/lib/clibs" -I"$Z8/lib" -I. -lzx81_clib -lndos -lgfx81 -lz80iy_crt0 2>&1 | grep -E "error" | head -5
ls -la motorfull.bin 2>/dev/null && python3 -c "
d=open('/tmp/v9build/motorfull.bin','rb').read().rstrip(b'\x00')
print('MOTOR BIN:', len(d), 'B')" && echo "MOTOR OK"

echo "== boot =="
stage $P/boot16.c boot
cat stubs.asm hal.asm zone.asm boot.asm > boot_body.asm
cat "$Z8/lib/target/zx81/classic/zx81_crt0.asm" boot_body.asm > bootfull.asm
z80asm -mz80 -IXIY -b bootfull.asm -L"$Z8/lib/clibs" -I"$Z8/lib" -I. -lzx81_clib -lndos -lgfx81 -lz80iy_crt0 2>&1 | grep -E "error" | head -4
ls -la bootfull.bin 2>/dev/null && python3 -c "
d=open('/tmp/v9build/bootfull.bin','rb').read().rstrip(b'\x00')
print('BOOT BIN:', len(d), 'B')" && echo "BOOT OK"
