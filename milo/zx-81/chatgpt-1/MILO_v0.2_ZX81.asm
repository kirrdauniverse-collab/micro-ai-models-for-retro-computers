; MILO_v0.2_ZX81.asm - MILO v0.2 micro language model for ZX81 16K.
;
; Runs from BASIC line 1 (1 REM <code>) at 0x4082 = 16514; the cassette
; (tools/t81ai16_build.py) also holds line 2 "RAND USR VAL "16514"" plus
; the knowledge banks, the MEM slot, an inert RT-TURBO reservation and
; the D-file - everything below 0x8000, so it runs on a stock ZX81 with
; the 16K RAM pack.
;
; Screen: own renderer straight into the D-file (rows 0-1 status,
; rows 2-21 chat window, rows 22-23 input line). Scrollback one full
; page per SHIFT+7 (up) / SHIFT+6 (down). Keyboard: own 5x8 matrix scan
; (port FE, rows A8..A15, pressed = bit low), SHIFT = row A8 bit 0.
;
; Memory: the MEM slot at 0x55D0 lives inside the cassette image; the
; engine writes profile/journal/settings back into it on exit, so a
; real-hardware SAVE "" stores the learned state as part of the program.
;
; Texts: embedded strings are ZX81-code bytes, 0xFF-terminated (0x00 is
; the space character, so it can NOT terminate); 0x0A = hard line break;
; 0x0D followed by a token letter = runtime substitution. The build tool
; (tools/t81ai16_build.py) expands the "..." literals before assembling.
;
; Assembler: pip "z80" (kosarev). Only instructions from that
; assembler's verified subset are used here.

; ---------------------------------------------------------- addresses
MEMADD     equ 0x5918      ; MEM slot (512 B, inside the image)
BASEADD    equ 0x5A18      ; BASE bank
PACKWADD   equ 0x65A8      ; WEATHER pack
PACKRADD   equ 0x6BD0      ; RETRO pack
TURBOADD   equ 0x7290      ; RT-TURBO reservation (inert, magic RTT1)
OUTBUF     equ 0x72F0      ; 64 B scratch (status rows, composing)
XL         equ OUTBUF+62   ; scratch pointer save L
XH         equ OUTBUF+63
LINEIN     equ 0x73F0      ; 46 B editor buffer (ZX81 codes)
VLEN       equ 0x7420      ; editor length
VKPREV     equ 0x742B      ; key edge latch: 1 = key still held
PNEXT      equ 0x742C      ; number parser position (u16)
PNCNT      equ 0x742E      ; number parser remaining chars
KBRAW      equ 0x7422      ; 8 B raw keyboard rows
VKSHIFT    equ 0x742A      ; shift held flag
DOCBUF     equ 0x7430      ; 48 B normalized doc, zero-padded
MISC       equ 0x7460      ; 24 B engine vars
SCR0       equ 0x7478      ; scratch bytes
SCR1       equ 0x7479
SCR2       equ 0x747A
SCR3       equ 0x747B
SCR6       equ 0x747C
PTR0       equ 0x747E      ; 16-bit scratch ptr (0x747E..0x747F)
HIST       equ 0x7480      ; ring of 35 slots x 33 B (len + 32 chars)
WORKEND    equ 0x7903      ; first byte after HIST

VSEED      equ MISC+0      ; u16 rng seed (seeded from FRAMES)
VSEEDH     equ MISC+1
VTEMP      equ MISC+2
VREAS      equ MISC+3
VFLAGS     equ MISC+4      ; bit1 name known, bit2 date seen
VDAY       equ MISC+5
VMON       equ MISC+6
VYY        equ MISC+7      ; years since 2000
VHH        equ MISC+8
VMM        equ MISC+9
VWDAY      equ MISC+10     ; 0=Sunday
VHHEAD     equ MISC+11     ; ring head (write slot)
VVIEW      equ MISC+12     ; lines scrolled back (0 = live)
VWRCNT     equ MISC+13     ; chars in open ring slot
VPACK      equ MISC+15     ; 0 none, 1 weather, 2 retro
VBRM       equ MISC+16     ; boot current D-file row
VLMAX      equ MISC+17     ; boot editor limit
VREMLO     equ VBRM        ; reminder target FRAMES low byte (post-boot)
VREMHI     equ VLMAX       ; reminder target FRAMES high byte (post-boot)
MSCORE     equ MISC+18     ; last match score
MRHL       equ MISC+19     ; matched record pointer
MRHH       equ MISC+20
VROW       equ MISC+21     ; render loop row
SCR4       equ MISC+22     ; render window slot index
SCR5       equ MISC+23

MMAGIC     equ 0
MTEMP      equ 4
MREAS      equ 5
MDAY       equ 6
MMON       equ 7
MYY        equ 8
MHH        equ 9
MMM        equ 10
MNAME      equ 12          ; 16 B lowercase ASCII, zero-terminated
MTOWN      equ 28          ; 16 B
MGENDER    equ 44
MBDAY      equ 45
MFLAG      equ 46          ; persistent user-state flags copy
MADDR      equ 52          ; 12 B address/nickname (name used if empty)
MJCOUNT    equ 58
MJHEAD     equ 59
MJOURNAL   equ 64          ; 12 x 14 B: d, mon, yy, tag[11] zero-terminated
MSIZE      equ 512

KEY_NEWLN  equ 0x80
KEY_BS     equ 0x81
KUP        equ 0x82
KDN        equ 0x83
KTEMP      equ 0x84        ; shift+1..4 -> temperature 1..4 (0x84..0x87)
KREAS      equ 0x88        ; shift+9 -> reasoning on/off
HELPC1     equ 0x7100      ; help page 1 (parked in retro slot tail)
HELPC2     equ 0x7180      ; help page 2
HELPC3     equ 0x7200      ; help page 3
KEY_NONE   equ 0xFF

; ---------------------------------------------------------- entry
org 0x4082

entry:
    ld (savesp), sp
    di
    ld sp, 0x7E00
    call var_init
    call mem_load
    ei
    call boot_flow
    call chat_loop
exitchat:
    di
    ld hl, (savesp)
    ld sp, hl
    ei
    ret
savesp: dw 0

; ---------------------------------------------------------- init
var_init:
    ld hl, OUTBUF
    ld bc, WORKEND - OUTBUF
vi_loop:
    ld (hl), 0
    inc hl
    dec bc
    ld a, b
    or c
    jr nz, vi_loop
    ld a, (0x4034)
    ld (VSEED), a
    ld a, (0x4035)
    ld (VSEEDH), a
    ld a, 26
    ld (VYY), a
    ret

mem_load:
    ld a, (MEMADD + MMAGIC)
    cp 0x4D
    jr nz, ml_none
    ld a, (MEMADD + MMAGIC + 1)
    cp 0x45
    jr nz, ml_none
    ld a, (MEMADD + MTEMP)
    ld (VTEMP), a
    ld a, (MEMADD + MREAS)
    ld (VREAS), a
    ld a, (MEMADD + MFLAG)
    ld (VFLAGS), a
    ld a, (MEMADD + MNAME)
    or a
    ret z
    ld a, (VFLAGS)
    or 0x02
    ld (VFLAGS), a
    ret
ml_none:
    ld a, 2
    ld (VTEMP), a
    ld (VREAS), a
    ret

mem_save:
    ld hl, MEMADD + MMAGIC
    ld (hl), 0x4D
    inc hl
    ld (hl), 0x45
    inc hl
    ld (hl), 0x4D
    inc hl
    ld (hl), 0x31
    ld a, (VTEMP)
    ld (MEMADD + MTEMP), a
    ld a, (VREAS)
    ld (MEMADD + MREAS), a
    ld a, (VDAY)
    ld (MEMADD + MDAY), a
    ld a, (VMON)
    ld (MEMADD + MMON), a
    ld a, (VYY)
    ld (MEMADD + MYY), a
    ld a, (VHH)
    ld (MEMADD + MHH), a
    ld a, (VMM)
    ld (MEMADD + MMM), a
    ld a, (VFLAGS)
    ld (MEMADD + MFLAG), a
    ret

; ---------------------------------------------------------- ring writer
; ring slot: [len u8][32 chars ZX81 codes]; len = current char count
wr_ch:
    cp 0x0A
    jr z, wr_nl
    push af
    push bc
    push de
    push hl
    ld c, a
    ld a, (VWRCNT)
    cp 32
    jr nz, wr_go
    call wr_adv
    xor a
wr_go:
    ld b, a                  ; b = payload index (old count)
    inc a
    ld (VWRCNT), a
    ld a, (VHHEAD)
    ld l, a
    ld h, 0
    ld e, l
    ld d, h
    add hl, hl
    add hl, hl
    add hl, hl
    add hl, hl
    add hl, hl
    add hl, de
    ld de, HIST
    add hl, de
    ld a, b
    inc a
    ld (hl), a               ; slot[0] = char count
    inc hl
    ld a, b
    ld e, a
    ld d, 0
    add hl, de
    ld a, c
    ld (hl), a
    pop hl
    pop de
    pop bc
    pop af
    ret

wr_nl:
    ld a, (VWRCNT)
    or a
    ret z
wr_adv:
    ld a, (VHHEAD)
    inc a
    cp 35
    jr c, wa_1
    xor a
wa_1:
    ld (VHHEAD), a
    xor a
    ld (VWRCNT), a
    xor a
    ld (VVIEW), a
    ret

wr_lineend:
    ld a, 0x0A
    jp wr_ch

