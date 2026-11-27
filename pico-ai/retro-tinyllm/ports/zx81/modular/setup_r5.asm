org 0x4082

entry:
    ; USR must return with BASIC's original stack intact.
    ld (savesp), sp
    di
    ld sp, 0x7F00

    ; Clear the 512-byte protected profile slot.
    ld hl, 0x7D00
    ld de, 0x7D01
    ld bc, 0x01FF
    xor a
    ld (hl), a
    ldir

    ; MEM1 magic.
    ld hl, 0x7D00
    ld (hl), 0x4D
    inc hl
    ld (hl), 0x45
    inc hl
    ld (hl), 0x4D
    inc hl
    ld (hl), 0x31
    xor a
    ld (0x7CC4), a

    ; A$ = DDMMYY
    ld hl, (0x4010)
    call readvar
    call parse_date

    ; B$ = HHMM
    call readvar
    call parse_time

    ; C$ = name
    call readvar
    ld hl, 0x7D0C
    call copy16

    ; D$ = gender: M / F / anything else
    call readvar
    ld a, (de)
    cp 0x32
    jr z, gender_m
    cp 0x2B
    jr z, gender_f
    xor a
    jr gender_store
gender_m:
    ld a, 1
    jr gender_store
gender_f:
    ld a, 2
gender_store:
    ld (0x7D2C), a

    ; E$ = instructions: Y means enabled.
    call readvar
    ld a, (de)
    cp 0x3E
    jr nz, no_instr
    ld a, 1
    ld (0x7D2E), a
no_instr:
    ; date + name + setup are known; keep those flags for the engine.
    ld a, (0x7D2E)
    or 6
    ld (0x7D2E), a

    ; Restore BASIC's SP before RET from USR.
    ld hl, (savesp)
    ld sp, hl
    ei
    ret

savesp:
    dw 0

; IN: HL = current variable, OUT: HL = next variable, DE = text, BC = length.
readvar:
    inc hl
    ld c, (hl)
    inc hl
    ld b, (hl)
    inc hl
    ld e, l
    ld d, h
    add hl, bc
    ret

; IN DE=DDMMYY. Store day/month/year in MEM.
parse_date:
    ld a, (de)
    sub 0x1C
    ld h, a
    add a, a
    add a, a
    add a, h
    add a, a
    ld c, a
    inc de
    ld a, (de)
    sub 0x1C
    add a, c
    ld (0x7D2D), a

    inc de
    ld a, (de)
    sub 0x1C
    ld h, a
    add a, a
    add a, a
    add a, h
    add a, a
    ld c, a
    inc de
    ld a, (de)
    sub 0x1C
    add a, c
    ld (0x7D07), a

    inc de
    ld a, (de)
    sub 0x1C
    ld h, a
    add a, a
    add a, a
    add a, h
    add a, a
    ld c, a
    inc de
    ld a, (de)
    sub 0x1C
    add a, c
    ld (0x7D08), a
    ret

; IN DE=HHMM. Store hour/minute.
parse_time:
    ld a, (de)
    sub 0x1C
    ld h, a
    add a, a
    add a, a
    add a, h
    add a, a
    ld c, a
    inc de
    ld a, (de)
    sub 0x1C
    add a, c
    ld (0x7D09), a

    inc de
    ld a, (de)
    sub 0x1C
    ld h, a
    add a, a
    add a, a
    add a, h
    add a, a
    ld c, a
    inc de
    ld a, (de)
    sub 0x1C
    add a, c
    ld (0x7D0A), a
    ret

; IN DE=text, BC=len, HL=destination. Copy at most 16 chars and terminate.
copy16:
    ld a, c
    cp 16
    jr c, cp_ok
    ld c, 16
cp_ok:
    ld b, 0
    ex de, hl
    ldir
    xor a
    ld (de), a
    ret
