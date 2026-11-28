        org $4082
; key test: only the keyboard scan (same KSCAN as the app), display on.
; each key press writes its index (0..39) as a character into row 6.
BOOT:   di
        ld iy,$4000
        set 6,(iy+$3b)          ; SLOW: display on
        ld hl,$7B01+6*33
        ld de,$7B01+6*33
        ld b,32
CL:     ld (hl),0
        inc hl
        djnz CL
KLOOP:  call KSCAN
        cp $FF
        jr z,KLOOP
        ld (de),a               ; store the key index
        inc de
        ld a,e
        cp $7B01+6*33+32 & $FF
        jr c,KWAIT
        ld de,$7B01+6*33        ; wrap to the row start
KWAIT:  call KSCAN              ; wait for release
        cp $FF
        jr nz,KWAIT
        jr KLOOP

; ---- keyboard: same tables and routine as src/app1.asm ----
ROWS:   db $FE,$FD,$FB,$F7,$EF,$DF,$BF,$7F
KSCAN:  ld b,$FE
        ld c,$FE
        in a,(c)
        cpl
        and 1
        ld hl,ROWS
        ld d,0
KS_ROW: ld a,(hl)
        ld b,a
        ld c,$FE
        in a,(c)
        cpl
        and $1F
        ld e,a
        ld a,d
        or a
        ld a,e
        jr nz,KS_M
        and $1E
KS_M:   or a
        jr nz,KS_HIT
        inc hl
        inc d
        ld a,d
        cp 8
        jr c,KS_ROW
        ld a,$FF
        ret
KS_HIT: ld e,0
KS_BIT: rrca
        jr c,KS_GOT
        inc e
        jr KS_BIT
KS_GOT: ld a,d
        add a,a
        add a,a
        add a,d
        add a,e
        ret