; B bytes from HL, tokens included; line NOT closed (caller does)
print_b:
    ld a, b
    or a
    ret z
pb_l:
    ld a, (hl)
    inc hl
    push bc
    push hl
    cp 0x0D
    jr z, pb_tok
    call wr_ch
    pop hl
    pop bc
    djnz pb_l
    ret
pb_tok:
    ld a, (hl)
    inc hl
    call emit_tok
    pop hl
    pop bc
    djnz pb_l
    ret

; 0xFF-terminated string at HL
print_enc:
    ld a, (hl)
    cp 0xFF
    ret z
    inc hl
    push hl
    cp 0x0D
    jr z, pe_tok
    call wr_ch
    pop hl
    jr print_enc
pe_tok:
    ld a, (hl)
    inc hl
    call emit_tok
    pop hl
    jr print_enc

say:
    call print_enc
    jr wr_lineend

; ASCII zero-terminated string at HL printed as codes + line end
say_conv:
    ld a, (hl)
    or a
    jr z, sc_done
    push hl
    call cnv_code
    call wr_ch
    pop hl
    inc hl
    jr say_conv
sc_done:
    jp wr_lineend

; A = ASCII char -> A = ZX81 code
cnv_code:
    push bc
    ld c, a
    sub 97
    cp 26
    jr nc, cc_d
    add a, 0x26
    pop bc
    ret
cc_d:
    ld a, c
    sub 48
    cp 10
    jr nc, cc_x
    add a, 0x1C
    pop bc
    ret
cc_x:
    ld a, c
    pop bc
    ret

; A = ZX81 code byte -> A = ASCII
cvn_as:
    push bc
    ld c, a
    sub 0x26
    cp 26
    jr nc, ca_d
    add a, 97
    pop bc
    ret
ca_d:
    ld a, c
    sub 0x1C
    cp 10
    jr nc, ca_x
    add a, 48
    pop bc
    ret
ca_x:
    ld a, c
    pop bc
    ret

; A = value -> two digit codes at (HL), HL += 2
num2:
    push de
    push bc
    ld b, 0
n2_l:
    cp 10
    jr c, n2_d
    sub 10
    inc b
    jr n2_l
n2_d:
    ld e, a
    ld a, b
    add a, 0x1C
    ld (hl), a
    inc hl
    ld a, e
    add a, 0x1C
    ld (hl), a
    inc hl
    pop bc
    pop de
    ret

; --------------------------------------------- token substitution
emit_tok:
    cp 0x33                  ; name
    jp z, et_name
    cp 0x31                  ; town
    jp z, et_town
    cp 0x2C                  ; gender
    jp z, et_gend
    cp 0x29                  ; date
    jp z, et_date
    cp 0x3C                  ; weekday
    jp z, et_wday
    cp 0x39                  ; time
    jp z, et_time
    cp 0x35                  ; part of day
    jp z, et_daypart
    cp 0x27                  ; birthday
    jp z, et_bday
    ret
et_name:
    ld hl, MEMADD + MADDR
    ld a, (hl)
    or a
    jr nz, et_str
    ld hl, MEMADD + MNAME
    jr et_str
et_town:
    ld hl, MEMADD + MTOWN
et_str:
    ld a, (hl)
    or a
    ret z
    push hl
    call cnv_code
    call wr_ch
    pop hl
    inc hl
    jr et_str
et_gend:
    ld a, (MEMADD + MGENDER)
    cp 1
    jr nz, eg1
    ld hl, T_BOY
    jr et_s
eg1:
    cp 2
    jr nz, eg2
    ld hl, T_GIRL
    jr et_s
eg2:
    ld hl, T_PERSON
et_s:
    jp print_enc
et_date:
    ld hl, OUTBUF
    push hl
    ld a, (VDAY)
    call num2
    ld (hl), 0x1B
    inc hl
    ld a, (VMON)
    call num2
    ld (hl), 0x1B
    inc hl
    ld (hl), 0x1E
    inc hl
    ld (hl), 0x1C
    inc hl
    ld a, (VYY)
    call num2
    pop hl
    jp print_enc
et_time:
    ld hl, OUTBUF
    push hl
    ld a, (VHH)
    call num2
    ld (hl), 0x0E
    inc hl
    ld a, (VMM)
    call num2
    pop hl
    jp print_enc
et_wday:
    ld a, (VWDAY)
    add a, a
    ld e, a
    ld d, 0
    ld hl, DWTBL
    add hl, de
    ld e, (hl)
    inc hl
    ld d, (hl)
    ex de, hl
    jp print_enc
et_daypart:
    ld a, (VHH)
    cp 5
    jr c, dp_n
    cp 12
    jr c, dp_m
    cp 18
    jr c, dp_a
    cp 22
    jr c, dp_e
    ld hl, T_NIGHT
    jr dp_go
dp_n:
    ld hl, T_NIGHT
    jr dp_go
dp_m:
    ld hl, T_MORN
    jr dp_go
dp_a:
    ld hl, T_AFT
    jr dp_go
dp_e:
    ld hl, T_EVE
dp_go:
    jp print_enc
et_bday:
    ld a, (MEMADD + MBDAY)
    or a
    ret z
    ld hl, OUTBUF
    push hl
    ld a, (MEMADD + MBDAY)
    call num2
    ld (hl), 0x1B
    inc hl
    ld a, (MEMADD + MBDAY + 1)
    call num2
    pop hl
    jp print_enc

; A = n * 14 (n < 13)
mul14:
    push bc
    ld l, a
    ld h, 0
    add hl, hl
    ld c, l
    ld b, h
    add hl, hl
    add hl, hl
    add hl, hl
    or a
    sbc hl, bc
    pop bc
    ret

; ---------------------------------------------------------- renderer
; A = row -> HL = dfile + 1 + 33*row
rowbase:
    push bc
    push de
    ld c, a
    ld b, 0
    ld e, c
    ld d, b
    ex de, hl
    ld e, l
    ld d, h
    add hl, hl
    add hl, hl
    add hl, hl
    add hl, hl
    add hl, hl
    add hl, de
    ex de, hl
    ld hl, (0x400C)
    inc hl
    add hl, de
    pop de
    pop bc
    ret

; HL = rowbase, DE = data, B = count, pad to 32 with 0x00
blit:
    push bc
    ld c, 32
bl_l:
    ld a, b
    or a
    jr z, bl_p
    ld a, (de)
    inc de
    dec b
    jr bl_w
bl_p:
    xor a
bl_w:
    ld (hl), a
    inc hl
    dec c
    jr nz, bl_l
    pop bc
    ret

df_clearrow:
    push hl
    push bc
    call rowbase
    ld b, 32
    xor a
dcr_l:
    ld (hl), a
    inc hl
    djnz dcr_l
    pop bc
    pop hl
    ret

df_border:
    push hl
    push bc
    call rowbase
    ld b, 32
    ld c, 0x80
dbo_l:
    ld (hl), c
    inc hl
    djnz dbo_l
    pop bc
    pop hl
    ret

; A = row, B = col, E = code
df_char:
    push hl
    push bc
    push de
    push af
    call rowbase
    pop af
    pop de
    pop bc
    push bc
    add hl, bc
    ld (hl), e
    pop bc
    pop hl
    ret

; status rows composed in OUTBUF, then blitted
stcomp:
    ld hl, OUTBUF
    ld de, ST0A
    call scopy
    ld a, (VTEMP)
    add a, 0x1C
    ld (hl), a
    inc hl
    ld de, ST0B
    call scopy
    ld a, (VREAS)
    add a, 0x1C
    ld (hl), a
    inc hl
    ld (hl), 0xFF
    ld de, OUTBUF
    xor a
    call df_rowblit
    ld hl, OUTBUF
    ld a, (VPACK)
    or a
    ld de, ST1BA
    jr z, sc1_d
    cp 1
    ld de, ST1WE
    jr z, sc1_d
    ld de, ST1RE
sc1_d:
    call scopy
    ld a, (VVIEW)
    or a
    jr z, sc1_c
    ld de, ST1PG
    call scopy
    ld a, (VVIEW)
    add a, 19
    ld e, 0
sc1_p:
    cp 20
    jr c, sc1_q
    sub 20
    inc e
    jr sc1_p
sc1_q:
    ld a, e
    add a, 0x1C
    ld (hl), a
    inc hl
sc1_c:
    ld de, ST1FG
    call scopy
    call flagch
    ld (hl), a
    inc hl
    ld (hl), 0xFF
    ld de, OUTBUF
    ld a, 1
    call df_rowblit
    ret

; the packed user-state digit on the status row: one printable char that
; encodes the flag bits (bit0 notes on file, bit1 mood happy, bit2 gender
; known) - state lives in ONE character, exactly like the old trick of
; parking variable values over display-file cells.
flagch:
    ld e, 0
    ld a, (MEMADD + MJCOUNT)
    or a
    jr z, fc_1
    ld e, 1
fc_1:
    ld a, (VFLAGS)
    bit 7, a
    jr z, fc_2
    ld a, e
    or 2
    ld e, a
fc_2:
    ld a, (MEMADD + MGENDER)
    or a
    jr z, fc_3
    ld a, e
    or 4
    ld e, a
fc_3:
    ld a, e
    add a, 0x1C
    ret

; 0xFF-terminated string at DE -> row A, padded with spaces (0x00)
df_rowblit:
    push hl
    push bc
    push de
    call rowbase
    pop de
    ld bc, 0
