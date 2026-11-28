; app1.asm - entry, keyboard matrix, console (log ring + screen redraw)
        org $4082
        jp BOOT                 ; 16514: USR entry
        jp GEN                  ; +3
        jp INIT                 ; +6
        jp FWD                  ; +9

DFILE   equ $7B00               ; D_FILE (sysvar $400C points here)
LOG     equ $6200               ; 64 rows x 32 cells chat log ring
LOGN    equ 64
LOGHEAD equ $6180               ; current log row (0..63)
COL     equ $6181              ; column in current row (0..32)
VOFF    equ $6182              ; scroll-back offset in rows (0 = live)
ROMSP   equ $6183               ; saved ROM stack pointer (2 bytes)
SHFLAG  equ $6185               ; shift key state (1 = pressed)
TOPIC   equ $6186               ; loaded topic id (0 = base)
STKTOP  equ $7EF0               ; own stack, below protected state at $7F00

K_NONE  equ $FF
K_ENTER equ $FD
K_DEL   equ $F1
K_UP    equ $F2
K_DOWN  equ $F3
K_T1    equ $F4                 ; $F4..$F7 = temperature 1..4
K_REAS  equ $F8                 ; reasoning switch
K_FAST  equ $F9                 ; SHIFT-F: fast mode on/off

BOOT:   ld (ROMSP),sp
        ld sp,STKTOP
        ld iy,$4000
        set 6,(iy+$3b)          ; SLOW mode: display stays on
        call CK_FILL            ; diagnostic canary (v1.1.5-diag)
        call APP
        ld sp,(ROMSP)
        ld bc,0
        ret

; ---- keyboard: ZX81 matrix via IN A,(C) ----
ROWS:   db $FE,$FD,$FB,$F7,$EF,$DF,$BF,$7F
KEYTAB: ; unshifted, index = row*5+bit (bit0 = leftmost key of the row)
        db $FF,63,61,40,59          ; row FE: SHIFT z x c v
        db 38,56,41,43,44           ; row FD: a s d f g
        db 54,60,42,55,57           ; row FB: q w e r t
        db 29,30,31,32,33           ; row F7: 1..5
        db 28,37,36,35,34           ; row EF: 0 9 8 7 6
        db 53,52,46,58,62           ; row DF: p o i u y
        db K_ENTER,49,48,47,45      ; row BF: ENTER l k j h
        db 0,$FF,50,51,39           ; row 7F: SPACE - m n b
KEYTABS: ; shifted (index+40)
        db $FF,14,26,15,$FF         ; FE: z=: x=, c=? v=-
        db $FF,$FF,$FF,K_FAST,$FF   ; FD: SHIFT-F = fast mode
        db $FF,$FF,$FF,$FF,$FF
        db K_T1,K_T1+1,K_T1+2,K_T1+3,$FF   ; F7: 1..4 temp, 5 unused
        db K_DEL,K_REAS,K_DEL,K_UP,K_DOWN ; EF: 0=DEL 9=REAS 8=DEL 7=UP 6=DOWN
        db $FF,$FF,$FF,$FF,$FF
        db $FF,$FF,$FF,$FF,$FF
        db 0,$FF,27,26,22           ; 7F: - - . , -

; KSCAN: A = key index 0..39 (or $FF), SHFLAG = shift state
KSCAN:  ld b,$FE
        ld c,$FE
        in a,(c)
        cpl
        and 1                   ; bit0 = SHIFT (active low)
        ld (SHFLAG),a
        ld hl,ROWS
        ld d,0                  ; row index
KS_ROW: ld a,(hl)
        ld b,a
        ld c,$FE
        in a,(c)
        cpl
        and $1F
        ld e,a                  ; pressed bits of this row
        ld a,d
        or a
        ld a,e
        jr nz,KS_M
        and $1E                 ; row 0: SHIFT (bit 0) is not a key
KS_M:   or a
        jr nz,KS_HIT
        inc hl
        inc d
        ld a,d
        cp 8
        jr c,KS_ROW
        ld a,K_NONE
        ret
