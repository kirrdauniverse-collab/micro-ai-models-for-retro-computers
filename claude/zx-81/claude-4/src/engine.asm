; engine.asm - RTLM v2 class-F forward pass + sampler for ZX81 (16K)
; Entry points (USR addresses):  16514 GEN  (chat turn)
;                                16517 INIT (clear context window)
;                                16520 FWD  (forward only, for tests)
; Input for GEN: INBUF[0]=n, INBUF[1..n]=ZX81 char codes.
; Output: reply chars printed with RST 10 (ROM PRINT-A), newline ends.
; Settings (POKE by frame): TSH (temp shift 1..4), GREEDY (0/1).

; ---------- fixed layout (see tools/build_engine.py) ----------
SQB     equ $6C00          ; sq[n] = floor(n*n/4) at SQB+2n, n in [-256,255] (table $6A00..$6DFF)
EXPS    equ $6E00          ; 256 bytes ($6E00..$6EFF): min(255, round(exp(-k/8)*4096)>>4)
MODEL   equ $5500
EMB     equ MODEL+92       ; 45*10 int8
SH1     equ EMB+450        ; 16 u8
W1      equ SH1+16         ; 16*81 int8
SHO     equ W1+1296        ; 45 u8
WO      equ SHO+45         ; 45*17 int8
MAPIN_T equ $5F80          ; 64 entries: ZX81 code -> model index
MAPOUT_T equ $5FC0         ; 45 entries: model index -> ZX81 code
BUF     equ $6000
WIN     equ BUF            ; 8 bytes context window (model indices)
INBUF   equ BUF+$10        ; 34 bytes
XBUF    equ BUF+$40        ; 80 bytes embeddings
HBUF    equ BUF+$90        ; 16 bytes hidden
LGBUF   equ BUF+$A0        ; 45 x u16 logits (biased +$8000)
WBUF    equ BUF+$100       ; 45 bytes sampling weights
ACC     equ BUF+$140       ; 4 bytes int32 accumulator
XP      equ BUF+$144
WP      equ BUF+$146
CNT     equ BUF+$148
SHP     equ BUF+$149
SHV     equ BUF+$14B
XV      equ BUF+$14C
WV      equ BUF+$14D
HP      equ BUF+$14E
LP      equ BUF+$150
XD      equ BUF+$152
CI      equ BUF+$154
OC      equ BUF+$155
MV      equ BUF+$156
BI      equ BUF+$158
SUMW    equ BUF+$159
WPW     equ BUF+$15B
RN      equ BUF+$15D
CUM     equ BUF+$15F
CIDX    equ BUF+$161
RS      equ BUF+$162       ; 16-bit LFSR state
TSH     equ BUF+$164
GREEDY  equ BUF+$165
TRIES   equ BUF+$166
NOUT    equ BUF+$167
CUR     equ BUF+$168
MAXNEW  equ 60

; ---------- chat turn ----------
GEN:
        ld a,(INBUF)
        or a
        jr z,GEN_GO
        ld b,a
        ld hl,INBUF+1
GI_LOOP:
        push bc
        push hl
        ld a,(hl)
        call MAPIN
        call PUSHWIN
        pop hl
        inc hl
        pop bc
        djnz GI_LOOP
        xor a                   ; the training lines are "question<newline>answer"
        call PUSHWIN            ; model index 0 = newline ends the user's line
GEN_GO:
        ld a,3
        ld (TRIES),a
        xor a
        ld (NOUT),a
GEN_STEP:
        call TICK_SLOW          ; frames of the SLOW part since the last tick
        ld a,(FASTF)
        or a
        jr z,GS_SLOW
        res 6,(iy+$3b)          ; SHIFT-F: FAST mode for the forward pass only
        call FORWARD
        set 6,(iy+$3b)          ; back to SLOW: display and FRAMES run again
        call TICK_FAST          ; the FAST pass counted as an estimate
        jr GS_SAMPLE
GS_SLOW: call FORWARD           ; default: display stays on, the reply is printed live
GS_SAMPLE: call SAMPLE
        or a
        jr nz,GEN_CHAR
        ld a,(NOUT)             ; newline: end, unless nothing printed yet
        or a
        jr nz,GEN_END
        ld a,(TRIES)
        or a
        jr z,GEN_END
        dec a
        ld (TRIES),a
        jr GEN_STEP
GEN_CHAR:
        ld (CUR),a
        call MAPOUT
        call PUTC
        ld a,(CUR)
        call PUSHWIN
        ld a,(NOUT)
        inc a
        ld (NOUT),a
        cp MAXNEW
        jr c,GEN_STEP
GEN_END:
        call TICK_SLOW
        ld a,118                ; ZX81 newline
        call PUTC
        ld bc,0
        ret

; ---------- INIT: context window = spaces (model index 1), rand seed ----------
INIT:
        ld hl,WIN
        ld (hl),1
        ld de,WIN+1
        ld bc,7
        ldir
        ld hl,$ACE1
        ld (RS),hl
        ld a,1
        ld (TSH),a
        ld a,1
        ld (GREEDY),a
        ld bc,0
        ret

