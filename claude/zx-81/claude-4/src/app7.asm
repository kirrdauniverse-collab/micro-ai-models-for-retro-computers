; app7.asm - clock, header rows 0..2, chat header rows (inverse video)
; FRAMES ($4034, 16 bit) counts 50 per second (PAL) and runs down; it is
; frozen in FAST mode, so the forward pass is added as an estimate (FWD_FR).
FRAMES   equ $4034
FWD_FR   equ 20                 ; estimated frames (1/50 s) of one forward pass
HDRB     equ $6198              ; 32-cell build buffer (ZX codes)
HB_P     equ $61B8              ; build pointer
CLK_MIN  equ $61BA              ; minute of the day 0..1439
CLK_FR   equ $61BC              ; frames inside the current minute 0..2999
CLK_F    equ $61BE              ; FRAMES value at the last sync
GFR      equ $61C0              ; frames of the current reply (SLOW + FAST estimate)
SESS_TOK equ $61C2              ; characters in + out of this session
HDR_ROW  equ $61C4              ; LOG row of the open chat header
HDR_ON   equ $61C5              ; 1 once the chat has started
HDR_H    equ $61C6
HDR_M    equ $61C7
DECV     equ $61C8              ; 2 bytes
DECST    equ $61CA
DECI     equ $61CB
FASTF    equ $61CC              ; 1 = FAST mode (display off while computing)

; ---------- clock ----------
; SET_CLOCK: A = hour, E = minute (from PARSE2); starts the clock now
SET_CLOCK:
        cp 24
        jr c,SCK1
        xor a
SCK1:   ld (ST_HOUR),a
        ld b,a
        ld a,e
        cp 60
        jr c,SCK2
        xor a
SCK2:   ld c,a                  ; C = minute
        ld hl,0
        ld de,60
        ld a,b
        or a
        jr z,SCK4
SCK3:   add hl,de
        djnz SCK3
SCK4:   ld e,c
        ld d,0
        add hl,de
        ld (CLK_MIN),hl
        ld hl,0
        ld (CLK_FR),hl
        ld hl,(FRAMES)
        ld (CLK_F),hl
        ret

; CLK_SYNC: advances the clock by the frames elapsed since the last sync
CLK_SYNC:
        ld hl,(CLK_F)
        ld de,(FRAMES)
        ld (CLK_F),de
        or a
        sbc hl,de               ; old - new: FRAMES counts down
        jp CLK_ADDF

; TICK_SLOW: as CLK_SYNC, and the same frames count towards the reply time
TICK_SLOW:
        ld hl,(CLK_F)
        ld de,(FRAMES)
        ld (CLK_F),de
        or a
        sbc hl,de
        push hl
        call CLK_ADDF
        pop hl
        ld de,(GFR)
        add hl,de
        ld (GFR),hl
        ret

; TICK_FAST: one forward pass ran with FRAMES frozen: add its estimate
TICK_FAST:
        ld hl,FWD_FR
        push hl
        call CLK_ADDF
        pop hl
        ld de,(GFR)
        add hl,de
        ld (GFR),hl
        ret

; CLK_ADDF: HL = frames to add to the clock
CLK_ADDF:
        ld de,(CLK_FR)
        add hl,de
CAF1:   ld de,3000
        or a
        sbc hl,de
        jr nc,CAF2
        add hl,de
        ld (CLK_FR),hl
        ret
CAF2:   push hl
        ld hl,(CLK_MIN)
        inc hl
        ld de,1440
        or a
        sbc hl,de
        jr c,CAF3
        ld hl,0
        jr CAF4
CAF3:   add hl,de
CAF4:   ld (CLK_MIN),hl
        pop hl
        jr CAF1

; HM_SPLIT: HL = minute of the day -> A = hour, E = minute
HM_SPLIT:
        ld bc,0
HMS1:   ld de,60
        or a
        sbc hl,de
        jr c,HMS2
        inc bc
        jr HMS1
HMS2:   add hl,de
        ld e,l
        ld a,c
        ret

; DIVMOD: HL / DE -> BC = quotient, HL = remainder (DE > 0)
DIVMOD: ld bc,0
DM1:    or a
        sbc hl,de
        jr c,DM2
        inc bc
        jr DM1
DM2:    add hl,de
        ret

; ---------- build buffer (32 cells, ZX codes) ----------
HB_BEGIN:
        ld hl,HDRB
        ld (HB_P),hl
        ret