dfrb_l:
    ld a, (de)
    cp 0xFF
    jr z, dfrb_pad
    ld (hl), a
    inc hl
    inc de
    inc b
    ld a, b
    cp 32
    jr c, dfrb_l
    jr dfrb_d
dfrb_pad:
    ld a, b
    cp 32
    jr nc, dfrb_d
    xor a
    ld (hl), a
    inc hl
    inc b
    jr dfrb_pad
dfrb_d:
    pop bc
    pop hl
    ret

scopy:
    ld a, (de)
    cp 0xFF
    ret z
    ld (hl), a
    inc de
    inc hl
    jr scopy

render_win:
    xor a
    ld (VROW), a
rw_loop:
    ld a, (VHHEAD)
    dec a
    ld b, a
    ld a, (VVIEW)
    ld hl, VROW
    add a, (hl)
    ld c, a
    ld a, b
    sub c
    call norm35
    ld e, a
    ld d, 0
    ld h, d
    ld l, e
    add hl, hl
    add hl, hl
    add hl, hl
    add hl, hl
    add hl, hl
    add hl, de
    ld bc, HIST
    add hl, bc
    ld a, (hl)
    ld (SCR1), a
    inc hl
    ld d, h
    ld e, l
    ld a, (VROW)
    add a, 2
    push hl
    call rowbase
    pop de
    ld a, (SCR1)
    ld b, a
    call blit
    ld a, (VROW)
    inc a
    ld (VROW), a
    cp 22
    jr c, rw_loop
    ret

norm35:
    cp 0x80
    ret c
    add a, 35
    jr norm35

render_in:
    ld a, 22
    call rowbase
    push hl
    ld de, RIN
    call scopy
    ld a, (VLEN)
    cp 27
    jr c, ri_c1
    ld a, 27
ri_c1:
    ld c, a
    ld b, a
    ld de, LINEIN
ri_l:
    ld a, b
    or a
    jr z, ri_c2
    ld a, (de)
    ld (hl), a
    inc de
    inc hl
    dec b
    jr ri_l
ri_c2:
    ld a, (0x4034)
    bit 3, a
    jr z, ri_n
    ld (hl), 0x80
ri_n:
    inc hl
    ld a, 27
    sub c
    ld c, a
    or a
    jr z, ri_d
    ld b, a
ri_p:
    xor a
    ld (hl), a
    inc hl
    djnz ri_p
ri_d:
    pop hl
    ret

render:
    call stcomp
    call render_win
    call render_in
    ret

; ---------------------------------------------------------- keyboard
kb_scan:
    push bc
    push de
    push hl
    ld b, 0xFE
    ld c, 0xFE
    ld hl, KBRAW
    ld d, 8
kbs_row:
    in a, (c)
    cpl
    and 0x1F
    ld (hl), a
    inc hl
    sla b
    set 0, b
    dec d
    jr nz, kbs_row
    xor a
    ld (VKSHIFT), a
    ld a, (KBRAW)
    bit 0, a
    jr z, ksf_ish
    ld a, 1
    ld (VKSHIFT), a
ksf_ish:
    ld hl, KBRAW
    ld de, 0
ksf_r:
    ld a, (hl)
    ld c, a
    ld b, 5
ksf_c:
    srl c
    jr nc, ksf_n
    push hl
    ld a, (VKSHIFT)
    or a
    ld hl, KBSHIFT
    jr nz, ksf_p1
    ld hl, KBPLAIN
ksf_p1:
    add hl, de
    ld a, (hl)
    pop hl
    cp 0xFF
    jr nz, ksf_hit
ksf_n:
    inc e
    ld a, e
    cp 40
    jr z, ksf_none
    djnz ksf_c
    inc hl
    jr ksf_r
ksf_none:
    ld a, 0xFF
    jr ksf_out
ksf_hit:
    ; keep hl/de for debug; restore in out path
ksf_out:
    pop hl
    pop de
    pop bc
    ret

; Edge detection: a key fires ONCE when the scan first sees it pressed
; and stays idle until a scan sees NO key at all (full release). A real
; emulator (or a human finger) holds a key for milliseconds - the old
; 60-scan repeat gate expired inside one frame, so the first typed
; character flooded the whole editor buffer and swallowed the rest.
getkey:
    call kb_scan
    cp KEY_NONE
    jr z, gk_none
    ld e, a
    ld a, (VKPREV)
    or a
    jr nz, gk_held
    ld a, 1
    ld (VKPREV), a
    ld a, e
    ret
gk_held:
    ld a, KEY_NONE
    ret
gk_none:
    xor a
    ld (VKPREV), a
    ld a, KEY_NONE
    ret

; wait for key, wait release, return key in A
getkey_sl:
    call getkey
    cp KEY_NONE
    jr z, getkey_sl
    push af
gk_rl:
    call kb_scan
    cp KEY_NONE
    jr nz, gk_rl
    pop af
    ret

; Y/N prompt: returns 1 for y, else 0; echoes key at row 21 col 0
yn_key:
    push hl
    push bc
    push de
    call getkey_sl
    ld e, a
    push de
    ld a, 21
    ld b, 0
    call df_char
    pop de
    ld a, e
    cp 0x3E
    ld e, 0
    jr nz, yn_out
    ld e, 1
yn_out:
    ld a, e
    pop de
    pop bc
    pop hl
    ret

rnd8:
    push hl
    ld a, (VSEED)
    srl a
    ld (VSEED), a
    jr nc, rd8_end
    ld a, (VSEED)
    xor 0xB8
    ld (VSEED), a
rd8_end:
    pop hl
    ret

delayk:
    push af
    push bc
    ld bc, 0x4000
dk_l:
    dec bc
    ld a, b
    or c
    jr nz, dk_l
    pop bc
    pop af
    ret

; ---------------------------------------------------------- editor
type_line:
    ld a, 21
    call df_clearrow
    xor a
    ld (VLEN), a
tl_loop:
    call getkey
    cp KEY_NONE
    jr z, tl_loop
    cp KEY_NEWLN
    jr z, tl_fin
    cp KEY_BS
    jr z, tl_bs
    cp 0x80
    jr nc, tl_loop
tl_add:
    ld (SCR0), a
    ld a, (VLEN)
    cp 27
    jr nc, tl_loop
    ld c, a
    ld hl, LINEIN
    ld b, 0
    add hl, bc
    ld a, (SCR0)
    ld (hl), a
    ld a, (SCR0)
    ld e, a
    ld a, c
    inc a
    ld (VLEN), a
    dec a
    ld b, a
    xor a
    ld (SCR1), a
    ld a, 21
    call df_char
    jr tl_loop
tl_bs:
    ld a, (VLEN)
    or a
    jr z, tl_loop
    dec a
    ld (VLEN), a
    ld b, a
    ld a, 21
    ld e, 0
    call df_char
    jr tl_loop
tl_fin:
    ret

; LINEIN codes -> ASCII into MEM name
name_store:
    ld a, (VLEN)
    or a
    ret z
    ld c, a
    cp 12
    jr c, ns_go
    ld c, 12
ns_go:
    ld hl, LINEIN
    ld de, MEMADD + MNAME
ns_l:
    ld a, c
    or a
    jr z, ns_z
    dec c
    ld a, (hl)
    push hl
    call cvn_as
    pop hl
    inc hl
    ld (de), a
    inc de
    jr ns_l
ns_z:
    xor a
    ld (de), a
    ld a, (VFLAGS)
    or 2
    ld (VFLAGS), a
    ret

; ---------------------------------------------------------- boot flow
bq:
    call df_line
bq_adv:
    ld a, (VBRM)
    inc a
    cp 21
    jr c, bq_st
    ld a, 17
bq_st:
    ld (VBRM), a
    ret

df_line:
    ld (XL), hl
    push bc
    push de
    push af
    ld a, (VBRM)
    call rowbase
    ld b, 32
    xor a
dfl_c:
    ld (hl), a
    inc hl
    djnz dfl_c
    ld a, (VBRM)
    call rowbase
    ex de, hl
    ld hl, (XL)
dfl_w:
    ld a, (hl)
    cp 0x0A
    jr z, dfl_b
    cp 0xFF
    jr z, dfl_d
    ld (de), a
    inc hl
    inc de
    jr dfl_w
dfl_b:
    inc hl
dfl_d:
    ld (XL), hl
    pop af
    pop de
    pop bc
    ld hl, (XL)
    ret

df_walk:
    ld a, (hl)
    cp 0xFF
    ret z
    call df_line
    jr df_walk

boot_dots:
    push af
    push bc
    push de
    push hl
    ld c, 8
    ld hl, 12
bd_l:
    push hl
    push bc
    ld a, 21
    ld b, l
    ld e, 0x1B
    call df_char
    pop bc
    pop hl
    inc hl
    call delayk
    dec c
    jr nz, bd_l
    pop hl
    pop de
    pop bc
    pop af
    ret

df_splash:
    ld a, 2
ds_c:
    push af
    call df_clearrow
    pop af
    inc a
    cp 14
    jr c, ds_c
    ld a, 2
    call df_border
    ld a, 13
    call df_border
    ld hl, ARTBL
    ld b, 3
ds_art:
    push bc
    push hl
    push de
    ld d, h
    ld e, l
    ld a, b
    call rowbase
    ld bc, 31
ds_l:
    ld a, (de)
    ld (hl), a
    inc de
    inc hl
    dec bc
    ld a, b
    or c
    jr nz, ds_l
    xor a
    ld (hl), a
    pop de
    pop hl
    ld de, 31
    add hl, de
    pop bc
    inc b
    ld a, b
    cp 11
    jr c, ds_art
    ; caption
    ld a, 11
    call rowbase
    ld bc, 8