; A = model index -> push into window (shift left, append)
PUSHWIN:
        ld hl,WIN+1
        ld de,WIN
        ld bc,7
        ldir
        ld (WIN+7),a
        ret

; A = ZX81 code -> A = model index
MAPIN:
        and $3F
        ld hl,MAPIN_T
        add a,l
        ld l,a
        ld a,0
        adc a,h
        ld h,a
        ld a,(hl)
        ret

; A = model index -> A = ZX81 code
MAPOUT:
        ld hl,MAPOUT_T
        add a,l
        ld l,a
        ld a,0
        adc a,h
        ld h,a
        ld a,(hl)
        ret

; ---------- forward pass (FWD entry) ----------
FWD:
FORWARD:
        ld hl,XBUF
        ld (XD),hl
        xor a
        ld (CI),a
FE_I:
        ld a,(CI)
        ld hl,WIN
        ld e,a
        ld d,0
        add hl,de               ; &WIN[i]
        ld a,(hl)
        ld e,a
        ld d,0                  ; DE = idx
        ld hl,0
        ld b,10
FE_M:
        add hl,de
        djnz FE_M               ; HL = idx*10
        ld de,EMB
        add hl,de               ; source row
        ld de,(XD)
        ld bc,10
        ldir
        ld (XD),de
        ld a,(CI)
        inc a
        ld (CI),a
        cp 8
        jr c,FE_I
        ; ---- layer 1: 16 hidden, row = 81 (80 weights + bias), clamp [0,127]
        ld hl,W1
        ld (WP),hl
        ld hl,SH1
        ld (SHP),hl
        ld hl,HBUF
        ld (HP),hl
        ld a,16
        ld (OC),a
L1_LOOP:
        ld hl,XBUF
        ld (XP),hl
        ld a,80
        ld (CNT),a
        call DOTROW
        call SHIFT_ROW
        ld a,(ACC+3)           ; negative -> 0
        bit 7,a
        jr z,L1_POS
        xor a
        jr L1_STORE
L1_POS:
        ld hl,(ACC+2)
        ld a,h
        or l
        jr nz,L1_MAX           ; high word nonzero -> >=65536 -> 127
        ld a,(ACC)
        cp 128
        jr c,L1_STORE
L1_MAX:
        ld a,127
L1_STORE:
        ld hl,(HP)
        ld (hl),a
        inc hl
        ld (HP),hl
        ld hl,(WP)
        ld de,81
        add hl,de
        ld (WP),hl
        ld a,(OC)
        dec a
        ld (OC),a
        jr nz,L1_LOOP
        ; ---- layer 2: 45 logits, row = 17 (16 weights + bias), int16 with +$8000
        ld hl,WO
        ld (WP),hl
        ld hl,SHO
        ld (SHP),hl
        ld hl,LGBUF
        ld (LP),hl
        ld a,45
        ld (OC),a
L2_LOOP:
        ld hl,HBUF
        ld (XP),hl
        ld a,16
        ld (CNT),a
        call DOTROW
        call SHIFT_ROW
        ld hl,(LP)
        ld a,(ACC)
        ld (hl),a
        inc hl
        ld a,(ACC+1)
        xor $80                 ; bias: flips sign bit = +$8000
        ld (hl),a
        inc hl
        ld (LP),hl
        ld hl,(WP)
        ld de,17
        add hl,de
        ld (WP),hl
        ld a,(OC)
        dec a
        ld (OC),a
        jr nz,L2_LOOP
        ret

; ACC = sum_i XP[i]*WP[i] + 128*WP[CNT]   (int32)
DOTROW:
        ld hl,0
        ld (ACC),hl
        ld (ACC+2),hl
        ld hl,(XP)
        ld de,(WP)
        ld a,(CNT)
        ld b,a
DR1:
        push bc
        push hl
        push de
        ld a,(hl)
        ld (XV),a
        ld a,(de)
        ld (WV),a
        call MUL
        call ACCADD
        pop de
        pop hl
        pop bc
        inc hl
        inc de
        djnz DR1
        ld a,(de)               ; bias weight * 128
        ld l,a
        rlca
        sbc a,a
        ld h,a
        ld b,7
DR2:
        add hl,hl
        djnz DR2
        ex de,hl
        call ACCADD
        ret

; ACC >>= (SHP) and advance SHP (arithmetic, 32-bit)
SHIFT_ROW:
        ld hl,(SHP)
        ld a,(hl)
        ld (SHV),a
        inc hl
        ld (SHP),hl
        or a
        ret z
        ld b,a
SR1:
        ld hl,(ACC+2)
        sra h
        rr l
        ld (ACC+2),hl
        ld hl,(ACC)
        rr h
        rr l
        ld (ACC),hl
        djnz SR1
        ret

