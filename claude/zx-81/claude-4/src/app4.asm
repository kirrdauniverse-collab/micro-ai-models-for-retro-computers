; app4.asm - title, manual, setup dialogue, memory check
; string conventions: zn "..." = ZX codes, zs "..." = ZX codes + $FF end,
; $FE inside a string = newline (PUTS only); the builder converts zn/zs.
TOPIC_ID equ $5F6A             ; byte written by the builder after the model
STR_END equ $FF
STR_NL  equ $FE

; PUTS: HL = string -> console (PUTC); $FE = newline, $FF = end
PUTS:   call PUTS2              ; string, then newline
        ld a,118
        jp PUTC

PUTS2:  ld a,(hl)              ; string without the final newline
        cp STR_END
        ret z
        inc hl
        push hl
        cp STR_NL
        jr nz,PS_C
        ld a,118
PS_C:   call PUTC
        pop hl
        jr PUTS2

; PUTD: HL = string -> D-file at DE directly (no newline handling)
PUTD:   ld a,(hl)
        cp STR_END
        ret z
        ld (de),a
        inc hl
        inc de
        jr PUTD

; DF_ROW: A = screen row -> DE = D-file address of its column 0
DF_ROW: ld h,0
        ld l,a
        ld e,a
        ld d,0
        ld b,5
DFR1:   add hl,hl
        djnz DFR1               ; hl = row*32
        add hl,de               ; hl = row*33
        ld de,DFILE+1
        add hl,de
        ex de,hl
        ret

; TITLE: boxed title on screen rows 1..6, waits for a key
TITLE:  call CLS
        ld a,1
        call DF_ROW
        ld hl,S_BOX1
        call PUTD
        ld a,2
        call DF_ROW
        ld hl,S_BOX2
        call PUTD
        ld a,3
        call DF_ROW
        ld hl,S_BOX3
        call PUTD
        ld a,4
        call DF_ROW
        ld hl,S_BOX1
        call PUTD
        ld a,6
        call DF_ROW
        ld hl,S_PRESS
        call PUTD
        call GETKEY
        call CLS
        ret
S_BOX1:  zs "**************************"
S_BOX2:  zs "*   CRICKET-81  V1.1.6   *"
S_BOX3:  zs "*   ZX81 AI - CLAUDE-4   *"
S_PRESS: zs "   BILLENTYU A FOLYTATAHOZ"

; ASK_MANUAL: asks for the manual and prints it when wanted
ASK_MANUAL:
        ld hl,S_Q_MAN
        call PUTS
        call YESNO
        or a
        ret z
        ld hl,S_MAN
        call PUTS
        call GETKEY
        ret
S_Q_MAN: zs "KELL HASZNALATI UTMUTATO? (Y/N)"
S_MAN:   zn "IRJ, ENTER-REL KULDD. SHIFT+6/7"
        db STR_NL
        zn "GORGETES. SHIFT+1..4 HOMERSEKLET."
        db STR_NL
        zn "SHIFT+9 GONDOLKODAS BE/KI."
        db STR_NL
        zn "QUIT = KILEPES, HELP = SEGITSEG."
        db STR_NL
        zs "BILLENTYU A FOLYTATASHOZ."

; YESNO: waits for Y (returns A=1) or N (returns A=0)
YESNO:  call GETKEY
        cp 62                   ; ZX 'Y'
        jr z,YN_Y
        cp 51                   ; ZX 'N'
        jr nz,YESNO
        xor a
        ret
YN_Y:   ld a,1
        ret

; SETUP: weekday, date, hour, name, gender; then saves the state
SETUP:  call SETUP_DATE
        jp SETUP_NAME

SETUP_DATE: ld hl,S_Q_WD
        call PUTS
        call READ_LINE
        ld a,(INBUF+1)
        sub 28
        ld (ST_WD),a
        ld hl,S_Q_DATE
        call PUTS
        call READ_LINE
        ld hl,INBUF+1
        ld a,(INBUF)
        ld b,a
        call PARSE2             ; A = first, E = second
        ld (ST_DAY),a
        ld a,e
        ld (ST_MON),a
        ld hl,S_Q_HOUR
        call PUTS
        call READ_LINE
        ld hl,INBUF+1
        ld a,(INBUF)
        ld b,a
        call PARSE2             ; A = hour, E = minute
        call SET_CLOCK
        ret