; HB_CH: A = ZX code -> next cell
; (v1.1.7-diag) bounds check: HB_P sits right after HDRB ($61B8), so a write past
; cell 31 would overwrite HB_P itself and the next write goes to a random address.
HB_CH:  push hl
        push de
        ld hl,(HB_P)
        ld de,HDRB+32
        or a
        sbc hl,de               ; carry set when HB_P < end of buffer
        jr nc,HBC_SKIP          ; no room: drop the character
        add hl,de               ; HL = HB_P again
        ld (hl),a
        inc hl
        ld (HB_P),hl
HBC_SKIP: pop de
        pop hl
        ret

; HB_S: HL = $FF-terminated ZX string -> buffer
HB_S:   ld a,(hl)
        cp STR_END
        ret z
        call HB_CH
        inc hl
        jr HB_S

; HB_2: A = 0..99 -> two digits
HB_2:   ld b,0
H2A:    cp 10
        jr c,H2B
        sub 10
        inc b
        jr H2A
H2B:    push af
        ld a,b
        add a,28
        call HB_CH
        pop af
        add a,28
        jp HB_CH

; HB_PAD: fills the buffer up to 32 cells with spaces
HB_PAD: ld hl,(HB_P)
        ld de,HDRB+32
        or a
        sbc hl,de
        ret nc
        xor a
        call HB_CH
        jr HB_PAD

; DECW: HL = value -> decimal digits into the buffer (no leading zeros)
DECW:   ld (DECV),hl
        xor a
        ld (DECST),a
        ld (DECI),a
DW1:    ld a,(DECI)
        add a,a
        ld e,a
        ld d,0
        ld hl,DECTAB
        add hl,de
        ld e,(hl)
        inc hl
        ld d,(hl)               ; DE = divisor
        ld c,0
        ld hl,(DECV)
DW2:    or a
        sbc hl,de
        jr c,DW3
        inc c
        jr DW2
DW3:    add hl,de
        ld (DECV),hl
        ld a,(DECI)
        cp 4
        jr z,DW4                ; last digit is always written
        ld a,c
        or a
        jr nz,DW4
        ld a,(DECST)
        or a
        jr z,DW5                ; leading zero: skipped
DW4:    ld a,1
        ld (DECST),a
        ld a,c
        add a,28
        call HB_CH
DW5:    ld a,(DECI)
        inc a
        ld (DECI),a
        cp 5
        jr c,DW1
        ret
DECTAB: dw 10000,1000,100,10,1

; WD_NAME: A = weekday 1..7 -> HL = name
WD_NAME:
        cp 1
        jr c,WDB
        cp 8
        jr nc,WDB
        dec a
        add a,a
        ld e,a
        ld d,0
        ld hl,WD_TAB
        add hl,de
        ld e,(hl)
        inc hl
        ld d,(hl)
        ex de,hl
        ret
WDB:    ld hl,H_QM
        ret
WD_TAB: dw WD1,WD2,WD3,WD4,WD5,WD6,WD7
WD1:    zs "HETFO"
WD2:    zs "KEDD"
WD3:    zs "SZERDA"
WD4:    zs "CSUTORTOK"
WD5:    zs "PENTEK"
WD6:    zs "SZOMBAT"
WD7:    zs "VASARNAP"

; HDR_PUT: buffer -> D-file at DE (32 cells)
HDR_PUT:
        ld hl,HDRB
        ld bc,32
        ldir
        ret

; ---------- screen header: rows 0..2 (D-file, always live) ----------
; row 0: DD.MM WEEKDAY HH:MM NAME
; row 1: HOM<temperature> NEM:<F/N> GOND:<BE/KI> TOK:<session characters>
; row 2: inverse separator
HDR_DRAW:
        call HB_BEGIN
        ld a,(ST_DAY)
        call HB_2
        ld a,27                 ; '.'
        call HB_CH
        ld a,(ST_MON)
        call HB_2
        xor a
        call HB_CH
        ld a,(ST_WD)
        call WD_NAME
        call HB_S
        xor a
        call HB_CH
        ld hl,(CLK_MIN)
        call HM_SPLIT
        push de
        call HB_2
        ld a,14                 ; ':'
        call HB_CH
        pop de
        ld a,e
        call HB_2
        xor a
        call HB_CH
        ld hl,ST_NAME
        ld b,8
HD_N:   ld a,(hl)
        call HB_CH
        inc hl
        djnz HD_N
        call HB_PAD
        ld de,DFILE+1
        call HDR_PUT
        ; row 1
        call HB_BEGIN
        ld hl,H_R1
        call HB_S
        ld a,(TSH)
        add a,28
        call HB_CH
        ld hl,H_R2
        call HB_S
        ld a,(ST_GEN)
        cp 1
        ld a,43                 ; 'F' (male)
        jr z,HD_G
        ld a,51                 ; 'N' (female)
