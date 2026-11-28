; app5.asm - chat loop: line input, keys, commands, keywords, main
RESTORED equ $6197
MT_P    equ $6194
MT_I    equ $6196

; ---- DIAGNOSTIC (v1.1.5-diag): canary $A5 in $7E40-$7EC3 (below the stack
; that is in use). CK_CHECK runs at each READ_LINE; on damage it prints "CK"
; plus the READ_LINE number (mod 10), then refills the canary.
CK_N    equ $61D8
CK_FILL: ld hl,$7E40
        ld b,132
CKF_L:  ld (hl),$A5
        inc hl
        djnz CKF_L
        ret
CK_CHECK:
        ld hl,CK_N
        inc (hl)
        ld hl,$7E40
        ld b,132
CKC_L:  ld a,(hl)
        cp $A5
        jr nz,CKC_BAD
        inc hl
        djnz CKC_L
        ret
CKC_BAD:
        ld a,40                 ; C
        call PUTC
        ld a,48                 ; K
        call PUTC
        ld a,(CK_N)
        ld b,a
CKM:    cp 10
        jr c,CKD
        sub 10
        jr CKM
CKD:    add a,28
        call PUTC
        call CK_FILL
        ret

; READ_LINE: fills INBUF (count + ZX codes), echoes via PUTC, ends on ENTER
READ_LINE:
        call CK_CHECK
        xor a
        ld (INBUF),a
RL:     call GETKEY
        cp K_ENTER
        jp z,RL_END
        cp K_DEL
        jr nz,RL_1
        call RL_DEL
        jp RL
RL_1:   cp K_UP
        jr nz,RL_2
        ld a,(VOFF)
        add a,4
        cp LOGN-21
        jr c,RL_UP
        ld a,LOGN-21
RL_UP:  ld (VOFF),a
        call REDRAW
        jp RL
RL_2:   cp K_DOWN
        jr nz,RL_3
        ld a,(VOFF)
        sub 4
        jr nc,RL_DN
        xor a
RL_DN:  ld (VOFF),a
        call REDRAW
        jp RL
RL_3:   cp K_T1
        jr c,RL_4
        cp K_T1+4
        jr nc,RL_4
        sub K_T1-1              ; 1..4
        ld (TSH),a
        ld (ST_TSH),a
        call STATUS
        jp RL
RL_4:   cp K_REAS
        jr nz,RL_F
        ld a,(GREEDY)
        xor 1
        ld (GREEDY),a
        ld (ST_GRD),a
        call STATUS
        jp RL
RL_F:   cp K_FAST
        jr nz,RL_5
        ld a,(FASTF)            ; SHIFT-F: fast mode on/off (header row 2 shows it)
        xor 1
        ld (FASTF),a
        jp RL
RL_5:   cp 64                   ; only plain character codes
        jp nc,RL
        ld b,a
        ld a,(INBUF)
        cp 28                   ; line full
        jp nc,RL
        inc a
        ld (INBUF),a
        ld hl,INBUF
        ld e,a
        ld d,0
        add hl,de
        ld (hl),b
        ld a,b
        call PUTC
        jp RL
RL_END: ld a,118
        call PUTC
        ret

; RL_DEL: remove last character
RL_DEL: ld a,(INBUF)
        or a
        ret z
        dec a
        ld (INBUF),a
        ld a,(COL)
        dec a
        ld (COL),a
        call ROWADDR
        ld a,(COL)
        ld e,a
        ld d,0
        add hl,de
        ld (hl),0
        jp REDRAW

; STATUS: settings line on screen row 1
STATUS: ld a,1
        call DF_ROW
        ld hl,S_ST1
        call PUTD
        ld a,(TSH)
        add a,28                ; n -> ZX digit code 28+n
        ld (de),a
        inc de
        ld hl,S_ST2
        call PUTD
        ld a,(GREEDY)
        or a
        ld hl,S_OFF
        jr z,ST_1
        ld hl,S_ON
ST_1:   call PUTD
        ret
S_ST1:  zs "HOMERSEKLET "
S_ST2:  zs "  GONDOLKODAS "
S_ON:   zs "BE "
S_OFF:  zs "KI "

; RESTORE SETTINGS from the state (after INIT)
APPLY:  ld a,(ST_TSH)
        or a
        jr nz,AP_1
        ld a,1
AP_1:   ld (TSH),a
        ld a,(ST_GRD)
        ld (GREEDY),a
        ret

; MATCH: HL = $FF-terminated ZX pattern; A = 1 if it occurs in INBUF
MATCH:  ld (MT_P),hl
        xor a
        ld (MT_I),a
