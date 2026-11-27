10 REM PICO AI LOADER V0.3
20 REM More tolerant input + help option
30 REM Collects name, gender, date, time then RAMTOP+NEW

100 CLS
110 PRINT "    ****  PICO AI  ****"
120 PRINT "  ZX81 Micro Language Model"
130 PRINT 
140 PRINT "Made with GLM help by"
150 PRINT "Safar Sandor"
160 PRINT 
170 PRINT "A tiny real AI for your"
180 PRINT "16K ZX81."
190 PRINT 
200 PRINT "Press H for help"
210 PRINT "or any other key to start..."
220 PAUSE 4E4
230 IF INKEY$="H" OR INKEY$="h" THEN GOTO 2000

300 CLS
310 PRINT "PERSONAL DATA"
320 PRINT 
330 PRINT "I need a few things to"
340 PRINT "remember you."
350 PRINT 

360 PRINT "Your name (max 12)?"
370 INPUT N$
380 IF LEN N$>12 THEN LET N$=N$( TO 12)
390 IF N$="" THEN LET N$="Friend"

400 PRINT 
410 PRINT "Gender (M/F)?"
420 INPUT G$
430 IF G$="" THEN LET G$="M"
440 LET G$=G$(1)
450 IF G$="m" THEN LET G$="M"
460 IF G$="f" THEN LET G$="F"
470 IF G$<>"M" AND G$<>"F" THEN LET G$="M"

480 PRINT 
490 PRINT "Date (any format ok)"
500 PRINT "e.g. 05/06/2026 or 5 6 26"
510 INPUT D$
520 IF D$="" THEN LET D$="01/01/2026"

530 PRINT 
540 PRINT "Time (any format ok)"
550 PRINT "e.g. 04:17 or 4 17"
560 INPUT T$
570 IF T$="" THEN LET T$="12:00"

600 CLS
610 PRINT "CONFIRM"
620 PRINT 
630 PRINT "Name: ";N$
640 PRINT "Gender: ";G$
650 PRINT "Date: ";D$
660 PRINT "Time: ";T$
670 PRINT 
680 PRINT "Correct (Y/N)?"
690 INPUT C$
700 IF C$="N" OR C$="n" THEN GOTO 300

800 CLS
810 PRINT "LOADER INFO"
820 PRINT 
830 PRINT "1. I set RAMTOP so upper"
840 PRINT "   memory stays protected."
850 PRINT 
860 PRINT "2. Then I do NEW."
870 PRINT 
880 PRINT "3. After NEW type:"
890 PRINT "   LOAD """""
900 PRINT "   and start the tape."
910 PRINT 
920 PRINT "Your data will be kept"
930 PRINT "by the next block."
940 PRINT 
950 PRINT "Press ENTER..."
960 INPUT A$

1000 POKE 16388,48
1010 POKE 16389,117
1020 PRINT 
1030 PRINT "RAMTOP=30000. NEW..."
1040 PAUSE 100
1050 NEW
1060 STOP

2000 CLS
2010 PRINT "HELP - PICO AI"
2020 PRINT 
2030 PRINT "This is the first stage."
2040 PRINT "It collects your name,"
2050 PRINT "gender, date and time."
2060 PRINT 
2070 PRINT "Then protects upper memory"
2080 PRINT "with RAMTOP and does NEW."
2090 PRINT 
2100 PRINT "After that load the next"
2110 PRINT "block with LOAD """""
2120 PRINT 
2130 PRINT "Later versions will have"
2140 PRINT "real token generation."
2150 PRINT 
2160 PRINT "Press any key..."
2170 PAUSE 4E4
2180 GOTO 100
