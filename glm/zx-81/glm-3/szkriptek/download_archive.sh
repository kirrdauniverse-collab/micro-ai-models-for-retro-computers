#!/bin/bash
# Google Drive archívum letöltése több fallback-módszerrel.
# A letöltött fájl egy saját, üres könyvtárba kerül (megbízhatatlan tartalom).
set -u
URLID="1VJ__-hK6WREt0nnexDYIwp4wKNUOSEeO"
DEST=/home/z/my-project/GLM/tmp/dl
mkdir -p "$DEST"
FILE="$DEST/archive.bin"
cd "$DEST"
rm -f "$FILE"

# 1) gdown
if command -v gdown >/dev/null 2>&1; then
  if gdown --fuzzy "https://drive.google.com/file/d/$URLID/view" -O "$FILE" >/dev/null 2>&1; then
    echo "GDOWN_OK $(stat -c%s "$FILE")"; exit 0
  fi
else
  pip install -q gdown >/dev/null 2>&1
  if command -v gdown >/dev/null 2>&1 && gdown --fuzzy "https://drive.google.com/file/d/$URLID/view" -O "$FILE" >/dev/null 2>&1; then
    echo "GDOWN_OK $(stat -c%s "$FILE")"; exit 0
  fi
fi

# 2) curl direct
curl -sL "https://drive.google.com/uc?export=download&id=$URLID" -o "$FILE"
SIZE=$(stat -c%s "$FILE" 2>/dev/null || echo 0)
echo "curl1 size: $SIZE"
if [ "$SIZE" -gt 10000 ]; then
  file "$FILE"; echo "CURL_OK"; exit 0
fi

# 3) curl confirm-token (nagy fájlok / víruskereső-átirányítás)
CONFIRM=$(grep -o 'confirm=[^&"]*' "$FILE" 2>/dev/null | head -1 | cut -d= -f2)
UUID=$(grep -o 'name="uuid" value="[^"]*"' "$FILE" 2>/dev/null | head -1 | sed 's/.*value="//;s/"//')
if [ -n "$CONFIRM" ]; then
  curl -sL "https://drive.google.com/uc?export=download&id=$URLID&confirm=$CONFIRM" -o "$FILE"
  SIZE=$(stat -c%s "$FILE" 2>/dev/null || echo 0)
  echo "curl2 size: $SIZE"
  if [ "$SIZE" -gt 10000 ]; then file "$FILE"; echo "CONFIRM_OK"; exit 0; fi
fi

echo "ALL_FAILED"
head -c 400 "$FILE" 2>/dev/null || true
exit 1
