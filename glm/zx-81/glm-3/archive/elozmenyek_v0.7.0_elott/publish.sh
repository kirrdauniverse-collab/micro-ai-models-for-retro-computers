#!/bin/bash
# Pico AI — GitHub-közzététel a te gépeden (kb. 30 másodperc)
#
# 1) A github.com/kirrdauniverse-collab fiókban hozz létre egy ÜRES,
#    PUBLIC repót "ZX81 AI micro language modell" néven (README nélkül!).
# 2) Futtasd ezt a szkriptet abban a könyvtárban, ahova a bundle-t másoltad:
#       bash publish.sh
# 3) Kéri a GitHub felhasználónevedet + jelszót/token-t, feltölt, kész.
set -e
BUNDLE="zx81-ai-micro-language-modell.bundle"
DIR="zx81-ai-micro-language-modell"
[ -f "$BUNDLE" ] || { echo "Nem talalom: $BUNDLE"; exit 1; }
git clone "$BUNDLE" "$DIR" -b main 2>/dev/null || git clone "$BUNDLE" "$DIR"
cd "$DIR"
git remote remove origin 2>/dev/null || true
git remote add origin "https://github.com/kirrdauniverse-collab/ZX81-AI-micro-language-modell.git"
git push -u origin main
echo "Kész: https://github.com/kirrdauniverse-collab/ZX81-AI-micro-language-modell"
