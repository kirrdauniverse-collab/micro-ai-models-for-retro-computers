# Z80 Bigram Engine – First Implementation

## Files
- `src/engine/bigram.asm` – core GENERATE + GET_NEXT_TOKEN + simple RNG
- `src/engine/vocab_and_bigrams.asm` – 31 token vocab + bigram table

## Design (realistic for 16K)
- Vocab size: 32 tokens (easy to expand later to 64–96)
- Bigram entry: 13 bytes (count + 6 next IDs + 6 weights)
- Table size: ~416 bytes
- Temperature: 0 = always highest weight, >0 = random among possibles
- No floating point, pure integer
- Output: list of token IDs (0-terminated)

## How it works
1. Start with a seed token (or 0)
2. Look up current token in BIGRAM_TABLE
3. According to temperature pick next token ID
4. Append to output buffer
5. Repeat until max length or no more next tokens

## Next steps to make it usable
1. Fix/complete the GENERATE loop (current version has a small logic note)
2. Add DETOKENIZE routine (token ID → string using VOCAB_TABLE)
3. Simple tokenizer (input string → first matching token ID)
4. Integrate into a CODE block that can be called with USR from BASIC or run standalone
5. Put the tables into the protected memory area after RAMTOP

## Size estimate
- Code: ~300–400 bytes
- Vocab + bigrams: ~500–600 bytes
- Still lots of room for larger vocab and better sampling later

This is the first real step away from pure BASIC hardcoded answers.