; DE = XV*WV (signed 8x8 -> signed 16), quarter-square table
MUL:
        ld a,(XV)
        ld l,a
        rlca
        sbc a,a
        ld h,a                  ; HL = sext(a)
        ld a,(WV)
        ld e,a
        rlca
        sbc a,a
        ld d,a                  ; DE = sext(b)
        ld b,h
        ld c,l                  ; BC = a
        add hl,de               ; HL = a+b
        ex de,hl                ; DE = a+b, HL = b
        ld a,c
        sub l
        ld l,a
        ld a,b
        sbc a,h
        ld h,a                  ; HL = a-b
        ex de,hl                ; DE = a-b, HL = a+b
        add hl,hl
        ld bc,SQB
        add hl,bc
        ld a,(hl)
        inc hl
        ld h,(hl)
        ld l,a                  ; HL = sq[a+b]
        ex de,hl                ; DE = sq[a+b], HL = a-b
        add hl,hl
        ld bc,SQB
        add hl,bc
        ld a,(hl)
        inc hl
        ld h,(hl)
        ld l,a                  ; HL = sq[a-b]
        ex de,hl                ; HL = sq[a+b], DE = sq[a-b]
        or a
        sbc hl,de
        ex de,hl                ; DE = product
        ret

; ACC += DE (signed 16, sign-extended to 32)
ACCADD:
        ld hl,(ACC)
        add hl,de
        ld (ACC),hl
        ld hl,(ACC+2)
        ld a,0
        adc a,0
        ld c,a
        bit 7,d
        jr z,AA1
        dec hl
AA1:
        ld a,c
        ld e,a
        ld d,0
        add hl,de
        ld (ACC+2),hl
        ret

; ---------- sampling: A = chosen model index ----------
SAMPLE:
        ld hl,LGBUF
        ld e,(hl)
        inc hl
        ld d,(hl)
        inc hl
        ld (MV),de
        xor a
        ld (BI),a
        ld c,1
        ld b,44
SM_MAX:
        ld e,(hl)
        inc hl
        ld d,(hl)
        inc hl
        push hl
        ld hl,(MV)
        or a
        sbc hl,de               ; carry iff MV < LG
        pop hl
        jr nc,SM_NX
        ld (MV),de
        ld a,c
        ld (BI),a
SM_NX:
        inc c
        djnz SM_MAX
        ld a,(GREEDY)
        or a
        jr z,SM_SAMP
        ld a,(BI)
        ret
SM_SAMP:
        ld hl,0
        ld (SUMW),hl
        ld hl,LGBUF
        ld (LP),hl
        ld hl,WBUF
        ld (WPW),hl
        ld a,45
        ld (OC),a
SW1:
        ld hl,(LP)
        ld e,(hl)
        inc hl
        ld d,(hl)
        inc hl
        ld (LP),hl
        ld hl,(MV)
        or a
        sbc hl,de               ; HL = d = MV - LG (>= 0)
        ld a,(TSH)
        or a
        jr z,SW_T0
        ld b,a
SW_T:
        srl h
        rr l
        djnz SW_T
SW_T0:
        srl h
        rr l
        srl h
        rr l
        srl h
        rr l                    ; HL = d >> 3
        ld a,h
        or a
        jr z,SW_K
        ld l,255
SW_K:
        ld h,0
        ld de,EXPS
        add hl,de
        ld a,(hl)               ; weight
        ld hl,(WPW)
        ld (hl),a
        inc hl
        ld (WPW),hl
        ld e,a
        ld d,0
        ld hl,(SUMW)
        add hl,de
        ld (SUMW),hl
        ld a,(OC)
        dec a
        ld (OC),a
        jr nz,SW1
        ld hl,(SUMW)
        ld a,h
        or l
        jr nz,SW_RND
        ld a,(BI)
        ret
SW_RND:
        ; xorshift-style 16-bit LFSR step: x = (x>>1) ^ ($B400 if bit0)
        ld hl,(RS)
        srl h
        rr l
        jr nc,SW_NOXOR
        ld a,h
        xor $B4
        ld h,a
SW_NOXOR:
        ld (RS),hl
        ; r = rnd mod sum
        ld de,(SUMW)
SW_MOD:
        or a
        sbc hl,de
        jr nc,SW_MOD
        add hl,de
        ld (RN),hl
        ; pick: first i with r < cum
        ld hl,0
        ld (CUM),hl
        ld hl,WBUF
        ld (WPW),hl
        xor a
        ld (CIDX),a
        ld a,45
        ld (OC),a
SW_PICK:
        ld hl,(WPW)
        ld e,(hl)
        inc hl
        ld (WPW),hl
        ld d,0
        ld hl,(CUM)
        add hl,de
        ld (CUM),hl
        ld de,(CUM)
        ld hl,(RN)
        or a
        sbc hl,de               ; carry iff r < cum
        jr c,SW_HIT
        ld a,(CIDX)
        inc a
        ld (CIDX),a
        ld a,(OC)
        dec a
        ld (OC),a
        jr nz,SW_PICK
        ld a,(BI)
        ret
SW_HIT:
        ld a,(CIDX)
        ret
