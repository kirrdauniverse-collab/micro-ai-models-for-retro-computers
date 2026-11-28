        org $4082
; minimal display test: writes HELLO on screen row 5, then loops forever
BOOT:   ld iy,$4000
        set 6,(iy+$3b)          ; SLOW: display on
        ld hl,MSG
        ld de,$7B01+5*33
        ld bc,5
        ldir
MLOOP:  jr MLOOP
MSG:    db 45,42,48,48,51       ; H E L L O (ZX codes)
