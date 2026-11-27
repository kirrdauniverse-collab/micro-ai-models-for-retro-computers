10 REM PICO AI LOADER V0.2
20 REM Collects name, gender, date, time
30 REM Then sets RAMTOP and NEW

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
200 PRINT "Press any key..."
210 PAUSE 4E4

300 CLS
310 PRINT "PERSONAL DATA"
320 PRINT 
330 PRINT "I need a few things to"
340 PRINT "remember you."
350 PRINT 

360 PRINT "Your name (max 12 chars)?"
370 INPUT N$
380 IF LEN N$>12 THEN LET N$=N$( TO 12)

390 PRINT 
400 PRINT "Gender (M/F)?"
410 INPUT G$
420 LET G$=G$(1)
430 IF G$<>"M" AND G$<>"F" AND G$<>"m" AND G$<>"f" THEN GOTO 400
440 IF G$="m" THEN LET G$="M"
450 IF G$="f" THEN LET G$="F"

460 PRINT 
470 PRINT "Today date (DD/MM/YYYY)?"
480 INPUT D$
490 IF LEN D$<8 THEN GOTO 470

500 PRINT 
510 PRINT "Current time (HH:MM)?"
520 INPUT T$
530 IF LEN T$<4 THEN GOTO 510

600 CLS
610 PRINT "CONFIRM"
620 PRINT 
630 PRINT "Name: ";N$
640 PRINT "Gender: ";G$
650 PRINT "Date: ";D$
660 PRINT "Time: ";T$
670 PRINT 
680 PRINT "Is this correct (Y/N)?"
690 INPUT C$
700 IF C$="N" OR C$="n" THEN GOTO 300

800 CLS
810 PRINT "HOW THE LOADER WORKS"
820 PRINT 
830 PRINT "1. I will set RAMTOP so the"
840 PRINT "   upper memory is protected."
850 PRINT 
860 PRINT "2. Then I do NEW."
870 PRINT 
880 PRINT "3. After that you must type:"
890 PRINT "   LOAD """""
900 PRINT "   and start the tape again."
910 PRINT 
920 PRINT "Your personal data will be"
930 PRINT "saved by the next block."
940 PRINT 
950 PRINT "Press ENTER to continue..."
960 INPUT A$

1000 REM Set RAMTOP to 30000
1010 POKE 16388,48
1020 POKE 16389,117

1030 PRINT 
1040 PRINT "RAMTOP set to 30000."
1050 PRINT "Doing NEW now..."
1060 PAUSE 150
1070 NEW

1080 STOP