cap_sk:
    add hl, bc
    ld de, CAPTXT
    ld b, 15
    call blit
    ret

; date/time parsing on LINEIN
next_num:
    push bc
    push de
    ld e, 0
    ld d, 0
nn_s:
    ld a, b
    or a
    jr z, nn_end
    ld a, (hl)
    cp 0x1C
    jr c, nn_s2
    cp 0x26
    jr nc, nn_end
    sub 0x1C
    ld c, a
    push bc
    ld a, e
    sla a
    ld b, a
    sla a
    sla a
    add a, b
    add a, c
    ld e, a
    pop bc
    ld d, 1
    inc hl
    dec b
    jr nn_s
nn_s2:
    ld a, d
    or a
    jr z, nn_adv
    jr nn_end
nn_adv:
    inc hl
    dec b
    jr nn_s
nn_end:
    ld a, d
    or a
    jr z, nn_fail
    ld (PNEXT), hl
    ld a, b
    ld (PNCNT), a
    ld a, e
    pop de
    pop bc
    ret
nn_fail:
    ld (PNEXT), hl
    ld a, b
    ld (PNCNT), a
    ld a, 0
    scf
    pop de
    pop bc
    ret

next_num2:
    ld hl, LINEIN
    ld (PNEXT), hl
    ld a, (VLEN)
    ld (PNCNT), a
next_cont:
    ld hl, (PNEXT)
    ld a, (PNCNT)
    ld b, a
    call next_num
    ret

parse_date:
    call next_num2
    jr c, pd_bad
    ld (SCR0), a
    call next_cont
    jr c, pd_bad
    ld (SCR1), a
    call next_cont
    jr c, pd_noyy
    cp 100
    jr nc, pd_noyy
    ld (VYY), a
pd_noyy:
    ld a, (SCR0)
    or a
    jr z, pd_bad
    cp 32
    jr nc, pd_bad
    ld (VDAY), a
    ld a, (SCR1)
    or a
    jr z, pd_bad
    cp 13
    jr nc, pd_bad
    ld (VMON), a
    call calc_wday
    ret
pd_bad:
    ld a, 1
    ld (VDAY), a
    ld (VMON), a
    call calc_wday
    ret

parse_time:
    call next_num2
    jr c, pt_bad
    ld (SCR0), a
    call next_cont
    jr c, pt_bad
    ld (SCR1), a
    ld a, (SCR0)
    cp 24
    jr nc, pt_bad
    ld (VHH), a
    ld a, (SCR1)
    cp 60
    jr nc, pt_bad
    ld (VMM), a
    ret
pt_bad:
    ld a, 18
    ld (VHH), a
    xor a
    ld (VMM), a
    ret

WTAB:
    db 0x00, 0x03, 0x02, 0x05, 0x00, 0x03, 0x05, 0x01, 0x04, 0x06, 0x02, 0x04

calc_wday:
    push bc
    push de
    push hl
    ld a, (VMON)
    cp 3
    ld a, (VYY)
    jr nc, cw_p1
    ld b, 1
    or a
    jr nz, cw_j2
    ld a, 99
cw_j2:
    dec a
    jr cw_gy
cw_p1:
    ld b, 0
cw_gy:
    ld e, a
    srl a
    srl a
    add a, e
    ld c, a
    ld a, (VMON)
    dec a
    ld e, a
    ld d, 0
    ld hl, WTAB
    add hl, de
    ld a, (VDAY)
    add a, (hl)
    add a, c
    add a, b
cw_m:
    cp 7
    jr c, cw_md
    sub 7
    jr cw_m
cw_md:
    ld (VWDAY), a
    pop hl
    pop de
    pop bc
    ret

; ---------------------------------------------------------- NLP core
build_doc:
    ld b, 48
    ld hl, DOCBUF
bd_z:
    ld (hl), 0
    inc hl
    djnz bd_z
    ld a, (VLEN)
    or a
    ret z
    ld hl, LINEIN
    ld de, DOCBUF
    ld b, a
bd_cp:
    ld a, (hl)
    ld (de), a
    inc hl
    inc de
    djnz bd_cp
    ret

; find key (DE = ptr, C = len) in DOCBUF; CF=0 + A=pos on hit
find_sub:
    push hl
    push de
    push bc
    ld hl, DOCBUF
    ld b, 0
fs_l:
    ld a, b
    cp 40
    jr nc, fs_no
    push hl
    push de
    push bc
fs_c:
    ld a, (de)
    cp (hl)
    jr nz, fs_m
    inc de
    inc hl
    dec c
    jr nz, fs_c
    pop bc
    pop de
    pop hl
    jr fs_hit
fs_m:
    pop bc
    pop de
    pop hl
    inc hl
    inc b
    jr fs_l
fs_no:
    pop bc
    pop de
    pop hl
    ld a, 0xFF
    or a
    scf
    ret
fs_hit:
    ld a, b
    pop bc
    pop de
    pop hl
    or a
    ret

; skip key list: HL at nkeys byte -> HL = first byte after keys
rec_sk:
    ld b, (hl)
    inc hl
rs_l:
    ld a, b
    or a
    ret z
    dec b
    ld e, (hl)
    ld d, 0
    inc hl
    add hl, de
    jr rs_l

; score one record: HL = record start -> HL = after record; on strict
; score improvement MRPTR/MSCORE update
ms_rec:
    ld (VROW), hl
    inc hl
    inc hl
    ld a, (hl)
    ld (SCR2), a
    inc hl
    ld b, a
msr_k:
    ld a, b
    or a
    jr z, msr_ke
    dec b
    ld a, (hl)
    ld (SCR3), a
    inc hl
    ld e, l
    ld d, h
    ld c, a
    push hl
    call find_sub
    jr c, msr_no
    push af
    ld a, (SCR2)
    add a, a
    ld c, a
    add a, a
    add a, a
    add a, c
    ld c, a
    ld a, (SCR3)
    add a, c
    ld c, a
    ld a, (MSCORE)
    cp c
    jr nc, msr_lo
    ld a, c
    ld (MSCORE), a
    ld hl, (VROW)
    ld (MRHL), hl
    pop af
    ld (SCR5), a
    ld a, (SCR3)
    ld (SCR6), a
    jr msr_no
msr_lo:
    pop af
msr_no:
    pop hl
    ld a, (SCR3)
    ld e, a
    ld d, 0
    add hl, de
    jr msr_k
msr_ke:
    ld c, (hl)
    inc hl
msr_r:
    ld a, c
    or a
    jr z, msr_d
    dec c
    ld e, (hl)
    ld d, 0
    inc hl
    add hl, de
    jr msr_r
msr_d:
    ret

ms_scan:                  ; HL = bank base; walks its nint records
    push bc
    ld bc, 16
    add hl, bc
    ld c, (hl)
    inc hl
    ld b, (hl)
    inc hl
ms_n:
    ld a, b
    or c
    jr z, ms_d
    push bc
    call ms_rec
    call think_tick
    pop bc
    dec bc
    jr ms_n
ms_d:
    pop bc
    ret

; match DOCBUF against active pack (scanned first) and base bank;
; sets MRPTR / MSCORE (fallback record when score 0)
match:
    xor a
    ld (MSCORE), a
    ld a, (VPACK)
    or a
    jr z, mt_base
    cp 1
    jr nz, mt_r2
    ld hl, PACKWADD
    jr mt_go
mt_r2:
    ld hl, PACKRADD
mt_go:
    push hl
    call ms_scan
    pop hl
    ld hl, BASEADD
    push hl
    call ms_scan
    pop hl
    jr mt_fall
mt_base:
    ld hl, BASEADD
    push hl
    call ms_scan
    pop hl
mt_fall:
    ld a, (MSCORE)
    or a
    ret nz
    ld a, (VPACK)
    or a
    jr z, mf_b
    cp 1
    jr nz, mf_r
    ld hl, PACKWADD
    jr mf_fw
mf_r:
    ld hl, PACKRADD
    jr mf_fw
mf_b:
    ld hl, BASEADD
mf_fw:
    ld bc, 18
    add hl, bc
mf_rec:
    inc hl
    inc hl
    ld a, (hl)
    or a
    jr z, mf_ok
    call rec_sk
    ; skip nrep replies
    ld c, (hl)
    inc hl
mfs_r:
    ld a, c
    or a
    jr z, mf_rec
    dec c
    ld e, (hl)
    ld d, 0
    inc hl
    add hl, de
    jr mfs_r
mf_ok:
    dec hl
    dec hl
    ld (MRHL), hl
    ld a, 1
    ld (MSCORE), a
    ret

; print chosen reply variant of the matched record (no line end)
print_reply:
    ld hl, (MRHL)
    inc hl
    inc hl
    call rec_sk
    ld c, (hl)
    inc hl
    ld b, 0
    ld a, (VTEMP)
    cp 2
    jr c, pr_go
    call rnd8
pr_m:
    sub c
    jr nc, pr_m
    add a, c
    ld b, a
pr_go:
    ld a, b
    or a
    jr z, pr_prt
    ld a, (hl)
    inc hl
    ld e, a
    ld d, 0
    add hl, de
    dec b
    jr pr_go
pr_prt:
    ld a, (hl)
    inc hl
    ld b, a
    call print_b
    ret

