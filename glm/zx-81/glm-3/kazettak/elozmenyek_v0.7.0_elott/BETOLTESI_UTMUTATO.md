# PICO AI kazetta — betöltési útmutató (2026-11-23., 4. menet)

## A mostani javítás
A korábbi fájl két szerkezeti hibája miatt az emulátor **elutasította**
a szalagot:
1. Hiányzott a fájl elejéről a kötelező **„EO81" mágia** (az EightyOne
   forrása szerint nélküle a .T81 betöltése elutasítva).
2. A motoros blokkok utolsó bájtja nem 0x80 volt — az emulátor a blokk
   végét az első 0x80-as bájtig vágja vissza, vagyis a blokkok végéből
   több száz bájt levágott volna.

Mindkettő javítva; az új **ZX81PICO.T81** (39 009 bájt, 4 blokk)
a hivatalos formátumszabályok szerint validálva.

## Betöltés (EightyOne emulátorban)
1. A kazetta beszúrása szalagként (Media/Tape → Insert — ugyanúgy,
   ahogy a régi v0.5.4 kazettákkal tetted).
2. A gépnek add ki: **LOAD "PICOBOOT"** — és nem LOAD ""!
   (A ZX81en a LOAD "" nem azonos a Spectruméval: a név-illesztés
   konvenciója miatt a blokk nevét ki kell írni.)
3. A boot-blokk betöltése után a képernyőn a boot üzeneteknek
   kellene megjelenniük.

## Őszinte kockázati jelzés
A fájlFORMÁTUM most már szabályos — de a boot-blokk BASIC-sorai
(PRINT/INPUT sorok) még a régi, kísérleti felépítésűek. Ha a betöltés
sikerül, de a gép a futásnál resetel/megáll, az már ezért van: a
következő munkamenet a régi, bizonyított v0.5.4-mintára (gépi kódú
boot + „IF USR 16514=1 THEN LOAD" láncolás) írja át őket. A
fájlstruktúra-ellenőrzés most ezt a lépést előzi meg — a kazetta
betölthetőségét most tudtuk biztosítani.
