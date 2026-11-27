# GROK döntések — a GLM fájljaihoz nem nyúl

Ez a fájl csak a GROK munkája. A `MASTERPROMPT.md`, a fázisdokumentumok, a napló, a `motor/`, az `eszkozok/`, a `kazetta/` és a `pioco-by-GLM-*.p` fájlok a GLM változatai; ide nem írunk.

Dátum: 2026-11-22.

## Görgetés

A projektgazda javítása: a beszélgetés görgetése **SHIFT+6 vissza**, **SHIFT+7 előre**. A SHIFT+5 nem görget. A GLM dokumentumaiban még a régi SHIFT+5/6 szerepel. A billentyűkezelés még nincs meg a motorban; amikor a GROK megírja, ezt a kiosztást használja.

## Nyelv

Az angol marad. A 0.1 nem válaszol magyarul. Így több szó és több token fér el.

## Nyelvtan (nincs ragozó)

- Megvan tokenként: `IS`, `ARE`, `DO`, `NOT`, `HAVE`, `HAS`.
- Még nincs, de kell: `DOES`, `DID`, `WAS`, `WERE`.
- Többes szám: külön `-S` token, nem számított alak.
- `DO NOT` két token. `DOES NOT` = `DOES` + `NOT`.

## Számok

A számjegysor szám, nem szó. Óra, dátum, év számjegy marad. A gyakori szám (`2`, `7`, `8`, `10`, `16`) egy token.

## Hangulat

Külön token, és hangulatbitet is állít: `HAHA`, `WOW`, `NOOO`, `:)`, `:(`, `:O`. A ZX81 csak nagybetű. A mosoly kettőspontból és zárójelből áll.

## Kész mondatok (nem generált)

- Másik nyelv: `I SPEAK ENGLISH ONLY.`
- Ki vagy: `I AM PIOCO. A TINY LANGUAGE MODEL ON A ZX81 WITH 16 KB.`
- Ki készített: `MADE WITH HELP FROM QWEN, BY SAFAR SANDOR.`
- Ki Sáfár Sándor: `SAFAR SANDOR IS A BUS DRIVER, AMATEUR WRITER AND ASTRONOMER. HE LIVES IN HUNGARY.`
- Közmondás: `ONE SWALLOW DOES NOT MAKE A SUMMER.`

## Állapot

A `pioco-by-GLM-0.2.p` a GLM fájlja. Elindul, képet ad, még nem beszélget. A GROK a következő saját szeletet `pioco-by-GROK-…` néven adja, és nem írja felül a GLM `.p` fájljait.
