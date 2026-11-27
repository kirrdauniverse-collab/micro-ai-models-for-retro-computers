10 REM PICO AI DEMO CHAT V0.2
20 REM Simple knowledge demo
30 REM Full token model later

100 CLS
110 PRINT "    ****  PICO AI  ****"
120 PRINT "     DEMO CHAT MODE"
130 PRINT 
140 PRINT "This is a simple demo with"
150 PRINT "some built-in knowledge."
160 PRINT 
170 PRINT "Full token generation will"
180 PRINT "come in a later version."
190 PRINT 
200 PRINT "Press any key to start..."
210 PAUSE 4E4

300 CLS
310 PRINT "PICO: Hello. I am Pico AI."
320 PRINT "      Made by Safar Sandor"
330 PRINT "      with GLM help."
340 PRINT 
350 PRINT "I know a few things."
360 PRINT "Try asking:"
370 PRINT "  who are you"
380 PRINT "  who made you"
390 PRINT "  what is zx81"
400 PRINT "  hello"
410 PRINT 
420 PRINT "Or type BYE to quit."
430 PRINT 

500 PRINT "YOU: ";
510 INPUT A$

530 IF A$="BYE" OR A$="bye" THEN GOTO 900
540 IF A$="HELLO" OR A$="hello" OR A$="HI" OR A$="hi" THEN GOTO 600
550 IF A$="WHO ARE YOU" OR A$="who are you" THEN GOTO 650
560 IF A$="WHO MADE YOU" OR A$="who made you" THEN GOTO 700
570 IF A$="WHAT IS ZX81" OR A$="what is zx81" THEN GOTO 750
580 GOTO 800

600 PRINT 
610 PRINT "PICO: Hello. Nice to meet"
620 PRINT "      you. How can I help?"
630 PRINT 
640 GOTO 500

650 PRINT 
660 PRINT "PICO: I am Pico AI, a tiny"
670 PRINT "      language model that"
680 PRINT "      runs on the ZX81."
690 PRINT 
695 GOTO 500

700 PRINT 
710 PRINT "PICO: Made with GLM help by"
720 PRINT "      Safar Sandor."
730 PRINT "      Bus driver, writer and"
740 PRINT "      astronomer from Hungary."
745 PRINT 
746 GOTO 500

750 PRINT 
760 PRINT "PICO: The ZX81 is a classic"
770 PRINT "      British home computer"
780 PRINT "      from 1981 by Sinclair."
790 PRINT "      Only 16K RAM in many"
795 PRINT "      machines."
796 PRINT 
797 GOTO 500

800 PRINT 
810 PRINT "PICO: I do not know that yet."
820 PRINT "      My knowledge is still"
830 PRINT "      very small."
840 PRINT 
850 GOTO 500

900 PRINT 
910 PRINT "PICO: Goodbye. Load me again"
920 PRINT "      anytime."
930 PRINT 
940 STOP