; table scan: HL = [len][codes]... 0 = end; Z=1 end, CF=1 no hit,
; found: CF=0, HL = codes ptr, C = len
list_scan:
    ld a, (hl)
    or a
    scf
    ret z
    ld c, a
    inc hl
    push hl
    ld e, l
    ld d, h
    call find_sub
    pop hl
    jr c, ls_adv
    or a
    ret
ls_adv:
    ld b, 0
    add hl, bc
    jr list_scan

dispatch:
    ld hl, (MRHL)
    ld a, (hl)
    add a, a
    ld e, a
    ld d, 0
    ld hl, htab
    add hl, de
    ld a, (hl)
    inc hl
    ld h, (hl)
    ld l, a
    jp (hl)

; plain reply + reasoning extras + line end
reply_x:
    call print_reply
    ld a, (VREAS)
    or a
    jp z, wr_lineend
    ld hl, T_THINK
    call print_enc
    ld hl, (MRHL)
    inc hl
    ld a, (hl)
    or a
    jr nz, rx1
    ld hl, T_BBASE
    jr rx_g
rx1:
    cp 1
    jr nz, rx2
    ld hl, T_BWEA
    jr rx_g
rx2:
    ld hl, T_BRET
rx_g:
    call print_enc
    ld a, (VREAS)
    cp 2
    jp c, wr_lineend
    ld hl, T_CONFP
    call print_enc
    ld a, (MSCORE)
    cp 35
    jr nc, rxh
    cp 16
    jr nc, rxm
    ld hl, T_CLOW
    jr rx_g2
rxh:
    ld hl, T_CHIGH
    jr rx_g2
rxm:
    ld hl, T_CMID
rx_g2:
    call print_enc
rx_r:
    ld a, (VREAS)
    cp 3
    jp c, wr_lineend
    ld a, (MSCORE)
    cp 14
    jp nc, wr_lineend
    ld hl, T_MORE
    jp say

; extract a word after pos A (keylen C) out of DOCBUF -> OUTBUF ASCII;
; CF=1 when nothing found
extract_at:
    push hl
    push de
    push bc
    ld e, a
    ld d, 0
    ld hl, DOCBUF
    add hl, de
    ld b, 0
    add hl, bc
    ld a, (hl)
    or a
    jr nz, ea_go
    inc hl
ea_go:
    ld de, OUTBUF
    ld b, 0
ea_l:
    ld a, (hl)
    or a
    jr z, ea_e
    push hl
    call cvn_as
    pop hl
    ld (de), a
    inc de
    inc hl
    inc b
    ld a, b
    cp 15
    jr nc, ea_ok
    jr ea_l
ea_e:
    xor a
    ld (de), a
    ld a, b
    or a
    jr z, ea_f
ea_ok:
    pop bc
    pop de
    pop hl
    or a
    ret
ea_f:
    pop bc
    pop de
    pop hl
    scf
    ret

cstr16:                   ; HL = src ascii, DE = dst; copies <= 15 + term
    ld b, 0
    ld a, (hl)
    or a
    jr z, cs_t
cs_l:
    ld (de), a
    inc de
    inc hl
    inc b
    ld a, b
    cp 15
    jr nc, cs_t
    ld a, (hl)
    or a
    jr nz, cs_l
cs_t:
    xor a
    ld (de), a
    ret

j_entry:                  ; DE = tag zp81 codes, C = tag len
    push af
    push bc
    push de
    push hl
    push de               ; tag ptr on stack
    push bc               ; tag len on stack (c)
    ld a, (MEMADD + MJHEAD)
    call mul14
    ld bc, MEMADD + 64
    add hl, bc            ; hl = entry dst
    ld a, (VDAY)
    ld (hl), a
    inc hl
    ld a, (VMON)
    ld (hl), a
    inc hl
    ld a, (VYY)
    ld (hl), a
    inc hl
    pop bc                ; c = tag len
    pop de                ; de = tag ptr
je_cp:
    ld a, c
    or a
    jr z, je_end
    ld a, (de)
    inc de
    call cvn_as
    ld (hl), a
    inc hl
    dec c
    jr je_cp
je_end:
    ld (hl), 0
    ld a, (MEMADD + MJHEAD)
    inc a
    cp 12
    jr c, je_h
    xor a
je_h:
    ld (MEMADD + MJHEAD), a
    ld a, (MEMADD + MJCOUNT)
    cp 12
    jr nc, je_c
    inc a
    ld (MEMADD + MJCOUNT), a
je_c:
    call mem_save
    pop hl
    pop de
    pop bc
    pop af
    ret

; ---------------------------------------------------------- handlers
; A = pos of a key hit in DOCBUF, C = its length -> ASCII word in OUTBUF
xw_word:
    ld a, (SCR6)
    ld c, a
    ld a, (SCR5)
    jp extract_at

h0:
    jp reply_x

h1:
    call xw_word
    jr c, h1_n
    ld hl, OUTBUF
    ld de, MEMADD + MNAME
    call cstr16
    ld a, (VFLAGS)
    or 2
    ld (VFLAGS), a
h1_n:
    jp reply_x

h2:
    call xw_word
    jr c, h2_n
    ld hl, OUTBUF
    ld de, MEMADD + MTOWN
    call cstr16
h2_n:
    jp reply_x

h3:
    ld hl, GENDTBL
h3_l:
    ld a, (hl)
    or a
    jr z, h3_f
    ld c, a
    inc hl
    ld a, (hl)
    ld (SCR4), a
    inc hl
    push hl
    push bc
    ld e, l
    ld d, h
    call find_sub
    pop bc
    pop hl
    jr c, h3_nx
    ld a, (SCR4)
    ld (MEMADD + MGENDER), a
    jp reply_x
h3_nx:
    ld b, 0
    add hl, bc
    jr h3_l
h3_f:
    jp reply_x

h4:
    call next_num2
    jr c, h4_bad
    ld (SCR0), a
    call next_cont
    jr c, h4_bad
    ld (SCR1), a
    ld a, (SCR0)
    or a
    jr z, h4_bad
    cp 32
    jr nc, h4_bad
    ld a, (SCR1)
    or a
    jr z, h4_bad
    cp 13
    jr nc, h4_bad
    ld a, (SCR0)
    ld (MEMADD + MBDAY), a
    ld a, (SCR1)
    ld (MEMADD + MBDAY + 1), a
    jp reply_x
h4_bad:
    ld hl, T_BADB
    jp say

h5:
    ld hl, TAGTBL
    call list_scan
    ld de, T_NOTE
    ld c, 4
    jr c, h5_go
    ld e, l
    ld d, h
h5_go:
    ld a, (VFLAGS)
    or 0x40
    ld (VFLAGS), a
    call j_entry
    jp reply_x

h6:
    xor a
    ld (MEMADD + MJCOUNT), a
    ld a, (VFLAGS)
    and 0xBF
    or 0x80
    ld (VFLAGS), a
    ld hl, T_CLEARED
    jp say

h7:
    ld a, (VFLAGS)
    bit 1, a
    jp z, h_unkn
    jp reply_x

h_unkn:
    ld hl, T_UNKN
    jp say

h8:
    ld a, (MEMADD + MTOWN)
    or a
    jr z, h_unkn
    jp reply_x

h9:
    ld a, (MEMADD + MGENDER)
    or a
    jr z, h_unkn
    jp reply_x

h10:
    ld a, (MEMADD + MBDAY)
    or a
    jr z, h10_n
    jp reply_x
h10_n:
    ld hl, T_NOBDAY
    jp say

h11:
    jp reply_x

h12:
    jp reply_x

h13:
    ld a, (MEMADD + MJCOUNT)
    or a
    jr z, h13_no
    ld (SCR3), a
    ld c, a
    ld a, 12
    sub c
    ld c, a
    ld a, (MEMADD + MJHEAD)
    add a, c
h13_m:
    cp 12
    jr c, h13_ok
    sub 12
    jr h13_m
h13_ok:
    ld (SCR2), a
h13_l:
    ld a, (SCR2)
    call h13_e
    ld a, (SCR3)
    dec a
    ld (SCR3), a
    jr z, h13_d
    ld a, (SCR2)
    inc a
    cp 12
    jr c, h13_l2
    xor a
h13_l2:
    ld (SCR2), a
    jr h13_l
h13_d:
    jp wr_lineend
h13_no:
    ld hl, T_NOJ
    jp say

; one journal entry: "on dd.mm.20yy: tag" -> ring; A = entry index
h13_e:
    push hl
    push de
    push bc
    call mul14
    ld bc, MEMADD + 64
    add hl, bc
    ld (PTR0), hl
    ld hl, T_ON3
    call print_enc
    ld de, OUTBUF
    ld hl, (PTR0)
    ld a, (hl)
    ex de, hl
    call num2
    ex de, hl
    ld a, 0x1B
    ld (de), a
    inc de
    inc hl
    ld a, (hl)
    ex de, hl
    call num2
    ex de, hl
    ld a, 0x1B
    ld (de), a
    inc de
    ld a, 0x1E
    ld (de), a
    inc de
    ld a, 0x1C
    ld (de), a
    inc de
    inc hl
    ld a, (hl)
    ex de, hl
    call num2
    ex de, hl
    ld a, 0x19
    ld (de), a
    inc de
    xor a
    ld (de), a
    inc de
    inc hl
h13_t:
    ld a, (hl)
    or a
    jr z, h13_te
    call cnv_code
    ld (de), a
    inc de
    inc hl
    jr h13_t
