        org $4082
; same as MINTEST, but with interrupts disabled and IM 0 first
BOOT:   di
        im 0
        ld iy,$4000
        set 6,(iy+$3b)          ; SLOW: display on
        ld hl,MSG
        ld de,$7B01+5*33
        ld bc,5
        ldir
MLOOP:  jr MLOOP
MSG:    db 45,42,49,49,52       ; H E L L O
