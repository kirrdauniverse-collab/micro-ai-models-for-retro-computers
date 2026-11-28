; app3.asm - protected state: raw copy at $7F00 (survives topic LOAD),
; packed copy in D-file row 0 (survives BASIC SAVE/LOAD of the base image)
ST      equ $7F00              ; 24 bytes, above the .P image (VARS ends $7E19)
ST_NAME equ ST+3               ; 8 bytes, ZX codes, $FF padded
ST_GEN  equ ST+11              ; 1 = male, 2 = female
ST_WD   equ ST+12              ; weekday 1..7
ST_DAY  equ ST+13
ST_MON  equ ST+14
ST_HOUR equ ST+15
ST_EVT  equ ST+16              ; 0 none, 1 pain, 2 happy, 3 love, 4 tired
ST_EKEY equ ST+17              ; 2 bytes: month*31+day of the event
ST_EWD  equ ST+19              ; weekday of the event
ST_TOP  equ ST+20              ; loaded topic id (0 = base)
ST_TSH  equ ST+21              ; temperature shift 1..4
ST_GRD  equ ST+22              ; reasoning on = 1
ST_SUM  equ ST+23
ST_LEN  equ 24
SS_B0   equ $6190              ; pack temporaries
SS_B1   equ $6191
SS_B2   equ $6192

; ST_CALC: A = sum of ST[0..22]
ST_CALC: ld hl,ST
        ld b,ST_LEN-1
        xor a
SC1:    add a,(hl)
        inc hl
        djnz SC1
        ret

; ST_OK: A = 1 if raw ST region is valid, else 0
ST_OK:  ld a,(ST)
        cp 'R'
        jr nz,SO_NO
        ld a,(ST+1)
        cp 'T'
        jr nz,SO_NO
        ld a,(ST+2)
        cp 1
        jr nz,SO_NO
        call ST_CALC
        ld hl,ST_SUM
        cp (hl)
        jr nz,SO_NO
        ld a,1
        ret
SO_NO:  xor a
        ret

; ST_SAVE: checksum + raw copy + packed copy in D-file row 0 (cells 0..31)
ST_SAVE: ld a,'R'
        ld (ST),a
        ld a,'T'
        ld (ST+1),a
        ld a,1
        ld (ST+2),a
        call ST_CALC
        ld (ST_SUM),a
        ld hl,ST
        ld de,DFILE+1
        ld b,8                  ; 8 groups of 3 bytes -> 32 cells
SS_G:   push bc
        ld a,(hl)
        ld (SS_B0),a
        inc hl
        ld a,(hl)
        ld (SS_B1),a
        inc hl
        ld a,(hl)
        ld (SS_B2),a
        inc hl
        push hl
        call SS_PACK3          ; writes 4 cells at DE
        pop hl
        pop bc
        djnz SS_G
        ret

; SS_PACK3: cells c0..c3 from SS_B0..2 to (DE), DE advanced by 4
SS_PACK3: ld a,(SS_B0)
        and 63
        ld (de),a
        inc de
        ld a,(SS_B0)            ; c1 = (b0>>6) | ((b1&15)<<2)
        rlca
        rlca
        and 3
        ld c,a
        ld a,(SS_B1)
        and 15
        add a,a
        add a,a
        or c
        ld (de),a
        inc de
        ld a,(SS_B1)            ; c2 = (b1>>4) | ((b2&3)<<4)
        rrca
        rrca
        rrca
        rrca
        and 15
        ld c,a
        ld a,(SS_B2)
        and 3
        rlca
        rlca
        rlca
        rlca
        or c
        ld (de),a
        inc de
        ld a,(SS_B2)            ; c3 = b2>>2
        rrca
        rrca
        and 63
        ld (de),a
        inc de
        ret

; ST_LOAD: A = 1 if a valid state was found (raw first, then D-file copy)
ST_LOAD: call ST_OK
        or a
        ret nz
        ld hl,DFILE+1           ; unpack row 0 into raw region
        ld de,ST
        ld b,8
SL_G:   push bc
        push de
        call SU_UNPACK4         ; reads 4 cells at HL -> SS_B0..2
        pop de
        ld a,(SS_B0)
        ld (de),a
        inc de
        ld a,(SS_B1)
        ld (de),a
        inc de
        ld a,(SS_B2)
        ld (de),a
        inc de
        pop bc
        djnz SL_G
        jp ST_OK

; SU_UNPACK4: HL = 4 cells -> SS_B0..2, HL advanced by 4
SU_UNPACK4: ld a,(hl)           ; c0
        ld c,a
        inc hl
        ld a,(hl)               ; c1
        ld b,a
        inc hl
        ld a,(hl)               ; c2
        ld e,a
        inc hl
        ld a,(hl)               ; c3
        inc hl
        ld d,a
        ; b0 = c0 | ((c1&3)<<6)
        ld a,b
        and 3
        rrca
        rrca
        or c
        ld (SS_B0),a
        ; b1 = (c1>>2) | ((c2&15)<<4)
        ld a,b
        rrca
        rrca
        and 15
        ld c,a
        ld a,e
        and 15
        rlca
        rlca
        rlca
        rlca
        or c
        ld (SS_B1),a
        ; b2 = (c2>>4) | (c3<<2)
        ld a,e
        rrca
        rrca
        rrca
        rrca
        and 3
        ld c,a
        ld a,d
        rlca
        rlca
        and $FC
        or c
        ld (SS_B2),a
        ret
