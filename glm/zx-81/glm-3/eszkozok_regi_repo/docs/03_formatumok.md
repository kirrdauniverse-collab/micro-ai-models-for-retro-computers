# 03 — Fájlformátumok

## 1. EO81 / .T81 konténer

```
offs  méret  mező
0     4      mágia: "EO81"
4/…   32     blokknév, ASCII, 0-ra töltve
+32   16     blokkhossz ASCII tizedes számjegyekként, 0-ra töltve
+48   N      blokkadat = teljes .P kép bájtonként (a memória 0x4009-től)
```

Egy `.P` fájl = ugyanez az adat konténer nélkül (a gyorsbetöltőkhöz).
A kép felépítése (appmake-konvenció, a ROM LOAD által alkalmazva):

```
0x4009-től: rendszer-változók 116 B
0x407D-től: 1 REM <kód> sor; 2 IF USR… LOAD; 3 IF USR… SAVE sorok;
            minden sor: [cimszám u16 BE][hossz u16 LE][törzs][0x76]
            a szám-litereket 0x7E + 5 bájtos ZX lebegőpontos érték követi
            (a ROM S-STK-DEC futásidejű szkennerének követelménye)
számok után: a motor adatai a kép végéig
SHORT kép:   a 0x7120 alatti zónáig ér véget (nincs D_FILE a fájlban,
             de a rendszer-változóinak D_FILE/VARS mutatói a betöltés
             UTÁNI állapotra mutatnak — a D_FILE a memóriában marad)
FULL kép:    0-ra töltés 0x7B00-ig, majd D_FILE (793 B) + VARS 0x80 jelző
```

A rendszer-változó blokk tartalma (a hármasan ellenőrzött konvenció):
E_PPC=1 (LE), D_FILE=0x7B00, DF_CC=D_FILE+1, VARS=0x7E19, E_LINE=0x7E1A,
CH_ADD=E_LINE+4, STKBOT=STKEND=E_LINE+5, MEM=0x405D, DF_SZ=2,
0x4026 szó = 0x7FFD (gyorsbetöltő SP-forrás), 0x4029 szó = D_FILE-másolat.

## 2. PK01 tudáscsomag (a motor tudásbázisa)

```
offs  mező
0     "PK01" mágia
4     u8  formátum-verzió (1)
5     u8  charset (0 = angol 26+10; 1 = fenntartva magyarnak)
6     u8  szótár-méret (a csomag szavait nem tartalmazza: a szótár a
         motor képében él; ez a szám a konzisztencia-ellenőrzéshez)
7     u8  fogalomszám N (max 48)
8     u16 bigram-bejegyzésszám M (max 900)
10    u16 rögzített-szöveg terület hossza
12    fogalomtábla: N × { u8 token; u8 osztálybitek;
        u8[6] társított tokenek (0 = üres) }            → N × 8 B
12+N*8 bigram-tábla: M × { u8 előző; u8 következő; u8 súly 1..8 }
        ( rendezve előző-token szerint; a súly a mintavétel
          relatív valószínűsége — a tréner a korpusz gyakoriságából
          kalibrálja )
+M*3   mondattervek: P × { u8 típus; u8[6] token-utvonal foltokkal }
        típusok: SVO, visszakérdezés, hangulat, tény
+…     hangulat- és trágárság-válasz-készletek (token-sorozatok)
+…     rögzített szövegek (identitás, e-mail, közmondás, súgó):
        hossz-bájt + ZX-karakterláncok (D_FILE-biztos kódok)
+…     szám→szöveg táblák (0..20, tízesek)
vége:  u8 XOR-ellenőrző-összeg
```

Minden tömörített szöveg = szótár-tokenek bájtjai; a szótáron kívüli szó
3 bájtos literál-escape-et kap (`0xFF, hossz, betűk`). Így a tipikus angol
mondat 1 bájt/szó — a tréner kiírja a bájtszámot és az arányt.

## 3. Csomagolt tartós állapot (D_FILE 0–2. sor, 6 bit/cella)

A 3 bájt → 4 cella csomagolás miatt a cellák mindig 0x00–0x3F — a D_FILE
sosem kaphat tiltott kódot a tárolásból. 72 bájt hasznos teher:

```
bájt  mező
0–2   "PK1" mágia
3     verzió
4–11  felhasználónév (max 8, 0-ra töltve)
12    bitmező (nem, gyerek-e, … — lásd 02/4. fejezet)
13    születési év − 1900
14–15 profil-nap (2000-01-01 óta; u16)
16–17 profil-óra/perc
18    hőmérséklet (1..4)
19    gondolkodás be/ki
20    téma-azonosító
21    pending-akció (0=nincs, 1=LOAD, 2=SAVE)
22–23 óra-állás a mentéskor (FRAMES-ből származtatva)
24–31 legutóbbi emlékesemény-index
32–63 emlékesemények: 8 × 2 B [bit-index | nap a profilhoz]
64–70 chat-gyűrő mutatók
71    XOR-ellenőrző-összeg
```

## 4. Tanult-zóna (0x7160–0x73E0, nem része a rövid képeknek)

```
0     "TL1" mágia, 1 verzió
2     darabszám (max 32)
3…    bejegyzés: 7 betű (0-ra töltve) + u8 előző-token +
      u8 találat-számláló (a generátor gyakrabban használja, ha a
      felhasználó többször mondta) + u2 foglalva
…     emlékbit-tükör és téma-állapot (a D_FILE-állapot biztonsági másolata)
```

## 5. A motor bináris és a BASIC-keret

Az assembler kimenete (`engine/build/engine.bin`) org=0x4082-től fut. A
`build_t81.py` ezt ágyazza be:

```
1 REM <engine.bin> <64 B tartós farok>
2 IF USR 16514 = 1 THEN LOAD "PICOBASE"
3 IF USR 16514 = 2 THEN SAVE "PICOBASE"
```

A 2-es sor névmezője (8 display-kód) a téma-váltás írási célja. A
tartós farok a legkisebb tartós réteg: `PF1` mágia + a D_FILE-állapot
kivonata + névtábla-index — ha a D_FILE sérülne, ebből áll helyre.
