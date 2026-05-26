#!/bin/bash
set -e

cd "$(dirname "$0")"

EPG_DIR=".epg-tool"
EPG_SITES="directv.com.ar,movistarplus.es,tv.movistar.co,tv.movistar.com.pe,anteltv.com.uy,cableplus.com.uy,energeek.cl,siba.com.co,reportv.com.ar,nuevosiglo.com.uy"

# --- Playlist ---
echo "Actualizando playlist..."
python scripts/update.py

# --- EPG ---
echo ""
echo "Actualizando EPG..."

if [ ! -d "$EPG_DIR" ]; then
    echo "  Clonando iptv-org/epg..."
    git clone --depth 1 https://github.com/iptv-org/epg.git "$EPG_DIR" --quiet
fi

if [ ! -d "$EPG_DIR/node_modules" ]; then
    echo "  Instalando dependencias (primera vez)..."
    npm install --prefix "$EPG_DIR" --quiet
fi

echo "  Generando guide.xml (sitios: $EPG_SITES)..."
cd "$EPG_DIR"
node -e "
const { execSync } = require('child_process');
" 2>/dev/null || true
npm run grab -- --sites="$EPG_SITES" --lang es --output ../output/guide.xml --maxConnections 4 2>&1 | grep -E "^\[|error|Error|warn|✓|✗" || true
cd ..

# --- Commit ---
echo ""
CHANGED=false

if ! git diff --quiet output/playlist.m3u; then
    git add output/playlist.m3u
    CHANGED=true
fi

if [ -f output/guide.xml ] && ! git diff --quiet output/guide.xml 2>/dev/null; then
    git add output/guide.xml
    CHANGED=true
elif [ -f output/guide.xml ] && ! git ls-files --error-unmatch output/guide.xml 2>/dev/null; then
    git add output/guide.xml
    CHANGED=true
fi

if [ "$CHANGED" = "false" ]; then
    echo "Sin cambios en playlist ni EPG."
    exit 0
fi

git commit -m "chore: update IPTV playlist and EPG [local]"
git push origin main

echo ""
echo "Playlist y EPG actualizados, commiteados y publicados."
