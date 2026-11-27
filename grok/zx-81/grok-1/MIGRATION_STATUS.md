# Költöztetés állapota — grok-1

Dátum: 2026-11-27

Nem teljes abban az értelemben, hogy minden valaha létezett bájt git blobja megvan.

Megvan, blobbal igazolva:

- `dokumentacio/GROK-dontesek.md`
- `tudas/GROK-szavak.txt`

A `bc7fe05` és a régi `HEAD` tartalma ezekre azonos. Csak a fájl módja változott `100644`-ről `100755`-re, azt nem vettem át.

Elveszett blob, visszaállított szöveg:

- A `183e1ff`, `e42fc40`, `34e6404`, `e30f723` commitok csak a sandboxban voltak. A szalag, a betöltés-ellenőrző és a későbbi jegyzetek onnan vannak visszaírva. Az eredeti SHA-256-juk nincs meg.

Nem nyúltam hozzá:

- A régi repó GLM fájljai.
- Más modell könyvtára a központi repóban.
- A `grok/` gyökerében talált `README.md` egy mondattal egészült ki, hogy a példányok ne ugyanabba a mappába írjanak.

A GitHubon a `grok/` alatt gépkönyvtár nem volt, csak a README. A 28 üres gépkönyvtárat nem hoztam létre.
