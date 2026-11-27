; ============================================================
; Pico AI - First small vocabulary + example bigrams
; Tokens are 1-based. Token 0 = end / none
; ============================================================

MAX_VOCAB       equ  32          ; keep tiny for first test

; ------------------------------------------------------------
; Vocab as length-prefixed strings (ZX81 charset friendly)
; Format: len, chars..., 0-terminated list end
; ------------------------------------------------------------
VOCAB_TABLE:
        defb 5, "HELLO"          ; 1
        defb 3, "THE"            ; 2
        defb 2, "AI"             ; 3
        defb 4, "PICO"           ; 4
        defb 2, "IS"             ; 5
        defb 1, "A"              ; 6
        defb 4, "TINY"           ; 7
        defb 5, "MODEL"          ; 8
        defb 3, "FOR"            ; 9
        defb 4, "ZX81"           ; 10
        defb 4, "MADE"           ; 11
        defb 2, "BY"             ; 12
        defb 5, "SAFAR"          ; 13
        defb 6, "SANDOR"         ; 14
        defb 4, "WITH"           ; 15
        defb 3, "GLM"            ; 16
        defb 4, "HELP"           ; 17
        defb 4, "FROM"           ; 18
        defb 7, "HUNGARY"        ; 19
        defb 3, "YOU"            ; 20
        defb 3, "ARE"            ; 21
        defb 4, "WHAT"           ; 22
        defb 3, "WHO"            ; 23
        defb 4, "THIS"           ; 24
        defb 3, "CAN"            ; 25
        defb 2, "DO"             ; 26
        defb 4, "TALK"           ; 27
        defb 5, "ABOUT"          ; 28
        defb 4, "CODE"           ; 29
        defb 4, "REAL"           ; 30
        defb 5, "TOKEN"          ; 31
        defb 0                   ; end of vocab

; ------------------------------------------------------------
; Bigram table
; Each entry: count, nextID1..6, weight1..6
; Size = 32 * 13 = 416 bytes
; ------------------------------------------------------------
BIGRAM_TABLE:
        ; Token 0 (unused)
        defb 0, 0,0,0,0,0,0, 0,0,0,0,0,0

        ; 1 HELLO -> THE, YOU, PICO
        defb 3, 2,20,4,0,0,0, 180,120,100,0,0,0

        ; 2 THE -> AI, MODEL, ZX81, TINY
        defb 4, 3,8,10,7,0,0, 200,150,140,130,0,0

        ; 3 AI -> IS, MODEL, FOR
        defb 3, 5,8,9,0,0,0, 180,160,100,0,0,0

        ; 4 PICO -> IS, AI, CAN
        defb 3, 5,3,25,0,0,0, 200,150,80,0,0,0

        ; 5 IS -> A, THE, TINY, REAL
        defb 4, 6,2,7,30,0,0, 180,100,160,90,0,0

        ; 6 A -> TINY, MODEL, REAL
        defb 3, 7,8,30,0,0,0, 200,150,100,0,0,0

        ; 7 TINY -> MODEL, AI
        defb 2, 8,3,0,0,0,0, 220,80,0,0,0,0

        ; 8 MODEL -> FOR, IS, MADE
        defb 3, 9,5,11,0,0,0, 180,100,120,0,0,0

        ; 9 FOR -> THE, ZX81, YOU
        defb 3, 2,10,20,0,0,0, 150,200,80,0,0,0

        ; 10 ZX81
        defb 2, 5,11,0,0,0,0, 100,80,0,0,0,0

        ; 11 MADE -> BY, WITH
        defb 2, 12,15,0,0,0,0, 220,100,0,0,0,0

        ; 12 BY -> SAFAR, SANDOR
        defb 2, 13,14,0,0,0,0, 200,180,0,0,0,0

        ; 13 SAFAR -> SANDOR
        defb 1, 14,0,0,0,0,0, 255,0,0,0,0,0

        ; 14 SANDOR -> FROM, WITH
        defb 2, 18,15,0,0,0,0, 150,100,0,0,0,0

        ; 15 WITH -> GLM, HELP
        defb 2, 16,17,0,0,0,0, 200,150,0,0,0,0

        ; 16 GLM -> HELP
        defb 1, 17,0,0,0,0,0, 255,0,0,0,0,0

        ; 17 HELP
        defb 1, 18,0,0,0,0,0, 100,0,0,0,0,0

        ; 18 FROM -> HUNGARY
        defb 1, 19,0,0,0,0,0, 255,0,0,0,0,0

        ; 19 HUNGARY
        defb 0, 0,0,0,0,0,0, 0,0,0,0,0,0

        ; 20 YOU -> ARE, CAN
        defb 2, 21,25,0,0,0,0, 200,100,0,0,0,0

        ; 21 ARE -> A, THE
        defb 2, 6,2,0,0,0,0, 150,100,0,0,0,0

        ; 22 WHAT -> IS, CAN
        defb 2, 5,25,0,0,0,0, 200,120,0,0,0,0

        ; 23 WHO -> MADE, ARE
        defb 2, 11,21,0,0,0,0, 220,80,0,0,0,0

        ; 24 THIS -> IS
        defb 1, 5,0,0,0,0,0, 255,0,0,0,0,0

        ; 25 CAN -> DO, TALK
        defb 2, 26,27,0,0,0,0, 180,150,0,0,0,0

        ; 26 DO
        defb 1, 28,0,0,0,0,0, 100,0,0,0,0,0

        ; 27 TALK -> ABOUT
        defb 1, 28,0,0,0,0,0, 255,0,0,0,0,0

        ; 28 ABOUT -> THE, CODE, AI
        defb 3, 2,29,3,0,0,0, 150,120,100,0,0,0

        ; 29 CODE
        defb 1, 5,0,0,0,0,0, 80,0,0,0,0,0

        ; 30 REAL -> TOKEN, MODEL, AI
        defb 3, 31,8,3,0,0,0, 180,150,100,0,0,0

        ; 31 TOKEN -> MODEL
        defb 1, 8,0,0,0,0,0, 200,0,0,0,0,0
