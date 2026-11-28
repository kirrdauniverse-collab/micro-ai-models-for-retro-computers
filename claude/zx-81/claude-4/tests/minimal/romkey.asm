        org $4082
; ROM key test: calls the ROM KEYBOARD ($02BB) and DECODE ($07BD) in a loop
; and shows their results as hex digits on screen (rows 5 and 6).
BOOT:   di
        ld iy,$4000
        set 6,(iy+$3b)          ; SLOW: display on
RLOOP:  call $02BB              ; KEYBOARD -> HL
        ld ($6300),hl
        call $07BD              ; DECODE -> A
        ld ($6302),a
        call SHOW
        jr RLOOP

; SHOW: "HL=hhhh" on row 5, "A=hh" on row 6
SHOW:   ld hl,$7B01+5*33
        ld (hl),45              ; H
        inc hl
        ld (hl),49              ; L
        inc hl
        ld (hl),20              ; =
        inc hl
        ld a,($6301)
        call HEX2
        ld a,($6300)
        call HEX2
        ld hl,$7B01+6*33
        ld (hl),38              ; A
        inc hl
        ld (hl),20              ; =
        inc hl
        ld a,($6302)
        call HEX2
        ret

HEX2:   push af
        rrca
        rrca
        rrca
        rrca
        call HEX1
        pop af
        call HEX1
        ret

HEX1:   and $0F
        add a,28                ; 0..9 -> 28..37, A..F -> 38..43
        ld (hl),a
        inc hl
        ret