h13_te:
    ld a, 0xFF
    ld (de), a
    ld hl, OUTBUF
    call print_enc
    pop bc
    pop de
    pop hl
    ret

h14:
    jp c_help
h15:
    ld hl, (MRHL)
    inc hl
    ld a, (hl)
    inc a
    ld c, a
    ld a, (VPACK)
    cp c
    jp z, h15_on
    push bc
    call print_reply
    call wr_lineend
    call getkey_sl
    or a
    pop bc
    jp z, h15_ld
    ld hl, T_NL
    jp say
h15_ld:
    ld a, c
    ld (VPACK), a
    ld hl, T_LOADING
    call print_enc
    ld b, 8
h15_d:
    push bc
    ld a, 0x1B
    call wr_ch
    call delayk
    pop bc
    djnz h15_d
    call wr_lineend
    ld hl, T_PLOADED
    jp say
h15_on:
    call print_reply
    call wr_lineend
    ld hl, T_PACKON
    jp say

h16:
    jp reply_x

h17:
    jp reply_x

h18:
    call mem_save
    ld hl, T_BYE
    call say
    jp exitchat

h19:
    ld hl, T_TOPICS
    jp say

; ---------------------------------------------------------- commands

arg_digit:
    ld hl, DOCBUF
    ld b, 0
ad_l:
    ld a, (VLEN)
    cp b
    jr c, ad_no
    ld a, (hl)
    cp 0x1C
    jr c, ad_n
    cp 0x26
    jr c, ad_d
ad_n:
    inc hl
    inc b
    jr ad_l
ad_d:
    sub 0x1C
    or a
    ret
ad_no:
    ld a, 0
    scf
    ret

cmd_is:
    ld e, l
    ld d, h
    call find_sub
    ret c
    xor a
    ret

cmd_run:
    ld hl, CMD_HELP
    ld c, 4
    call cmd_is
    jp z, c_help
    ld hl, CMD_TOPICS
    ld c, 6
    call cmd_is
    jp z, c_top
    ld hl, CMD_TEMP
    ld c, 4
    call cmd_is
    jp z, c_temp
    ld hl, CMD_REAS
    ld c, 6
    call cmd_is
    jp z, c_reas
    ld hl, CMD_MEM
    ld c, 3
    call cmd_is
    jp z, c_mem
    ld hl, CMD_SAVE
    ld c, 4
    call cmd_is
    jp z, c_save
    ld hl, CMD_QUIT
    ld c, 4
    call cmd_is
    jp z, c_quit
    ld hl, CMD_FOGT
    ld c, 6
    call cmd_is
    jp z, c_fogt
    ld hl, CMD_COFFEE
    ld c, 6
    call cmd_is
    jp z, c_coffee
    ld hl, CMD_TIME
    ld c, 4
    call cmd_is
    jp z, c_time
    ld hl, CMD_REMIND
    ld c, 6
    call cmd_is
    jp z, c_remind
    ld hl, T_BADCMD
    jp say

c_help:
    ld hl, HELPC1
    call print_enc
    ld a, 0x0A
    call wr_ch
    ld hl, HELPC2
    call print_enc
    ld a, 0x0A
    call wr_ch
    ld hl, HELPC3
    call print_enc
    jp wr_lineend

c_top:
    ld hl, T_TOPICS
    jp say

c_temp:
    call arg_digit
    jp c, c_arg
    cp 7
    jp nc, c_arg
    ld c, a
    ld (VTEMP), a
    ld hl, T_TEMPOK
    call print_enc
    ld a, c
    add a, 0x1C
    call wr_ch
    jp wr_lineend
c_reas:
    call arg_digit
    jp c, c_arg
    cp 4
    jp nc, c_arg
    ld c, a
    ld (VREAS), a
    ld hl, T_REASOK
    call print_enc
    ld a, c
    add a, 0x1C
    call wr_ch
    jp wr_lineend

; /time HH MM - set MILO's conversational clock.
c_time:
    call next_num2
    jr c, c_time_bad
    ld (SCR0), a
    call next_cont
    jr c, c_time_bad
    ld (SCR1), a
    ld a, (SCR0)
    cp 24
    jr nc, c_time_bad
    ld (VHH), a
    ld a, (SCR1)
    cp 60
    jr nc, c_time_bad
    ld (VMM), a
    call mem_save
    ld hl, T_TIMEOK
    jp say
c_time_bad:
    ld hl, T_TIMEBAD
    jp say

; /remind N - schedule a short reminder in the live chat.
; N is minutes, 1..5. FRAMES is a 15-bit countdown on the ZX81.
c_remind:
    call arg_digit
    jr c, c_rem_bad
    or a
    jr z, c_rem_bad
    cp 6
    jr nc, c_rem_bad
    ld c, a
    ld hl, 0
    ld b, c
c_rem_mul:
    ld de, 3000
    add hl, de
    djnz c_rem_mul
    ld de, (0x4034)
    ld a, d
    and 0x7F
    ld d, a
    push hl
    or a
    sbc hl, de
    pop hl
    jr c, c_rem_zero
    ex de, hl
    or a
    sbc hl, de
    jr c, c_rem_zero
    jr c_rem_store
c_rem_zero:
    ld hl, 0
c_rem_store:
    ld (VREMLO), hl
    ld a, (VFLAGS)
    or 0x20
    ld (VFLAGS), a
    ld hl, T_REMSET
    call print_enc
    ld a, c
    add a, 0x1C
    call wr_ch
    ld hl, T_MINUTES
    call print_enc
    jp wr_lineend
c_rem_bad:
    ld hl, T_REMBAD
    jp say

c_arg:
    ld hl, T_ARGERR
    jp say

c_mem:
    call mem_show
    ret

c_save:
    call mem_save
    ld hl, T_SAVED
    jp say

c_quit:
    call mem_save
    ld hl, T_BYE
    call say
    jp exitchat

c_fogt:
    call mem_forget
    ld hl, T_FORGOT
    jp say

c_coffee:
    call coffee_brew
    ld hl, T_COFFEE_MSG
    jp say

mem_show:
    ld a, (VFLAGS)
    bit 1, a
    jr z, msw_1
    ld hl, T_MEMN
    call say
msw_1:
    ld a, (MEMADD + MTOWN)
    or a
    jr z, msw_2
    ld hl, T_MEMT
    call say
msw_2:
    ld a, (MEMADD + MGENDER)
    or a
    jr z, msw_3
    ld hl, T_MEMG
    call say
msw_3:
    ld a, (MEMADD + MBDAY)
    or a
    jr z, msw_4
    ld hl, T_MEMB
    call say
msw_4:
    ld a, (MEMADD + MJCOUNT)
    or a
    ret z
    jp h13

mem_forget:
    xor a
    ld (MEMADD + MNAME), a
    ld (MEMADD + MTOWN), a
    ld (MEMADD + MGENDER), a
    ld (MEMADD + MBDAY), a
    ld (MEMADD + MADDR), a
    ld (MEMADD + MJCOUNT), a
    ld (MEMADD + MJHEAD), a
    ld a, (VFLAGS)
    and 0xBD
    ld (VFLAGS), a
    ret

; ---------------------------------------------------------- chat headers
; Q header = timestamp + input token count. A header = timestamp + measured
; inference time in ZX81 frames. The header is written before dispatch, so it
; genuinely separates the answer that follows.
count_tokens:
    ld hl, DOCBUF
    ld a, (VLEN)
    ld b, a
    xor a
    ld c, a
    ld d, 0
    ld e, 0
ct_l:
    ld a, b
    or a
    jr z, ct_done
    ld a, (hl)
    inc hl
    cp 0
    jr z, ct_space
    ld e, 1
    jr ct_next
ct_space:
    ld a, e
    or a
    jr z, ct_next
    inc c
    xor a
    ld e, a
ct_next:
    djnz ct_l
ct_done:
    ld a, e
    or a
    jr z, ct_out
    inc c
ct_out:
    ld a, c
    ld (SCR5), a
    ret

q_header:
    call count_tokens
    ld hl, OUTBUF
    ld de, T_QHEAD
    call scopy
    ld a, (VHH)
    call num2
    ld (hl), 0x0E
    inc hl
    ld a, (VMM)
    call num2
    ld de, T_QTOK
    call scopy
    ld a, (SCR5)
    call num2
    ld (hl), 0xFF
    ld hl, OUTBUF
    call print_enc
    jp wr_lineend

a_header:
    ld a, (0x4034)
    ld c, a
    ld a, (SCR6)
    sub c
    neg
    ld (SCR6), a
    ld hl, OUTBUF
    ld de, T_AHEAD
    call scopy
    ld a, (VHH)
    call num2
    ld (hl), 0x0E
    inc hl
    ld a, (VMM)
    call num2
    ld de, T_ADT
    call scopy
    ld a, (SCR6)
    call num2
    ld de, T_AFR
    call scopy
    ld (hl), 0xFF
    ld hl, OUTBUF
    call print_enc
    jp wr_lineend

; ---------------------------------------------------------- D-file transient scratch
; 8 bytes at row 23, columns 24..31. This is NOT persistent memory.
; It is safe because render_in reconstructs the complete input row after each
; operation. Only printable ZX81 display codes are stored here.
DFSCRATCH_COL equ 24
df_scratch_put:
    ; Write one safe ZX81 display byte into row 23, col 24.
    ; Preserve ALL caller registers. The thinking marker is carried in E,
    ; so DE must not be used as the destination scratch register.
    push af
    push hl
    push bc
    push de
    ld a, 23
    call rowbase
    ld c, DFSCRATCH_COL
    ld b, 0
    add hl, bc
    ld (hl), a
    pop de
    pop bc
    pop hl
    pop af
    ret

