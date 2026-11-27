10 REM PICO AI MODEL V0.5 - SMART BASIC
20 REM Token-like keywords, mood, math, thinking, temp learning

100 CLS
110 PRINT "PICO AI V0.5 READY"
120 PRINT "Type HELP for commands"
130 PRINT 
140 LET MOOD=1
150 LET TEMP=2
160 LET LEARN$=""
170 LET USER$="Friend"
180 DIM F$(10,20)
190 LET FN=0

200 PRINT "----------------"
210 PRINT "YOU: ";
220 INPUT A$
230 PRINT "YOU: ";A$
240 PRINT 

250 REM THINKING
260 PRINT "PICO thinking..."
270 PAUSE 20+TEMP*10
280 PRINT 

290 REM EMPTY
300 IF A$="" THEN GOTO 200

310 REM COMMANDS
320 IF A$="BYE" OR A$="bye" THEN GOTO 9000
330 IF A$="HELP" OR A$="help" THEN GOTO 8000
340 IF A$="MOOD" OR A$="mood" THEN GOTO 7000
350 IF A$="TEMP" OR A$="temp" THEN GOTO 7100
360 IF A$="NAME" OR A$="name" THEN GOTO 7200
370 IF A$="TIME" OR A$="time" THEN GOTO 7300
380 IF A$="LEARN" OR A$="learn" THEN GOTO 7400

400 REM MOOD DETECT
410 IF A$="SAD" OR A$="sad" OR A$="szomoru" THEN LET MOOD=0
420 IF A$="HAPPY" OR A$="happy" OR A$="boldog" THEN LET MOOD=2
430 IF A$="ANGRY" OR A$="angry" OR A$="merges" THEN LET MOOD=3

500 REM MATH
510 IF A$="1+1" OR A$="1 + 1" THEN GOTO 6000
520 IF A$="2+2" OR A$="2 + 2" THEN GOTO 6010
530 IF A$="10-3" OR A$="10 - 3" THEN GOTO 6020

550 REM COLORS
560 IF A$="BLUE AND YELLOW" OR A$="blue and yellow" THEN GOTO 6100
570 IF A$="RED AND BLUE" OR A$="red and blue" THEN GOTO 6110
580 IF A$="RED AND YELLOW" OR A$="red and yellow" THEN GOTO 6120

600 REM KNOWLEDGE
610 IF A$="HELLO" OR A$="hello" OR A$="HI" OR A$="hi" THEN GOTO 5000
620 IF A$="WHO ARE YOU" OR A$="who are you" THEN GOTO 5100
630 IF A$="WHO MADE YOU" OR A$="who made you" THEN GOTO 5200
640 IF A$="WHAT IS ZX81" OR A$="what is zx81" THEN GOTO 5300
650 IF A$="WHAT CAN YOU DO" OR A$="what can you do" THEN GOTO 5400
660 IF A$="TELL ME A JOKE" OR A$="joke" THEN GOTO 5500
670 IF A$="STORY" OR A$="story" THEN GOTO 5600

700 REM UNKNOWN / LEARNED
710 IF LEARN$<>"" AND A$=LEARN$ THEN GOTO 7500
720 GOTO 5800

5000 REM HELLO
5010 IF MOOD=0 THEN PRINT "PICO: Hello... hope you feel better."
5020 IF MOOD=1 THEN PRINT "PICO: Hello ";USER$;"!"
5030 IF MOOD=2 THEN PRINT "PICO: Hey! Great to see you!"
5040 IF MOOD=3 THEN PRINT "PICO: ...hello."
5050 PRINT 
5060 GOTO 200

5100 PRINT "PICO: I am Pico AI, a tiny"
5110 PRINT "model running on ZX81."
5120 PRINT "I use keywords and simple"
5130 PRINT "rules. Real tokens coming."
5140 PRINT 
5150 GOTO 200

5200 PRINT "PICO: Made with help by"
5210 PRINT "Safar Sandor from Hungary."
5220 PRINT "Bus driver, writer,"
5230 PRINT "astronomer."
5240 PRINT 
5250 GOTO 200