MT_IL:  ld a,(MT_I)
        ld c,a
        ld a,(INBUF)
        ld b,a
        ld a,c
        cp b
        jr nc,MT_NO
        ld c,0                  ; j
MT_J:   ld hl,(MT_P)
        ld e,c
        ld d,0
        add hl,de
        ld a,(hl)
        cp STR_END
        jr z,MT_YES
        ld b,a                  ; pattern char
        ld a,(MT_I)
        add a,c
        ld d,a                  ; d = i + j
        ld a,(INBUF)
        cp d
        jr c,MT_NX
        jr z,MT_NX
        ld hl,INBUF+1
        ld e,d
        ld d,0
        add hl,de
        ld a,(hl)
        cp b
        jr nz,MT_NX
        inc c
        jr MT_J
MT_NX:  ld a,(MT_I)
        inc a
        ld (MT_I),a
        jr MT_IL
MT_YES: ld a,1
        ret
MT_NO:  xor a
        ret

; keyword table: dw pattern, db kind (0 = memory event, 1 = topic), db argument
KWTAB:  dw KW_HEAD
        db 0,1
        dw KW_PAIN
        db 0,1
        dw KW_HAPPY
        db 0,2
        dw KW_LOVE
        db 0,3
        dw KW_TIRED
        db 0,4
        dw KW_RAIN
        db 1,1
        dw KW_SUN
        db 1,1
        dw KW_DOG
        db 1,2
        dw KW_CAT
        db 1,2
        dw KW_JOKE
        db 1,3
        dw KW_NUMBER
        db 1,4
        dw 0
KW_HEAD: zs "HEAD"
KW_PAIN: zs "PAIN"
KW_HAPPY: zs "HAPPY"
KW_LOVE: zs "LOVE"
KW_TIRED: zs "TIRED"
KW_RAIN: zs "RAIN"
KW_SUN:  zs "SUN"
KW_DOG:  zs "DOG"
KW_CAT:  zs "CAT"
KW_JOKE: zs "JOKE"
KW_NUMBER: zs "NUMBER"
; topic names (LOAD names on tape), index = topic id
TOPNAME: dw 0, TN1, TN2, TN3, TN4
TN1: zs "WEATHER"
TN2: zs "ANIMALS"
TN3: zs "JOKES"
TN4: zs "NUMBERS"

; HANDLE: A = 0 run the model, 1 quit, 2 handled (skip model)
HANDLE: ld hl,KW_QUIT
        call MATCH
        or a
        ld a,1
        ret nz
        ld hl,KW_HELP
        call MATCH
        or a
        jr z,HD_NEW
        ld hl,S_MAN
        call PUTS
        ld a,2
        ret
HD_NEW: ld hl,KW_NEW
        call MATCH
        or a
        jr z,HD_KW
        call INIT
        call APPLY
        ld hl,S_NEWC
        call PUTS
        ld a,2
        ret
HD_KW:  ld hl,KWTAB
HK_L:   ld e,(hl)
        inc hl
        ld d,(hl)
        inc hl
        ld a,d
        or e
        jr z,HK_NO
        push hl
        push de
        ex de,hl                ; hl = pattern
        call MATCH
        pop de
        pop hl
        or a
        jr nz,HK_HIT
        inc hl                  ; skip kind
        inc hl                  ; skip arg
        jr HK_L
HK_HIT: ld a,(hl)               ; kind
        inc hl
        ld b,(hl)               ; arg
        inc hl
        or a
        jr nz,HK_TOP
        ld a,b
        call REMEMBER
        ld a,0
        ret
; topic needed: ask Y/N (Y = leave the chat and LOAD the topic block)
HK_TOP: ld a,(TOPIC)
        cp b
        ld a,0
        ret z
        ld a,b
        ld (HK_ID),a
        ld hl,S_TEMA
        call PUTS2
        call HK_NAME
        ld hl,S_YN
        call PUTS2
HK_WAIT: call GETKEY
        cp 62                   ; Y
        jr z,HK_Y
        cp 51                   ; N: keep chatting without the topic
        jr nz,HK_WAIT
        ld a,0
        ret
HK_Y:   ld hl,S_NEED2
        call PUTS2
        call HK_NAME
        ld hl,S_LOADSFX
        call PUTS
        ld a,1                  ; quit to BASIC: LOAD the topic, then RUN
        ret
; HK_NAME: prints the name of topic HK_ID
HK_NAME: ld a,(HK_ID)
        add a,a
        ld e,a
        ld d,0
        ld hl,TOPNAME
        add hl,de
        ld e,(hl)
        inc hl
        ld d,(hl)
        ex de,hl
        jp PUTS2