KS_HIT: ld e,0                  ; bit number
KS_BIT: rrca
        jr c,KS_GOT             ; carry = this bit pressed
        inc e
        jr KS_BIT
KS_GOT: ld a,d                  ; index = row*5 + bit
        add a,a
        add a,a
        add a,d
        add a,e
        ret

; GETKEY: waits for a key press, returns A = special or ZX char code
GETKEY: call KSCAN
        cp K_NONE
        jr nz,GETKEY
GK_W:   call CLK_SYNC           ; the clock runs while waiting for a key
        ld a,(HDR_ON)
        or a
        call nz,HDR_DRAW
        call KSCAN
        cp K_NONE
        jr z,GK_W
        ld e,a
        ld d,0
        ld hl,KEYTAB
        ld a,(SHFLAG)
        or a
        jr z,GK_T
        ld hl,KEYTABS
GK_T:   add hl,de
        ld a,(hl)
        cp K_NONE
        jr z,GETKEY             ; undefined key: wait for release, retry
        ret

; ---- console ----
; log address of current row + COL into HL is done inline in PUTC
CLS:    ld hl,DFILE+1
        ld (hl),0
        ld de,DFILE+2
        ld bc,24*33-1
        ldir                    ; all cells blank
        ld hl,DFILE
        ld b,25
CLS2:   ld (hl),$76             ; header + 24 row ends
        ld de,33
        add hl,de
        djnz CLS2
        xor a
        ld (LOGHEAD),a
        ld (COL),a
        ld (VOFF),a
        ld hl,LOG
        ld de,LOG+1
        ld bc,LOGN*32-1
        ld (hl),0
        ldir
        ret

; PUTC: A = ZX char code, 118 = newline
PUTC:   push af                 ; wrapper: keeps all registers
        push bc
        push de
        push hl
        call PUTC_I
        pop hl
        pop de
        pop bc
        pop af
        ret

PUTC_I: cp 118
        jp z,NEWLINE
        push af
        ld a,(COL)
        cp 32
        jr c,PC_W
        call NEWLINE
PC_W:   call ROWADDR           ; HL = LOG + head*32
        ld a,(COL)
        ld e,a
        ld d,0
        add hl,de
        pop af
        ld (hl),a
        ld a,(COL)
        inc a
        ld (COL),a
        ld a,(VOFF)
        or a
        ret nz
        jp REDRAW

; HL = LOG + LOGHEAD*32
ROWADDR: ld hl,0
        ld a,(LOGHEAD)
        ld l,a
        ld b,5
RA1:    add hl,hl
        djnz RA1
        ld de,LOG
        add hl,de
        ret

NEWLINE: ld a,(LOGHEAD)
        inc a
        and LOGN-1
        ld (LOGHEAD),a
        xor a
        ld (COL),a
        call ROWADDR
        ld b,32
        xor a
NL1:    ld (hl),a
        inc hl
        djnz NL1
        ld a,(VOFF)
        or a
        ret nz
        jp REDRAW

; REDRAW: 16 visible rows (screen 8..23) from log, honouring VOFF
REDRAW: ld a,(LOGHEAD)
        ld hl,VOFF
        sub (hl)
        sub 20
        ld (RD_B),a             ; first visible log row (mod 64)
        ld hl,DFILE+1+3*33      ; chat area: screen rows 3..23 (rows 0..2 = header)
        ld (RD_D),hl
        xor a
        ld (RD_R),a
RD1:    ld a,(RD_B)
        ld hl,RD_R
        add a,(hl)
        and LOGN-1
        ld l,a
        ld h,0
        ld b,5
RD2:    add hl,hl
        djnz RD2
        ld de,LOG
        add hl,de               ; HL = source row
        ld de,(RD_D)            ; DE = destination
        ld bc,32
        ldir
        ld hl,(RD_D)
        ld de,33
        add hl,de
        ld (RD_D),hl
        ld hl,RD_R
        inc (hl)
        ld a,(hl)
        cp 21
        jr c,RD1
        ret
RD_B:   db 0
RD_R:   db 0
RD_D:   dw 0