; ---------------------------------------------------------- thinking / coffee UI
; Bottom D-file rows are used only while the engine is busy. They contain
; ordinary ZX81 display codes and are immediately restored by render.
think_ui:
    ld a, 22
    call df_clearrow
    ld a, 23
    call df_clearrow
    ld a, 22
    call rowbase
    ld hl, T_THINKBAR
    call df_rowblit
    ld a, 23
    call rowbase
    ld hl, T_THINK0
    call df_rowblit
    ret

think_tick:
    ; ms_scan relies on HL pointing at the next record after ms_rec.
    push hl
    call think_ui
    ld a, (0x4034)
    and 3
    inc a
    ld e, a
    call df_scratch_put
    ld a, 22
    ld b, 27
    call df_char
    pop hl
    ret


coffee_brew:
    call think_ui
    ld a, 23
    call rowbase
    ld hl, T_COFFEE0
    call df_rowblit
    ld a, 3
    ld (SCR0), a
cb_loop:
    call delayk
    ld a, (SCR0)
    cp 3
    jr z, cb_1
    cp 2
    jr z, cb_2
    ld hl, T_COFFEE3
    jr cb_show
cb_1:
    ld hl, T_COFFEE1
    jr cb_show
cb_2:
    ld hl, T_COFFEE2
cb_show:
    ld a, 23
    call rowbase
    call df_rowblit
    ld a, (SCR0)
    dec a
    ld (SCR0), a
    jr nz, cb_loop
    ld a, 23
    call rowbase
    ld hl, T_COFFEE_DONE
    call df_rowblit
    call delayk
    ret

; ---------------------------------------------------------- live reminder
remind_tick:
    ld a, (VFLAGS)
    bit 5, a
    ret z
    ld hl, (0x4034)
    ld a, h
    and 0x7F
    ld h, a
    ld de, (VREMLO)
    or a
    sbc hl, de
    jr c, rt_fire
    jr z, rt_fire
    ret
rt_fire:
    ld a, (VFLAGS)
    and 0xDF
    ld (VFLAGS), a
    ld hl, T_REMNOW
    call say
    ret

; ---------------------------------------------------------- chat loop
chat_loop:
    xor a
    ld (VLEN), a
    ld (VVIEW), a
    call render
cl_p:
    call remind_tick
    call getkey
    cp KEY_NONE
    jp z, cl_p
    cp KEY_NEWLN
    jp z, cl_sub
    cp KUP
    jp z, cl_up
    cp KDN
    jp z, cl_dn
    cp KEY_BS
    jp z, cl_bs
    cp KTEMP
    jp c, cl_norm
    cp KREAS
    jp z, cl_reas
    jp nc, cl_p
cl_temp:
    sub KTEMP
    inc a
    ld (VTEMP), a
    ld hl, T_TEMPOK
    call print_enc
    ld a, (VTEMP)
    add a, 0x1C
    call wr_ch
    call wr_lineend
    jp cl_next
cl_reas:
    ld a, (VREAS)
    or a
    jr nz, cl_re0
    ld a, 2
    jr cl_re1
cl_re0:
    xor a
cl_re1:
    ld (VREAS), a
    ld hl, T_REASOK
    call print_enc
    ld a, (VREAS)
    add a, 0x1C
    call wr_ch
    call wr_lineend
    jp cl_next
cl_norm:
    cp 0x80
    jp c, cl_add
    jp cl_p
cl_add:
    ld (SCR0), a
    ld a, (VLEN)
    cp 27
    jp nc, cl_p
    ld c, a
    ld hl, LINEIN
    ld b, 0
    add hl, bc
    ld a, (SCR0)
    ld (hl), a
    ld a, c
    inc a
    ld (VLEN), a
    call render
    jp cl_p
cl_bs:
    ld a, (VLEN)
    or a
    jp z, cl_p
    dec a
    ld (VLEN), a
    call render
    jp cl_p
cl_up:
    ld a, (VVIEW)
    cp 20
    jp nc, cl_p
    add a, 20
    ld (VVIEW), a
    call render
    jp cl_p
cl_dn:
    ld a, (VVIEW)
    or a
    jp z, cl_p
    sub 20
    jr nc, cl_dn1
    xor a
cl_dn1:
    ld (VVIEW), a
    call render
    jp cl_p
cl_sub:
    call build_doc
    ld a, (VLEN)
    or a
    jr z, cl_next
    ld a, (0x4034)
    ld (SCR6), a
    call q_header
    ld hl, T_UBR
    call print_enc
    ld hl, LINEIN
    ld a, (VLEN)
    ld b, a
    call print_b
    call wr_lineend
    xor a
    ld (VVIEW), a
    ld a, (DOCBUF)
    cp 0x18
    jr z, cl_cmd
    call think_tick
    call match
    call think_tick
    call a_header
    call dispatch
    jr cl_next
cl_cmd:
    call cmd_run
cl_next:
    call render
    jp chat_loop

; ---------------------------------------------------------- boot flow
boot_flow:
    ; Explicit startup setup. No optional gate can accidentally skip the form.
    call df_splash
    xor a
    call df_clearrow
    ld hl, T_SETUP
    call df_rowblit
    ld a, 17
    ld (VBRM), a

    ld hl, P_DATE
    call bq
    call type_line
    call parse_date
    ld a, (VFLAGS)
    or 4
    ld (VFLAGS), a

    ld hl, P_TIME
    call bq
    call type_line
    call parse_time

    ld hl, P_NAME
    call bq
    call type_line
    call name_store
    xor a
    ld (VLEN), a

    ld hl, P_CALL
    call bq
    call type_line
    call addr_store
    xor a
    ld (VLEN), a

    ld a, (MEMADD + MJCOUNT)
    or a
    jr z, bf_noc
    ld hl, P_CARE
    call bq
    call yn_key
    or a
    jr z, bf_noc
    xor a
    ld (MEMADD + MJCOUNT), a
    ld hl, T_CLEARED
    call say
bf_noc:
    ld hl, T_START
    call bq
    call boot_dots
    ld hl, T_READY
    call bq
    ld a, (VFLAGS)
    bit 1, a
    ld hl, T_WELCOME
    jr nz, bf_w2
    ld hl, T_HELLOFRESH
bf_w2:
    call say
    ld a, (MEMADD + MJCOUNT)
    or a
    jr z, bf_noj
    ld hl, T_KEPTNOTES
    call say
bf_noj:
    ld hl, T_HINT
    jp say

; LINEIN codes -> ASCII address/nickname in the MEM slot;
; empty input keeps the name as address
addr_store:
    ld a, (VLEN)
    or a
    jr z, as_def
    ld hl, LINEIN
    ld de, MEMADD + MADDR
    ld c, a
    cp 12
    jr c, as_l
    ld c, 12
as_l:
    ld a, c
    or a
    jr z, as_z
    dec c
    ld a, (hl)
    push hl
    call cvn_as
    pop hl
    inc hl
    ld (de), a
    inc de
    jr as_l
as_def:
    ld hl, MEMADD + MNAME
    ld de, MEMADD + MADDR
    ld b, 12
as_d:
    ld a, (hl)
    or a
    jr z, as_z
    ld (de), a
    inc hl
    inc de
    djnz as_d
as_z:
    xor a
    ld (de), a
    ld a, (VFLAGS)
    or 1
    ld (VFLAGS), a
    ret

; ---------------------------------------------------------- data
; keyboard plain codes, index = row*5+col, first byte of row0 is SHIFT
KBPLAIN:
    db 0xFF
    db 0x3F, 0x3D, 0x28, 0x3B
    db 0x26, 0x38, 0x29, 0x2B, 0x2C
    db 0x36, 0x3C, 0x2A, 0x37, 0x39
    db 0x1D, 0x1E, 0x1F, 0x20, 0x21
    db 0x1C, 0x25, 0x24, 0x23, 0x22
    db 0x35, 0x34, 0x2E, 0x3A, 0x3E
    db 0x80, 0x31, 0x30, 0x2F, 0x2D
    db 0x00, 0x1B, 0x32, 0x33, 0x27

; shifted codes; shift+z = colon, shift+x = semi, shift+c = ?, shift+v = /
; shift+0 = backspace 0x81, shift+7 = page up 0x82, shift+6 = page down 0x83
; shift+1..4 = temperature 1..4, shift+9 = reasoning on/off
KBSHIFT:
    db 0xFF
    db 0x0E, 0x19, 0x0F, 0x18
    db 0xFF, 0xFF, 0xFF, 0xFF, 0xFF
    db 0xFF, 0xFF, 0xFF, 0xFF, 0xFF
    db 0x84, 0x85, 0x86, 0x87, 0xFF
    db 0x81, 0x88, 0xFF, 0x82, 0x83
    db 0x0B, 0x11, 0x10, 0xFF, 0xFF
    db 0x80, 0x14, 0x15, 0x16, 0xFF
    db 0x00, 0x1A, 0x12, 0x13, 0x17