HK_ID:  db 0
HK_NO:  xor a
        ret
KW_QUIT: zs "QUIT"
KW_HELP: zs "HELP"
KW_NEW:  zs "NEW"
S_NEWC:  zs "UJ BESZELGETES."
S_NEED:  zs "TEMA: KAZETTA KELL. LOAD {Q}"
S_LOADSFX: zs "{Q} THEN RUN"
S_TEMA:  zs "TEMA: "
S_YN:    zs " BETOLTES? Y/N"
S_NEED2: zs "LOAD {Q}"

; REMEMBER: A = event type; stores it with today's key and weekday, saves
REMEMBER:
        ld (ST_EVT),a
        call TODAYKEY
        ld (ST_EKEY),hl
        ld a,(ST_WD)
        ld (ST_EWD),a
        call ST_SAVE
        ld hl,S_REM
        call PUTS
        ret
S_REM:  zs "EMLEKEZEM."

; GREETING after setup or restore
GREET:  ld hl,S_HI
        call PUTS2
        ld hl,ST_NAME
        ld b,8
GR_N:   ld a,(hl)
        cp 0
        jr z,GR_S
        inc hl
        call PUTC
        djnz GR_N
GR_S:   ld hl,S_HI2
        call PUTS
        ret
S_HI:   zs "SZIA "
S_THINK: zs "GONDOLKODOM (KEP SOTET)"
S_HI2:  zs ". HELP, QUIT"

; QUIT message (state already saved in ST_SAVE)
QUITMSG: ld hl,S_Q1
        call PUTS
        ret
S_Q1:   zn "MENTVE. TEKERD VISSZA AZ ALAP"
        db STR_NL
        zn "KAZETTAT, ES BASIC-BEN:"
        db STR_NL
        zs "SAVE {Q}RTCHAT{Q}"

; APP: main flow
; LOADER (LDR_FLAG = 1 only in the RTLOAD image): asks the user data, saves it to
; the protected area $7F00 and stops, so the user can NEW + LOAD the engine.
LDR_FLAG equ $61DA
LOADER: call ASK_MANUAL
        call SETUP
        call ST_SAVE
        ld hl,S_L1
        call PUTS
        ld hl,S_L2
        call PUTS
        ld hl,S_L3
        call PUTS
        ld hl,S_L4
        call PUTS
        ld hl,S_L5
        call PUTS
        ld hl,S_L6
        call PUTS
        ret
S_L1:  zs "KESZ: ADATOK MENTVE"
S_L2:  zs "1. POKE 16388,0 ENTER"
S_L3:  zs "   POKE 16389,127 ENTER"
S_L4:  zs "2. NEW ENTER"
S_L5:  zs "3. LOAD {Q}RTCHAT{Q} ENTER"
S_L6:  zs "4. RUN ENTER"

APP:    ld hl,MODEL             ; model check: 'RTLM' must be at MODEL
        ld a,(hl)
        cp 'R'
        jp nz,NOMODEL
        inc hl
        ld a,(hl)
        cp 'T'
        jp nz,NOMODEL
        call ST_LOAD           ; read the saved state before the screen is cleared
        ld (RESTORED),a
        xor a
        ld (HDR_ON),a
        ld (FASTF),a            ; SLOW (display on) unless SHIFT-F
        ld hl,0
        ld (SESS_TOK),hl
        call TITLE
        ld a,(LDR_FLAG)
        or a
        jp nz,LOADER
        ld a,(TOPIC_ID)
        ld (TOPIC),a
        ld a,(RESTORED)
        or a
        jr z,AP_NEW
        call SETUP_DATE         ; new date and hour every session
        call ST_SAVE
        call INIT
        call APPLY
        call GREET
        call EVENT_CHECK
        jr AP_GO
AP_NEW: call ASK_MANUAL
        call SETUP
        call INIT
        call APPLY
        call GREET
AP_GO:  call CH_OPEN            ; inverse header row with the time
        ld hl,S_PROMPT
        call PUTS2
        call READ_LINE
        call HANDLE
        cp 1
        jr z,AP_QUIT
        cp 2
        jr z,AP_GO2
        ld hl,S_THINK           ; FAST mode blanks the picture while the reply is computed
        call PUTS
        call GEN
AP_GO2: call CH_CLOSE           ; header row gets BE / KI / V
        jr AP_GO
AP_QUIT: call CH_CLOSE
        call ST_SAVE
        call QUITMSG
        ret
S_PROMPT: zs "> "

NOMODEL: call CLS
        ld hl,S_NOMOD
        call PUTS
        ret
S_NOMOD: zs "HIBA: NINCS MODELL A MEMORIABAN"
