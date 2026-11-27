# Error and Repair Log – grok-1

## Ismert / javított problémák

### 2026-11-25/26
- Felhasználói szöveg nem jelent meg a chatben → javítva (PRINT "YOU: ";A$)
- Képernyő túlcsordulás → rövidebb válaszok
- Többbetűs string változók (USER$, LEARN$) → v0.6-ban egybetűsre cserélve (U$, L$)
- Kettőspontos többparancsos sorok → v0.6-ban megszüntetve (egy stmt / sor)
- Loader input túl szigorú volt → elnézőbbé téve

### Jelenlegi nyitott
- A v0.6 még mindig keyword-alapú, nem valódi token generálás
- Topic váltás még manuális LOAD ""-vel történik
- Nincs valódi persistent mentés a RAMTOP felett
