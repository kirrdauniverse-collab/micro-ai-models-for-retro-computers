#!/bin/bash
# build_v090.sh - a v0.9.0 motor leforditasa z88dk 2.5-tel (a v0.5.4/v0.6.5
# 1.8-as recegtje alapjan, -startup=2 = SLOW boot).
# A toolchain: /tmp/build/z88dk (forrasbol forditva, l. GLM/STATE.md 11. menet)
set -e
Z8=/tmp/build/z88dk
export PATH=$Z8/bin:$PATH
export ZCCCFG=$Z8/lib/config
V=/home/z/my-project/GLM/v090
E=$V/engine
P=$V/port
DEFS="-DRT_MAX_VOCAB=48 -DRT_MAX_CTX=8 -DRT_MAX_EMB=16 -DRT_MAX_HID=48 \
      -DRT_APP_MODEL_MAX=10240 -DRT_MEM_MAX=6 -DRT_JOURNAL_MAX=8 -DRT_LINE_MAX=64"

echo "== motor (chat + zone) =="
cd $V/build
zcc +zx81 -vn -O3 -startup=2 $DEFS -I$E -o motor \
    $P/hal_zx81.c $P/app16.c $P/zone.c \
    $E/rt_charset.c $E/rt_model.c $E/rt_engine.c $E/rt_chat.c \
    $E/rt_memory.c $E/rt_tape.c $E/rt_clock.c $E/rt_router.c \
    $E/rt_journal.c $E/rt_scratch.c
echo "== boot =="
zcc +zx81 -vn -O3 -startup=2 -I$E -o boot \
    $P/hal_zx81.c $P/boot16.c
echo "== kesz =="
ls -la motor.bin boot.bin 2>/dev/null || ls -la motor boot
