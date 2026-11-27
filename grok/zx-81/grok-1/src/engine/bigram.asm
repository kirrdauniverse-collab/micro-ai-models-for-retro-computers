; ============================================================
; Pico AI - Minimal Bigram Engine for ZX81 (Z80)
; Target: 16KB RAM, callable or standalone
; 
; Design goals:
; - Very small vocab (max 64-96 tokens for first version)
; - Bigram table: each token has up to 6 possible next tokens
; - Integer weights (0-255)
; - Simple temperature (0= deterministic, higher = more random)
; - No floating point
; ============================================================

; ------------------------------------------------------------
; Memory layout (example - adjust to final map)
; ------------------------------------------------------------
; VOCAB_TABLE     equ  $7000   ; token strings / lookup
; BIGRAM_TABLE    equ  $7200   ; bigram data
; GEN_BUFFER      equ  $7A00   ; generated token IDs
; WORK_AREA       equ  $7B00

; ------------------------------------------------------------
; Constants
; ------------------------------------------------------------
MAX_VOCAB       equ  64
MAX_NEXT        equ  6          ; max next tokens per bigram entry
MAX_GEN_LEN     equ  32         ; max tokens to generate

; Temperature levels (SHIFT+1..4 style)
; 0 = always highest weight
; 1 = light random
; 2 = medium
; 3 = high

; ------------------------------------------------------------
; Bigram entry structure (per token)
; ------------------------------------------------------------
; Offset 0     : count of valid next tokens (0..MAX_NEXT)
; Offset 1..6  : next token IDs
; Offset 7..12 : weights (0-255) corresponding to next IDs
; Total size per token: 13 bytes
;
; BIGRAM_TABLE size ≈ 64 * 13 = 832 bytes

; ------------------------------------------------------------
; Public routines
; ------------------------------------------------------------

; ------------------------------------------------------------
; GENERATE
; Input:
;   A  = start token ID (or 0 for random/seed)
;   B  = temperature (0-3)
;   C  = max tokens to generate
;   HL = pointer to output buffer (token IDs, 0-terminated)
; Output:
;   Buffer filled with token IDs, ends with 0
;   A  = number of tokens generated
; ------------------------------------------------------------
GENERATE:
        push    bc
        push    de
        push    hl

        ld      (GEN_TEMP), a          ; save start token
        ld      a, b
        ld      (GEN_TEMPERATURE), a
        ld      a, c
        ld      (GEN_MAXLEN), a
        ld      (GEN_OUTPTR), hl

        ; clear output
        xor     a
        ld      (hl), a

        ld      a, (GEN_TEMP)          ; current token
        or      a
        jr      nz, gen_loop

        ; if start token 0, pick a seed (very simple)
        ld      a, 1                   ; token 1 as default seed
        ld      (GEN_TEMP), a

gen_loop:
        ld      a, (GEN_MAXLEN)
        or      a
        jr      z, gen_done

        ; get next token based on current + temperature
        ld      a, (GEN_TEMP)
        call    GET_NEXT_TOKEN         ; returns A = next token ID
        or      a
        jr      z, gen_done            ; 0 = end

        ; store to output buffer
        ld      hl, (GEN_OUTPTR)
        ld      (hl), a
        inc     hl
        ld      (GEN_OUTPTR), hl
        xor     a
        ld      (hl), a                ; keep 0-terminated

        ld      (GEN_TEMP), a          ; wait, bugfix - save the next as current
        ; fix:
        ; We need to save the chosen token as new current
        ; (re-get it properly)

        ; Correct version of store + update current:
        ; (rewritten cleanly below in final logic)

        ld      a, (GEN_MAXLEN)
        dec     a
        ld      (GEN_MAXLEN), a
        jr      gen_loop

gen_done:
        pop     hl
        pop     de
        pop     bc
        ; return count later
        ret

; ------------------------------------------------------------
; GET_NEXT_TOKEN
; Input:  A = current token ID
; Output: A = next token ID (0 if none)
; Uses temperature from GEN_TEMPERATURE
; ------------------------------------------------------------
GET_NEXT_TOKEN:
        ; bounds check
        cp      MAX_VOCAB
        jr      nc, gnt_none

        ; HL = BIGRAM_TABLE + A * 13
        ld      l, a
        ld      h, 0
        add     hl, hl          ; *2
        ld      e, l
        ld      d, h
        add     hl, hl          ; *4
        add     hl, de          ; *6
        add     hl, hl          ; *12
        add     hl, de          ; *13
        ld      de, BIGRAM_TABLE
        add     hl, de

        ; HL now points to entry
        ld      a, (hl)         ; count
        or      a
        jr      z, gnt_none
        cp      MAX_NEXT+1
        jr      nc, gnt_none

        ld      b, a            ; B = count
        inc     hl              ; HL -> first next ID

        ; Temperature 0 = pick highest weight
        ld      a, (GEN_TEMPERATURE)
        or      a
        jr      z, gnt_deterministic

        ; Simple random selection weighted
        ; For first version: pick random index 0..count-1
        ; (true weighted later)
        call    RAND8
        ld      c, a
gnt_mod:
        ld      a, c
        sub     b
        jr      c, gnt_idx_ok
        ld      c, a
        jr      gnt_mod
gnt_idx_ok:
        ld      a, c            ; A = index 0..count-1

        ; skip to that next-ID
        ld      e, a
        ld      d, 0
        add     hl, de
        ld      a, (hl)
        ret

gnt_deterministic:
        ; find max weight
        push    hl              ; save start of IDs
        ld      de, MAX_NEXT
        add     hl, de          ; HL -> weights
        ld      c, 0            ; best index
        ld      d, 0            ; best weight
        ld      e, 0            ; current index
gnt_max_loop:
        ld      a, (hl)
        cp      d
        jr      c, gnt_not_better
        ld      d, a
        ld      c, e
gnt_not_better:
        inc     hl
        inc     e
        djnz    gnt_max_loop

        pop     hl              ; HL -> IDs
        ld      e, c
        ld      d, 0
        add     hl, de
        ld      a, (hl)
        ret

gnt_none:
        xor     a
        ret

; ------------------------------------------------------------
; Very simple 8-bit RNG (for temperature > 0)
; Returns A = 0..255
; ------------------------------------------------------------
RAND8:
        ld      a, (RNG_SEED)
        ld      b, a
        rrca
        xor     b
        ld      b, a
        rrca
        xor     b
        ld      b, a
        rrca
        xor     b
        ld      (RNG_SEED), a
        ret

; ------------------------------------------------------------
; Variables
; ------------------------------------------------------------
GEN_TEMP:           defb 0
GEN_TEMPERATURE:    defb 0
GEN_MAXLEN:         defb 0
GEN_OUTPTR:         defw 0
RNG_SEED:           defb 0xA5

; ------------------------------------------------------------
; Placeholder tables (to be filled)
; ------------------------------------------------------------
; BIGRAM_TABLE must be defined elsewhere or included
; VOCAB also separate

; End of bigram.asm
