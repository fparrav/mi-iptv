#!/bin/bash
set -e

cd "$(dirname "$0")"

echo "Actualizando playlist..."
python scripts/update.py

if git diff --quiet output/playlist.m3u; then
    echo "Sin cambios en el playlist."
    exit 0
fi

git add output/playlist.m3u
git commit -m "chore: update IPTV playlist [local]"

echo ""
echo "Playlist actualizado y commiteado."
echo "Para publicar: git push origin main"
