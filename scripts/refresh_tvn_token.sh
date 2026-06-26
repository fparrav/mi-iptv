#!/usr/bin/env bash
# Actualiza el playlist IPTV completo desde una máquina local (Mac o RPi).
# Corre localmente — NO en GitHub Actions (m3u.cl bloquea IPs de CI con 403).
#
# Para actualizar SOLO el token de TVN sin afectar otras fuentes, el
# workflow .github/workflows/update-tvn-token.yml corre cada 3 horas en GA.
#
# Setup (cron diario a las 06:00):
#   crontab -e
#   0 6 * * * /ruta/a/scripts/refresh_tvn_token.sh >> /tmp/refresh_tvn.log 2>&1

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="${PYTHON:-python3}"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Iniciando actualización IPTV..."

cd "$REPO_DIR"

# Regenerar playlist completo (incluye scraping de TVN via fetch_tvn_live)
echo "[INFO] Regenerando playlist (todas las fuentes)..."
$PYTHON scripts/update.py

git add output/playlist.m3u

if git diff --cached --quiet; then
    echo "[OK] Playlist sin cambios — no se requiere push"
    exit 0
fi

git commit -m "chore: update IPTV playlist [local]"
git push origin main
echo "[OK] Playlist publicado"
