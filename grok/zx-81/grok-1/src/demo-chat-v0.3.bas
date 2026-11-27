10 REM PICO AI DEMO CHAT V0.3
20 REM Shows user text + better screen
30 REM More knowledge + help

100 CLS
110 PRINT "    ****  PICO AI  ****"
120 PRINT "     DEMO CHAT V0.3"
130 PRINT 
140 PRINT "Simple knowledge demo."
150 PRINT "Real token model coming."
160 PRINT 
170 PRINT "Commands: HELP  BYE"
180 PRINT 
190 PRINT "Press any key..."
200 PAUSE 4E4

300 CLS
310 PRINT "PICO: Hello. I am Pico AI."
320 PRINT "Made by Safar Sandor with"
330 PRINT "GLM help."
340 PRINT 
350 PRINT "Ask me things or type HELP"
360 PRINT 

500 PRINT "----------------"
510 PRINT "YOU: ";
520 INPUT A$
530 PRINT "YOU: ";A$
540 PRINT 

550 IF A$="BYE" OR A$="bye" THEN GOTO 900
560 IF A$="HELP" OR A$="help" THEN GOTO 850
570 IF A$="HELLO" OR A$="hello" OR A$="HI" OR A$="hi" THEN GOTO 600
580 IF A$="WHO ARE YOU" OR A$="who are you" THEN GOTO 650
590 IF A$="WHO MADE YOU" OR A$="who made you" THEN GOTO 700
595 IF A$="WHAT IS ZX81" OR A$="what is zx81" THEN GOTO 750
596 IF A$="WHAT CAN YOU DO" OR A$="what can you do" THEN GOTO 800
597 GOTO 820

600 PRINT "PICO: Hello. Nice to talk."
610 PRINT 
620 GOTO 500

650 PRINT "PICO: I am Pico AI, a tiny"
660 PRINT "language model for the ZX81."
670 PRINT 
680 GOTO 500

700 PRINT "PICO: Made with GLM help by"
710 PRINT "Safar Sandor from Hungary."
720 PRINT "Bus driver, writer,"
730 PRINT "astronomer."
740 PRINT 
745 GOTO 500

750 PRINT "PICO: ZX81 is a 1981 British"
760 PRINT "home computer by Sinclair."
770 PRINT "Many had only 16K RAM."
780 PRINT 
790 GOTO 500

800 PRINT "PICO: I can answer simple"
810 PRINT "questions. Full AI later."
815 PRINT 
816 GOTO 500

820 PRINT "PICO: I do not know that."
830 PRINT "My knowledge is small."
840 PRINT 
845 GOTO 500

850 PRINT "PICO: Try these:"
860 PRINT "  hello"
870 PRINT "  who are you"
880 PRINT "  who made you"
890 PRINT "  what is zx81"
895 PRINT "  what can you do"
896 PRINT "  BYE"
897 PRINT 
898 GOTO 500

900 PRINT "PICO: Goodbye!"
910 PRINT 
920 STOP