SETUP_NAME:
        ld hl,S_Q_NAME
        call PUTS
        call READ_LINE
        ld hl,ST_NAME           ; copy up to 8 chars, pad with spaces
        ld b,8
        ld de,INBUF+1
        ld a,(INBUF)
        ld c,a
SU_N:   ld a,c
        or a
        jr z,SU_PAD
        ld a,(de)
        inc de
        dec c
        jr SU_PUT
SU_PAD: xor a
SU_PUT: ld (hl),a
        inc hl
        djnz SU_N
        ld hl,S_Q_GEN
        call PUTS
SU_G:   call GETKEY
        cp 43                   ; ZX 'F' = male
        jr nz,SU_G2
        ld a,1
        jr SU_SET
SU_G2:  cp 51                   ; ZX 'N' = female
        jr nz,SU_G
        ld a,2
SU_SET: ld (ST_GEN),a
        xor a
        ld (ST_EVT),a
        ld a,1
        ld (ST_GRD),a           ; reasoning (greedy) on by default
        ld a,1
        ld (ST_TSH),a           ; temperature shift 1 by default
        ld hl,S_OK
        call PUTS
        call ST_SAVE
        ret
S_Q_WD:   zs "HANYADIK NAP? (1=HETFO)"
S_Q_DATE: zs "DATUM (NAP HO, PL 21 11):"
S_Q_HOUR: zs "IDO (OO PP), PL 14 05:"
S_Q_NAME: zs "NEVED (MAX 8 BETU):"
S_Q_GEN:  zs "FERFI=F, NO=N (NYOMJ EGYET):"
S_OK:     zs "KOSZONOM, MENTETTEM."

; PARSE2: INBUF text "a b", B = length, HL = text -> A = first, E = second
PARSE2: call PNUM
        push af
        call PNUM
        ld e,a
        pop af
        ret

; PNUM: skips non-digits, reads digits (B counts down), returns A
PNUM:   ld c,0
PN_SP:  ld a,b
        or a
        jr z,PN_END
        ld a,(hl)
        cp 28                   ; '0'
        jr c,PN_SK
        cp 38                   ; past '9'
        jr c,PN_DIG
PN_SK:  inc hl
        dec b
        jr PN_SP
PN_DIG: ld a,c
        add a,a
        ld d,a
        add a,a
        add a,a
        add a,d                 ; a = c*10
        ld c,a
        ld a,(hl)
        sub 28
        add a,c
        ld c,a
        inc hl
        dec b
        jr z,PN_END
        ld a,(hl)
        cp 28
        jr c,PN_END
        cp 38
        jr c,PN_DIG
PN_END: ld a,c
        ret

; TODAYKEY: HL = month*31 + day
TODAYKEY: ld a,(ST_MON)
        ld e,a
        ld d,0
        ld h,d
        ld l,e
        ld b,5
TK1:    add hl,hl
        djnz TK1                ; hl = month*32
        or a
        sbc hl,de               ; hl = month*31
        ld a,(ST_DAY)
        ld e,a
        ld d,0
        add hl,de
        ret

; EVENT_CHECK: a pain noted within the last 1..7 days is asked about
EVENT_CHECK:
        ld a,(ST_EVT)
        cp 1
        ret nz
        call TODAYKEY
        ld de,(ST_EKEY)
        or a
        sbc hl,de               ; hl = today - event day
        ret c
        ld a,h
        or a
        ret nz
        ld a,l
        or a
        ret z
        cp 8
        ret nc
        ld hl,S_STILL
        call PUTS
        call YESNO
        or a
        ret nz
        xor a
        ld (ST_EVT),a
        call ST_SAVE
        ret
S_STILL: zs "FAJ MEG A FEJED? (Y/N)"