5300 PRINT "PICO: ZX81 is a 1981"
5310 PRINT "Sinclair computer. Many"
5320 PRINT "had only 16K RAM."
5330 PRINT 
5340 GOTO 200

5400 PRINT "PICO: I can chat, do simple"
5410 PRINT "math, mix colors, detect"
5420 PRINT "mood, learn one fact, and"
5430 PRINT "tell a short story."
5440 PRINT "Type HELP for more."
5450 PRINT 
5460 GOTO 200

5500 IF TEMP>1 AND RND>0.5 THEN GOTO 5520
5510 PRINT "PICO: Why did the computer"
5515 PRINT "go to therapy? It had too"
5516 PRINT "many bytes of emotional"
5517 PRINT "baggage."
5518 PRINT 
5519 GOTO 200
5520 PRINT "PICO: I told a ZX81 joke"
5525 PRINT "but it took 16K to laugh."
5526 PRINT 
5527 GOTO 200

5600 PRINT "PICO: Once there was a"
5610 PRINT "little computer who dreamed"
5620 PRINT "of talking. One day a human"
5630 PRINT "loaded a tiny AI... and it"
5640 PRINT "said: Hello."
5650 PRINT 
5660 GOTO 200

5800 PRINT "PICO: I do not understand."
5810 PRINT "Try HELP or ask something"
5820 PRINT "else. Or teach me with"
5830 PRINT "LEARN."
5840 PRINT 
5850 GOTO 200

6000 PRINT "PICO: 1+1 = 2"
6005 PRINT 
6006 GOTO 200
6010 PRINT "PICO: 2+2 = 4"
6015 PRINT 
6016 GOTO 200
6020 PRINT "PICO: 10-3 = 7"
6025 PRINT 
6026 GOTO 200

6100 PRINT "PICO: Blue + Yellow = Green"
6105 PRINT 
6106 GOTO 200
6110 PRINT "PICO: Red + Blue = Purple"
6115 PRINT 
6116 GOTO 200
6120 PRINT "PICO: Red + Yellow = Orange"
6125 PRINT 
6126 GOTO 200

7000 PRINT "PICO: Current mood code: ";MOOD
7010 PRINT "0=sad 1=normal 2=happy 3=angry"
7020 PRINT "Say SAD / HAPPY / ANGRY to change"
7030 PRINT 
7040 GOTO 200

7100 PRINT "PICO: Temperature ";TEMP
7110 PRINT "Higher = more random replies"
7120 PRINT "Set with TEMP 0 to 3 later"
7130 PRINT 
7140 GOTO 200

7200 PRINT "PICO: What is your name?"
7210 INPUT USER$
7220 IF USER$="" THEN LET USER$="Friend"
7230 PRINT "PICO: Nice to meet you, ";USER$
7240 PRINT 
7250 GOTO 200

7300 PRINT "PICO: I have no real clock."
7310 PRINT "I only know what you told"
7320 PRINT "the loader."
7330 PRINT 
7340 GOTO 200

7400 PRINT "PICO: Teach me one short"
7410 PRINT "fact (max 20 chars)."
7420 INPUT LEARN$
7430 IF LEN LEARN$>20 THEN LET LEARN$=LEARN$( TO 20)
7440 PRINT "PICO: I will remember:"
7450 PRINT LEARN$
7460 PRINT 
7470 GOTO 200

7500 PRINT "PICO: You taught me:"
7510 PRINT LEARN$
7520 PRINT 
7530 GOTO 200

8000 PRINT "COMMANDS:"
8010 PRINT " HELP  - this list"
8020 PRINT " BYE   - quit"
8030 PRINT " NAME  - set your name"
8040 PRINT " MOOD  - show mood"
8050 PRINT " TEMP  - show temperature"
8060 PRINT " LEARN - teach me one fact"
8070 PRINT " TIME  - about time"
8080 PRINT 
8090 PRINT "Try: hello, who are you,"
8100 PRINT "who made you, what is zx81,"
8110 PRINT "joke, story, 1+1,"
8120 PRINT "blue and yellow"
8130 PRINT 
8140 GOTO 200

9000 PRINT "PICO: Goodbye ";USER$;"!"
9010 PRINT 
9020 STOP
