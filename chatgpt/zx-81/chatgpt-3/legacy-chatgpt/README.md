# CHATGPT — közös fejlesztői munkaterület

Ez a könyvtár a PIOCO AI projekthez készült ChatGPT-oldali fejlesztési, ellenőrzési és átadási anyagokat tartalmazza. Más modellek is dolgozhatnak benne; minden érdemi módosítást dátummal és mérhető teszteredménnyel kell dokumentálni.

## Projekt

- Gazda: \`kirrdauniverse-collab\`
- Alap-repó: \`PIOCO-AI-miniature-language-modell\`
- Platform: Sinclair ZX81, 16 KB RAM, Z80
- Első modellnyelv: angol, nagybetűs karakterkészlet
- Kiadási cél: egyetlen többblokkos \`.T81\` kazettaállomány
- Jelenleg ellenőrzött kiadás: \`pioco-0.6.p\` — stabil boot és splash, nem kész beszélgető AI

A kért külön „ZX81 AI micro language modell” nevű GitHub-repót ebben a munkamenetben nem lehetett létrehozni: a csatlakoztatott GitHub-műveletek nem kínálnak repository-létrehozást. A meglévő, közvetlenül ide tartozó PIOCO-repóban ezért létrehoztam ezt a külön \`CHATGPT/\` könyvtárat. A gyökérben levő GLM/korábbi munkákat nem írom felül.

## A könyvtár tartalma

- \`MUSZAKI_AUDIT_2026-11-22.md\` — forráskód- és státuszaudit.
- \`FEJLESZTESI_UTITERV.md\` — végrehajtható fejlesztési sorrend és verziókapuk.
- \`ATVETELI_TESZTEK.md\` — követelményenkénti ellenőrzőlista.
- \`MODELLEKNEK.md\` — együttműködési szabályok több AI-modell számára.
- \`host_reference_chat.py\` — PC-n futó trigram-referencia a projekt jelenlegi bináris szótárához.

## Host referencia futtatása

A repó gyökeréből, Python 3-mal:

    python CHATGPT/host_reference_chat.py --self-test
    python CHATGPT/host_reference_chat.py
    python CHATGPT/host_reference_chat.py --prompt "WHO MADE YOU ?" --temperature 1

A host referencia a \`kazetta/adat/szotar.bin\` fájlt olvassa. Nem ZX81-es végrehajtható program, nem Z80-port, és nem készít \`.P\` vagy \`.T81\` fájlt. A statisztikai generátor viselkedésének PC-s vizsgálatára és a későbbi Z80-változattal való összehasonlításra szolgál.

## Fontos: mit jelent a „valódi generálás”?

A 16 KB-os ZX81-en mai, több millió paraméteres LLM nem fér el. A megvalósítható cél egy kicsi, statisztikai nyelvi modell: tokenizálás, kontextusfüggő trigram-választás, korlátozott hőmérséklet, egyszerű morfológia és állapotmemória. Ez új token-sorozatokat tud előállítani, de nem rendelkezik mai LLM-szintű világmodellel.

A 2026-11-22-i \`motor/motor0.asm\` még a \`MWAIT\` várakozó ciklusban áll. A teljes ROM INPUT → tokenizálás → válaszgenerálás → chat history ciklus még fejlesztendő. Ezt a státuszt minden modellnek és kiadásnak őszintén jeleznie kell.
