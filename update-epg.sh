#!/bin/bash
set -e

cd "$(dirname "$0")"

EPG_DIR=".epg-tool"
EPG_SITES="directv.com.ar,movistarplus.es,tv.movistar.co,tv.movistar.com.pe,anteltv.com.uy,cableplus.com.uy,energeek.cl,siba.com.co,reportv.com.ar,nuevosiglo.com.uy"

if [ ! -d "$EPG_DIR" ]; then
    echo "Clonando iptv-org/epg..."
    git clone --depth 1 https://github.com/iptv-org/epg.git "$EPG_DIR" --quiet
fi

if [ ! -d "$EPG_DIR/node_modules" ]; then
    echo "Instalando dependencias (primera vez, ~30s)..."
    npm install --prefix "$EPG_DIR" --silent
fi

echo "Generando guide.xml (~10-20 min)..."
echo "Sitios: $EPG_SITES"
cd "$EPG_DIR"
npm run grab -- \
    --sites="$EPG_SITES" \
    --lang es \
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
git push origin main

echo ""
echo "EPG actualizado, commiteado y publicado."
echo "URL: https://fparrav.github.io/mi-iptv/output/guide.xml"
