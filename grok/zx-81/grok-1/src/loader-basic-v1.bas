10 REM *** PICO AI - ZX81 MICRO LANGUAGE MODEL ***
20 REM First stage BASIC loader
30 REM Sets RAMTOP and prepares protected memory

100 CLS
110 PRINT 
120 PRINT "    ****  PICO AI  ****"
130 PRINT "  ZX81 Micro Language Model"
140 PRINT 
150 PRINT "Made with GLM help by"
160 PRINT "Safar Sandor"
170 PRINT 
180 PRINT "A tiny real AI that runs"
190 PRINT "in 16K on your ZX81."
200 PRINT 
210 PRINT "It uses tokens and simple"
220 PRINT "statistics to generate"
230 PRINT "answers - not just fixed"
240 PRINT "sentences."
250 PRINT 
260 PRINT "Press any key for more..."
270 PAUSE 4E4

300 CLS
310 PRINT "HOW IT WORKS"
320 PRINT 
330 PRINT "1. This program will set"
340 PRINT "   RAMTOP to protect the"
350 PRINT "   upper memory."
360 PRINT 
370 PRINT "2. After NEW the upper"
380 PRINT "   area stays safe."
390 PRINT 
400 PRINT "3. You must then LOAD the"
410 PRINT "   next block manually:"
420 PRINT "   LOAD """""
430 PRINT 
440 PRINT "4. Later blocks can change"
450 PRINT "   knowledge, but your"
460 PRINT "   personal data stays."
470 PRINT 
480 PRINT "Press any key..."
490 PAUSE 4E4

500 CLS
510 PRINT "IMPORTANT"
520 PRINT 
530 PRINT "After you press ENTER the"
540 PRINT "computer will do NEW."
550 PRINT 
560 PRINT "Then type:"
570 PRINT "  LOAD """""
580 PRINT "and start the tape again."
590 PRINT 
600 PRINT "Ready to continue?"
610 PRINT 
620 PRINT "Press ENTER to set RAMTOP"
630 PRINT "and restart..."
640 INPUT A$

700 REM Set RAMTOP (example value - will be tuned)
710 REM 30000 = roughly 0x7530
720 POKE 16388,48
730 POKE 16389,117
740 REM 117*256 + 48 = 30000

750 PRINT 
760 PRINT "RAMTOP set. Doing NEW..."
770 PAUSE 100
780 NEW

790 REM This line is never reached
800 STOP
