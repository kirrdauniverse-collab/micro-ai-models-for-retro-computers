# Fázis 2 – Képernyő elrendezés és UI elválasztás

## Alapelvek (ZX81 korlátok)
- 32 karakter széles, 24 soros képernyő (D_FILE)
- Inverz karakterek (bit 7 beállítva) = fehér alapon fekete / kiemelt
- Nincs színes, nincs vastag/vékony betű, nincs keret karakterkészlet a ROM-ban (csak a saját grafikus karakterek)
- Tilos: 0x76 (NEWLINE) és parancskódok a képernyőmemóriában közvetlenül
- Cél: jól elkülönülő feliratok, menük, chat üzenetek, státuszsávok

## Elválasztási módszerek
1. **Inverz fejlécsorok** – minden fontos szekció elején (legfontosabb és legtisztább)
2. **Üres sor + inverz elválasztó** (pl. teljes szélességű inverz szóközök vagy grafikus karakterek)
3. **Prefix karakterek** a chat üzeneteknél (pl. `>` felhasználó, `<` modell, vagy inverz kezdőbetű)
4. **Státuszsáv** mindig ugyanott (alsó 1–2 sor)

## Javasolt képernyő-struktúra (chat mód)

```
[INVERZ] PICO AI  T:2  R:ON  14:32  TOK:042   ← fejléc / státusz
------------------------------------------------ ← elválasztó (üres vagy grafikus)
[INVERZ] YOU  14:31  TOK:008                  ← felhasználó fejléc
Hello, how are you today?
                                                  ← üres sor
[INVERZ] PICO  14:32  TOK:035  1.2s           ← modell fejléc
I am running well. What would
you like to talk about?
                                                  ← üres sor
> _                                           ← input sor (ROM INPUT)
```

## Boot / Splash képernyő
- Felső rész: nagy inverz cím vagy egyszerű ASCII art (PICO AI)
- Középen: üdvözlő szöveg + rövid leírás
- Alsó rész: menü / kérdés (pl. "Show help? Y/N")
- Minden menüpont inverz kiemeléssel vagy számozott + inverz kijelölés

## Menürendszer
- Főmenü és almenük: inverz fejléc + számozott opciók
- Kiválasztott elem: inverz teljes sor
- Vissza / Mégse mindig jól látható helyen

## Chat history megjelenítés
- Minden üzenet saját inverz fejlécsorral (WHO + időbélyeg + tokenek + válaszidő)
- Üzenetek között legalább 1 üres sor
- Ha a history túl hosszú, a legrégebbi üzenetek kicsúsznak felül (körkörös buffer + görgetés SHIFT+5/6)

## Státusz / Thinking sáv
- Generálás közben a fejléc vagy egy külön sor mutatja: `[INVERZ] THINKING...` vagy animált pontok (ha megoldható)
- Temperature és Reasoning állapot mindig látható a fő fejlécben

## Bitmezők és tartós adatok (előzetes)
A felhasználói adatok (név, nem, születés, dátum/óra) a tartós memóriában bitmezőkkel és rövid stringekkel tárolódnak, a későbbi betöltések nem írják felül.

## Következő
- Részletes memóriatérkép (címekkel)
- Tokenizáló alapstruktúra
- .T81 sávok pontos leírása