ARTBL:                  ; big "ZX81 AI": 8 rows x 31 block-chars
    db 0x80, 0x80, 0x80, 0x80, 0x80, 0x00, 0x80, 0x00, 0x00, 0x00, 0x80, 0x00, 0x00, 0x80, 0x80, 0x80, 0x00, 0x00, 0x00, 0x80, 0x00, 0x00, 0x00, 0x80, 0x80, 0x80, 0x00, 0x00, 0x80, 0x80, 0x80
    db 0x00, 0x00, 0x00, 0x00, 0x80, 0x00, 0x00, 0x80, 0x00, 0x80, 0x00, 0x00, 0x80, 0x00, 0x00, 0x00, 0x80, 0x00, 0x80, 0x80, 0x00, 0x00, 0x80, 0x00, 0x00, 0x00, 0x80, 0x00, 0x00, 0x80, 0x00
    db 0x00, 0x00, 0x00, 0x80, 0x00, 0x00, 0x00, 0x00, 0x80, 0x00, 0x00, 0x00, 0x80, 0x00, 0x00, 0x00, 0x80, 0x00, 0x00, 0x80, 0x00, 0x00, 0x80, 0x00, 0x00, 0x00, 0x80, 0x00, 0x00, 0x80, 0x00
    db 0x00, 0x00, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x80, 0x00, 0x00, 0x00, 0x00, 0x80, 0x80, 0x80, 0x00, 0x00, 0x80, 0x00, 0x00, 0x80, 0x80, 0x80, 0x80, 0x80, 0x00, 0x00, 0x80, 0x00
    db 0x00, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x80, 0x00, 0x00, 0x00, 0x80, 0x00, 0x00, 0x00, 0x80, 0x00, 0x00, 0x80, 0x00, 0x00, 0x80, 0x00, 0x00, 0x00, 0x80, 0x00, 0x00, 0x80, 0x00
    db 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x80, 0x00, 0x80, 0x00, 0x00, 0x80, 0x00, 0x00, 0x00, 0x80, 0x00, 0x00, 0x80, 0x00, 0x00, 0x80, 0x00, 0x00, 0x00, 0x80, 0x00, 0x00, 0x80, 0x00
    db 0x80, 0x80, 0x80, 0x80, 0x80, 0x00, 0x80, 0x00, 0x00, 0x00, 0x80, 0x00, 0x00, 0x80, 0x80, 0x80, 0x00, 0x00, 0x80, 0x80, 0x80, 0x00, 0x80, 0x00, 0x00, 0x00, 0x80, 0x00, 0x80, 0x80, 0x80
    db 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00

CAPTXT:
    db "MILO V0.2"

ST0A:
    db "milo  v2 t="
ST0B:
    db " r="
ST1BA:
    db "bank base"
ST1WE:
    db "bank knowledge"
ST1RE:
    db "bank games"
ST1PG:
    db " pg="
ST1FG:
    db " f="
RIN:
    db "you "

GENDTBL:
    db 5, 2, 0x3C, 0x34, 0x32, 0x26, 0x33
    db 4, 2, 0x2C, 0x2E, 0x37, 0x31
    db 6, 2, 0x2B, 0x2A, 0x32, 0x26, 0x31, 0x2A
    db 3, 1, 0x27, 0x34, 0x38
    db 3, 1, 0x32, 0x26, 0x33
    db 4, 1, 0x32, 0x26, 0x31, 0x2A
    db 0

TAGTBL:
    db 8, 0x2D, 0x2A, 0x26, 0x29, 0x26, 0x28, 0x2D, 0x2A
    db 5, 0x2B, 0x2A, 0x37, 0x2A, 0x37
    db 5, 0x39, 0x2E, 0x37, 0x2A, 0x29
    db 4, 0x35, 0x26, 0x2E, 0x33
    db 4, 0x38, 0x2E, 0x28, 0x30
    db 3, 0x38, 0x26, 0x29
    db 3, 0x2E, 0x31, 0x31
    db 0

T_D0:
    db "sunday"
T_D1:
    db "monday"
T_D2:
    db "tuesday"
T_D3:
    db "wednesday"
T_D4:
    db "thursday"
T_D5:
    db "friday"
T_D6:
    db "saturday"
DWTBL:
    dw T_D0, T_D1, T_D2, T_D3, T_D4, T_D5, T_D6

htab:
    dw h0, h1, h2, h3, h4, h5, h6, h7, h8, h9
    dw h10, h11, h12, h13, h14, h15, h16, h17, h18, h19

CMD_HELP:
    db "help"
CMD_TOPICS:
    db "topics"
CMD_TEMP:
    db "temp"
CMD_REAS:
    db "reason"
CMD_MEM:
    db "mem"
CMD_SAVE:
    db "save"
CMD_QUIT:
    db "quit"
CMD_FOGT:
    db "forget"
CMD_COFFEE:
    db "coffee"
CMD_TIME:
    db "time"
CMD_REMIND:
    db "remind"

PH_HELP    equ 0x6A60      ; parked boot prompt slots (weather slot tail)
PH_DATE    equ 0x6AA0
PH_TIME    equ 0x6AE0
PH_NAME    equ 0x6B20
PH_CALL    equ 0x6B60
PH_CARE    equ 0x6BA0
P_HELP     equ PH_HELP
P_DATE     equ PH_DATE
P_TIME     equ PH_TIME
P_NAME     equ PH_NAME
P_CALL     equ PH_CALL
P_CARE     equ PH_CARE

T_SETUP:
    db "MILO V0.2 - SETUP"
T_START:
    db "start the tape"
T_READY:
    db "ready."
T_WELCOME:
    db "welcome back, $n. frame, engine and base bank are live."
T_HELLOFRESH:
    db "hello. fresh tape here. teach me: my name is ..."
T_KEPTNOTES:
    db "i keep notes from last time. ask: do you remember"
T_HINT:
    db "try /help or /topics. commands: /time hh mm /remind n"
T_UBR:
    db "you: "
T_UNKN:
    db "i do not know that yet. ask /topics or teach me a fact."
T_NOBDAY:
    db "your birthday is not set. try: my birthday is 21 3"
T_NOJ:
    db "my journal is empty. tell me how you feel."
T_ON3:
    db "on "
T_NOTE:
    db "note"
T_BADB:
    db "hmm. give it like: my birthday is 21 3"
T_BADCMD:
    db "unknown command. try /help."
T_TOPICS:
    db "topics: health philosophy learning-basic learning-school art music astronomy programming cars motorcycles retro kirrda games. packs: knowledge games."
T_SAVED:
    db "memory saved into the base bank."
T_BYE:
    db "bye $n. the tape keeps your memory."
T_FORGOT:
    db "forgotten. name, town and notes are empty."
T_MEMN:
    db "name: $n"
T_MEMT:
    db "town: $l"
T_MEMG:
    db "gender: $g"
T_MEMB:
    db "birthday: $b"
T_TEMPOK:
    db "temperature now "
T_REASOK:
    db "reasoning level "
T_ARGERR:
    db "give a number, like /temp 3"
T_TIMEOK:
    db "time set."
T_TIMEBAD:
    db "time format: /time hh mm"
T_REMSET:
    db "reminder set in "
T_MINUTES:
    db " minute(s)."
T_REMBAD:
    db "remind 1 to 5 minutes: /remind 2"
T_REMNOW:
    db "reminder: you asked me to speak now."
T_LOADING:
    db "loading"
T_PLOADED:
    db "pack loaded. type away."
T_NL:
    db "not loaded. the tape stops here."
T_PACKON:
    db "that pack is already loaded."
T_CLEARED:
    db "good news. i cleared the health notes."
T_QHEAD:
    db " Q "
T_QTOK:
    db " tok="
T_AHEAD:
    db " A "
T_ADT:
    db " dt="
T_AFR:
    db "f"
T_THINKBAR:
    db "thinking... "
T_THINK0:
    db "  thinking...    "
T_COFFEE0:
    db " coffee: warming up "
T_COFFEE1:
    db " coffee: heating   "
T_COFFEE2:
    db " coffee: brewing   "
T_COFFEE3:
    db " coffee: pouring   "
T_COFFEE_DONE:
    db " coffee: DONE!     "
T_COFFEE_MSG:
    db "coffee ready. no sugar? /coffee again."
T_AUTHOR:
    db "milo was made and trained by the mistral model, from the design of safar sandor."
T_SAFAR:
    db "Magyarorszagon elo buszvezeto, hobbi csillagasz es programozo (safizx81@gmail.com), amator iro (Alexander Steward iroi even)."
T_KIRRDA:
    db "kirrda is a science fiction adventure by safar sandor, written as alexander steward. aliens catch an old earth tv broadcast, then a catastrophe drives survivors toward earth and new friends."
T_TEACH:
    db "teach me with simple facts and sentences. names, places and feelings can be remembered; general facts are a future learning feature."
T_DRAW:
    db "yes. i can describe zx81 drawings and give plot or unplot basic. say: draw a house."
T_CODE:
    db "yes. ask for a short zx81 basic program, for example a clock, sine wave, game or plot drawing."
T_STORY:
    db "i can tell short stories. ask: write a short story, or give me a place and a character."
T_GAMES:
    db "games are experimental: number tricks, riddles, true-false, chess ideas and text adventures. say: game or riddle."
T_THINK:
    db " think: "
T_BBASE:
    db "base"
T_BWEA:
    db "weather"
T_BRET:
    db "retro"
T_CONFP:
    db " conf: "
T_CHIGH:
    db "high"
T_CMID:
    db "mid"
T_CLOW:
    db "low"
T_MORE:
    db "# give me more detail please"
T_BOY:
    db "boy"
T_GIRL:
    db "girl"
T_PERSON:
    db "you"
T_MORN:
    db "morning"
T_AFT:
    db "afternoon"
T_EVE:
    db "evening"
T_NIGHT:
    db "night"

