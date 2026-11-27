# Fázis 2 – Tokenizáló és generálási alapelvek

## Cél
Valódi (nem sablon-alapú) szöveggenerálás a ZX81 16 KB-os korlátai között.
A modell ne előre megírt mondatokat adjon vissza, hanem tokenekből építsen választ.

## Realista korlátok
- Vocab méret: **250–400 token** (cél: ~320)
- Minden token 1 bájtos ID (0–255, de 0x76 és veszélyes értékek kerülendők)
- Generálás sebessége: lassú (másodpercenként néhány token)
- Nincs valódi neurális háló – egyszerű statistikai modell kell

## Javasolt megoldás: Kis vocab + bigram / trigram modell

### 1. Tokenizálás
- Szavakra bontás (szóköz és írásjelek mentén)
- Kisbetűsítés
- Ismeretlen szó → speciális `<UNK>` token (és lehetőség szerint a kontextusból megjegyzi későbbre)
- Számok: külön tokenként vagy `<NUM>` + érték
- Gyakori rövidítések és emotikonok külön tokenek:
  - HAHA, WOW, NOOO, :), :(, :O, !!, ?? stb.

### 2. Szótár (Vocabulary)
Két irányú tábla a tudásblokkban:
- String → ID (kereséshez)
- ID → String (generáláshoz)

Tömörítés: a leggyakoribb szavak rövid ID-t kapnak.

Példa kategóriák a vocabban:
- Gyakori angol szavak (the, a, is, you, I, what, how...)
- Kérdőszavak
- Idő/dátum szavak
- Érzelmek / hangulat
- Speciális válaszok kulcsszavai (who, made, you, creator...)
- ZX81 / retro specifikus szavak
- Hangulatjelek és interjekciók

### 3. Generálási modell (egyszerű és működő)
**Bigram + kis trigram tábla** (helytakarékos):

- Minden tokenhez tároljuk a legvalószínűbb 4–8 következő tokent + súlyukat
- Hőmérséklet (Temperature 0–3):
  - 0 = mindig a legmagasabb súlyú
  - 1–2 = enyhe véletlenszerűség
  - 3 = erősebb véletlenszerűség
- Reasoning mód: hosszabb „gondolkodási” fázis (több belső lépés, lassabb, de kicsit jobb összefüggés)

Generálási folyamat:
1. Felhasználói input tokenizálása
2. Kontextus ablak (utolsó 6–12 token)
3. Következő token mintavételezése a táblából + hőmérséklet
4. Ismétlés amíg vége-jel vagy max hossz
5. Detokenizálás és kiírás

### 4. Speciális / hardcode-olt válaszok (helyspórolás)
Néhány gyakori kérdésre előre megírt, de tokenizált válasz:
- „Who made you?” / „Who created you?”
  → „Made with GLM help by Safar Sandor”
- „Who is Safar Sandor?”
  → „A bus driver, amateur writer and astronomer living in Hungary. Contact: SAFIZX810GMAIL.COM”
- Egyszerű szólások, üdvözlések

Ezek a tudásblokk elején külön szekcióban vannak, gyors kereséssel.

### 5. Elgépelés-tűrés
A tokenizáló fuzzy keresést is végezhet (1–2 karakteres eltérés), mert a teljes egyezés túl szigorú lenne.
Ismeretlen szó esetén:
- `<UNK>` token
- A modell a kontextusból próbál reagálni
- Opcionálisan megjegyzi a szót a session alatt (chat history-ban)

### 6. Múlt idő, többes szám, DO/DOES
Nem szabályalapú nyelvtan, hanem a training adatokban (bigram/trigram) megjelenő minták alapján.
A kis vocab miatt a leggyakoribb alakok (is/are, do/does, was/were, stb.) külön tokenekként szerepelnek.

### 7. Memóriaigény becslés
- Vocab stringek: ~1.2–1.8 KB
- ID ↔ string táblák: ~0.4 KB
- Bigram/trigram súlyok: ~3–5 KB
- Speciális válaszok: ~0.3–0.5 KB
- Összesen a modellrész: nagyjából belefér a 7.5–9 KB-os tudásblokkba

## Következő lépések
- Vocab első verziójának összeállítása (gyakori angol szavak + speciális tokenek)
- BASIC loader szövegeinek megírása
- Memóriatérkép finomítása a RAMTOP-hoz
