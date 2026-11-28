# Együttműködési szabályok más AI-modelleknek

Ez a könyvtár a PIOCO AI projekt külön ChatGPT-munkaterülete. A GLM és más modellek munkáját nem szabad felülírni vagy a gyökérben levő fejlesztési naplóból eltüntetni.

1. Minden munka előtt olvasd el a gyökér README.md, MASTERPROMPT.md, a fejlesztési napló utolsó bejegyzéseit és az érintett forrásokat.
2. Mindig a main ág legfrissebb állapotából indulj. Ellenőrizd a legutolsó commitot; ne építs elavult .P vagy .T81 fájlra.
3. A projektgazda nem programozó. Teljes, automatizáltan előállítható fájlokat és futtatható eredményt adj át, ne kézi összemásolási feladatokat.
4. A mesterpromptot és más modellek korábbi döntéseit ne írd át csendben. Minden új döntéshez dátum, indoklás, érintett fájlok és teszteredmény tartozzon.
5. Bináris kimenetet csak a saját generátorával állíts elő. Ne hex-editáld kézzel a .P, .T81, .blk, .bin fájlokat.
6. A D_FILE-t csak a karakterbiztonsági print-funnel írhatja. A 0x76 tiltása a display-file szerkezetére vonatkozik, nem általános RAM-adatra.
7. A 0x7E00–0x7EFF PERSIST-blokkot egyetlen nem profilblokk sem fedheti le. A 0x7F00–0x7FFF ROM-veremterületet soha ne használd.
8. A .P és .T81 formátumot soha ne nevezd egymás helyett. A v0.6 .P bootteszt nem multiload .T81 bizonyíték.
9. Válaszd külön a PC-s demonstrációt, a tényleges Z80-implementációt és az emulátoros végponttesztet. Csak arra mondd, hogy kész, amit ténylegesen teszteltél.
10. Minden változtatás után futtasd az érintett teszteket, és jegyezd fel a verziót, parancsot, emulátort és eredményt.

Első közös fejlesztési cél: a motor0.asm MWAIT ciklusának lecserélése megszakításbiztos ROM INPUT → tokenizálás → trigramgenerálás → print-funnel → history körre, golden tesztekkel.
