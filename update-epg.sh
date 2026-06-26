#!/bin/bash
set -e

cd "$(dirname "$0")"

EPG_DIR=".epg-tool"
EPG_CHANNELS="configs/epg-channels.xml"

if [ ! -d "$EPG_DIR" ]; then
    echo "Clonando iptv-org/epg..."
    git clone --depth 1 https://github.com/iptv-org/epg.git "$EPG_DIR" --quiet
fi

if [ ! -d "$EPG_DIR/node_modules" ]; then
    echo "Instalando dependencias (primera vez, ~30s)..."
    npm install --prefix "$EPG_DIR" --silent
fi

if [ ! -f "$EPG_CHANNELS" ]; then
    echo "ERROR: $EPG_CHANNELS no encontrado. Regenerar con scripts/generate-epg-channels.py"
    exit 1
fi

CHANNEL_COUNT=$(grep -c "<channel " "$EPG_CHANNELS" 2>/dev/null || echo 0)
echo "Generando guide.xml (~5-10 min)..."
echo "Canales: $CHANNEL_COUNT (desde $EPG_CHANNELS)"
cd "$EPG_DIR"
npm run grab -- \
    --channels="../$EPG_CHANNELS" \
    --output ../output/guide.xml \
    --maxConnections 8 \
    --days 2
cd ..

if [ ! -f output/guide.xml ]; then
    echo "ERROR: guide.xml no fue generado."
    exit 1
fi

GUIDE_CHANNELS=$(grep -c "<channel " output/guide.xml 2>/dev/null || echo 0)
echo "guide.xml generado: $GUIDE_CHANNELS canales."

if git diff --quiet output/guide.xml 2>/dev/null && git ls-files --error-unmatch output/guide.xml 2>/dev/null; then
    echo "Sin cambios en el EPG."
    exit 0
fi

git add output/guide.xml
git commit -m "chore: update IPTV EPG [local]"
# Pull --rebase antes del push para evitar race conditions cuando otro
# workflow (ej. update-tvn-token) hizo push mientras generábamos el EPG.
if ! git pull --rebase origin main; then
    git rebase --abort 2>/dev/null || true
    echo "ERROR: rebase falló — abortando sin push para evitar corrupción"
    exit 1
fi
git push origin main

echo ""
echo "EPG actualizado, commiteado y publicado."
echo "URL: https://fparrav.github.io/mi-iptv/output/guide.xml"
