; app6.asm - RT-turbo tape loader: BUILT BUT INACTIVE (TURBO_ON = 0, never called)
; For real hardware with a fast tape interface. Not tested on a real ZX81.
TURBO_ON equ 0
TL_TH   equ 6                   ; loops: half-period threshold (long = bit 1)

; TL_EDGE: waits for the EAR level (port $FE bit 7) to change; B = loops taken
; carry set on timeout
TL_EDGE: in a,($FE)
        and $80
        ld e,a
        ld b,0
TL_E1:  djnz TL_E2
        scf
        ret
TL_E2:  in a,($FE)
        and $80
        cp e
        jr z,TL_E1
        ld a,b
        ld (TL_LAST),a
        or a
        ret

; TL_BYTE: reads one byte (MSB first) into A; carry set on timeout
TL_BYTE: ld c,8
        ld d,0
TL_BIT: call TL_EDGE
        ret c
        call TL_EDGE
        ret c
        ld a,(TL_LAST)
        cp TL_TH
        ld a,d
        rla
        ld d,a
        dec c
        jr nz,TL_BIT
        ld a,d
        or a
        ret

; TURBO_LOAD: HL = destination, DE = length. Returns carry set on error.
TURBO_LOAD: ld a,(TURBO_ON)
        or a
        ret z                   ; inactive: returns at once
TL_LOOP: call TL_BYTE
        ret c
        ld (hl),a
        inc hl
        dec de
        ld a,d
        or e
        jr nz,TL_LOOP
        or a
        ret
TL_LAST: db 0