HD_G:   call HB_CH
        ld hl,H_R3
        call HB_S
        ld hl,H_BE
        ld a,(GREEDY)
        or a
        jr nz,HD_B
        ld hl,H_KI
HD_B:   call HB_S
        ld hl,H_R4
        call HB_S
        ld hl,(SESS_TOK)
        call DECW
        call HB_PAD
        ld de,DFILE+34
        call HDR_PUT
        ; row 2: inverse line with the FAST state
        call HB_BEGIN
        ld hl,H_GY
        call HB_S
        ld hl,H_BE
        ld a,(FASTF)
        or a
        jr nz,HD_F
        ld hl,H_KI
HD_F:   call HB_S
        ld hl,H_SF
        call HB_S
        call HB_PAD
        ld hl,HDRB
        ld b,32
HD_IV:  ld a,(hl)
        add a,64                ; inverse video
        ld (hl),a
        inc hl
        djnz HD_IV
        ld de,DFILE+67
        call HDR_PUT
        ret

; ---------- chat headers in the log (inverse video) ----------
; ROWOF: A = log row -> HL = LOG + row*32
ROWOF:  ld l,a
        ld h,0
        ld b,5
RO1:    add hl,hl
        djnz RO1
        ld de,LOG
        add hl,de
        ret

; CH_PUT: buffer -> log row HDR_ROW, inverted
CH_PUT: ld a,(HDR_ROW)
        call ROWOF
        ex de,hl
        ld hl,HDRB
        ld b,32
CP1:    ld a,(hl)
        add a,64
        ld (de),a
        inc hl
        inc de
        djnz CP1
        ret

; CH_OPEN: before each prompt: writes the header row with the time and
; BE/KI/V placeholders, then starts a new log row for the input
CH_OPEN:
        ld a,1
        ld (HDR_ON),a
        ld hl,0
        ld (GFR),hl
        xor a
        ld (NOUT),a
        ld a,(LOGHEAD)
        ld (HDR_ROW),a
        ld hl,(CLK_MIN)
        call HM_SPLIT
        ld (HDR_H),a
        ld a,e
        ld (HDR_M),a
        call HB_BEGIN
        ld a,(HDR_H)
        call HB_2
        ld a,14
        call HB_CH
        ld a,(HDR_M)
        call HB_2
        ld hl,H_OPEN
        call HB_S
        call HB_PAD
        call CH_PUT
        jp NEWLINE

; CH_CLOSE: after each turn: rewrites the header row with the real numbers
; BE = characters typed, KI = characters generated, V = reply time (estimate)
CH_CLOSE:
        ld a,(HDR_ON)
        or a
        ret z
        call HB_BEGIN
        ld a,(HDR_H)
        call HB_2
        ld a,14
        call HB_CH
        ld a,(HDR_M)
        call HB_2
        ld hl,H_BEI
        call HB_S
        ld a,(INBUF)
        ld h,0
        ld l,a
        call DECW
        ld hl,H_KIO
        call HB_S
        ld a,(NOUT)
        ld h,0
        ld l,a
        call DECW
        ld hl,H_VV
        call HB_S
        ld a,(NOUT)
        or a
        jr z,CC_DASH
        ld hl,(GFR)
        ld de,50
        call DIVMOD             ; BC = seconds, HL = frames left
        push hl
        ld h,b
        ld l,c
        call DECW
        ld a,27                 ; '.'
        call HB_CH
        pop hl
        ld de,5
        call DIVMOD             ; BC = tenths of a second
        ld a,c
        add a,28
        call HB_CH
        ld a,56                 ; 'S'
        call HB_CH
        jr CC_PAD
CC_DASH: ld a,22                ; '-'
        call HB_CH
CC_PAD: call HB_PAD
        ; session total
        ld a,(INBUF)
        ld l,a
        ld h,0
        ld a,(NOUT)
        ld e,a
        ld d,0
        add hl,de
        ld de,(SESS_TOK)
        add hl,de
        ld (SESS_TOK),hl
        call CH_PUT
        ld a,(VOFF)
        or a
        ret nz
        jp REDRAW

; ---------- strings ----------
H_QM:   zs "?"
H_GY:   zs " GYORS:"
H_SF:   zs "  SHIFT-F"
H_R1:   zs "HOM"
H_R2:   zs " NEM:"
H_R3:   zs " GOND:"
H_BE:   zs "BE"
H_KI:   zs "KI"
H_R4:   zs " TOK:"
H_OPEN: zs "  BE:-  KI:-  V:-"
H_BEI:  zs "  BE:"
H_KIO:  zs "  KI:"
H_VV:   zs "  V:"
