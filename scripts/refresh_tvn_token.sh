#!/usr/bin/env bash
# Actualiza el playlist IPTV diariamente desde una máquina local (Mac o RPi).
# Corre localmente — NO en GitHub Actions (m3u.cl bloquea IPs de CI con 403).
#
# Setup (cron diario a las 06:00):
#   crontab -e
#   0 6 * * * /ruta/a/scripts/refresh_tvn_token.sh >> /tmp/refresh_tvn.log 2>&1

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLAYLIST="$REPO_DIR/output/playlist.m3u"
PYTHON="${PYTHON:-python3}"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Iniciando actualización IPTV..."

# Verificar si el token TVN actual todavía funciona
current_token=$(grep -o 'access_token=[^&[:space:]]*' "$PLAYLIST" | head -1 | sed 's/access_token=//' || echo "")
stream_id="57a498c4d7b86d600e5461cb"

if [[ -n "$current_token" ]]; then
    http_code=$($PYTHON -c "
import requests
r = requests.get(
    'https://mdstrm.com/live-stream-playlist/$stream_id.m3u8?access_token=$current_token',
    timeout=10, headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://live.tvn.cl'}
)
print(r.status_code)
" 2>/dev/null || echo "0")
    echo "[INFO] Token TVN actual: HTTP $http_code"
else
    http_code="0"
    echo "[WARN] No se encontró token TVN en playlist"
fi

cd "$REPO_DIR"
echo "[INFO] Regenerando playlist..."
$PYTHON scripts/update.py

git add output/playlist.m3u

if git diff --cached --quiet; then
    echo "[OK] Playlist sin cambios — no se requiere push"
    exit 0
fi

if [[ "$http_code" == "401" || "$http_code" == "0" ]]; then
    msg="chore: update TVN token [auto] — token expired"
else
    msg="chore: update IPTV playlist [auto]"
fi

git commit -m "$msg"
git push origin main
echo "[OK] Playlist publicado"
