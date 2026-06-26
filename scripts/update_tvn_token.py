#!/usr/bin/env python3
"""
Actualiza SOLO el token de TVN en output/playlist.m3u.

Lógica:
  1. Verifica si el token actual del playlist sigue funcionando (HTTP check).
  2. Si da 401/error: scrapea nuevo token de live.tvn.cl, valida y reemplaza.
  3. Si funciona (200): no modifica el archivo (exit 0, sin output).

Exit codes:
  0 — no se requieren cambios (token válido)
  1 — token actualizado (el llamador debe hacer git commit)
  2 — error irrecuperable
"""

import re
import sys
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
PLAYLIST = REPO_ROOT / "output" / "playlist.m3u"
STREAM_ID = "57a498c4d7b86d600e5461cb"
MDSTRM_BASE = f"https://mdstrm.com/live-stream-playlist/{STREAM_ID}.m3u8"
TVN_URL_RE = re.compile(
    rf"(https://mdstrm\.com/live-stream-playlist/{re.escape(STREAM_ID)}\.m3u8)"
    r"\?access_token=([A-Za-z0-9._-]+)"
)
TOKEN_RE = re.compile(r"[A-Za-z0-9._-]+")

HEADERS_SCRAPE = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
    "Referer": "https://www.tvn.cl/en-vivo",
    "Origin": "https://www.tvn.cl",
}
HEADERS_CHECK = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://live.tvn.cl",
}


def check_token(token: str) -> int:
    """Devuelve el HTTP status code al verificar el token en mdstrm."""
    try:
        r = requests.get(
            MDSTRM_BASE,
            params={"access_token": token},
            timeout=10,
            headers=HEADERS_CHECK,
        )
        return r.status_code
    except requests.RequestException:
        return 0


def scrape_token() -> str:
    """Scrapea el token actual desde live.tvn.cl."""
    resp = requests.get("https://live.tvn.cl", timeout=15, headers=HEADERS_SCRAPE)
    resp.raise_for_status()
    m = re.search(r"access_token:\s*'([A-Za-z0-9._-]+)'", resp.text)
    if not m:
        raise ValueError("access_token no encontrado en live.tvn.cl")
    return m.group(1)


def main() -> int:
    content = PLAYLIST.read_text()

    # Extraer token actual del playlist
    match = TVN_URL_RE.search(content)
    if not match:
        print("[WARN] URL de TVN no encontrada en playlist.m3u")
        return 2

    current_token = match.group(2)

    # Verificar si el token actual sigue siendo válido
    status = check_token(current_token)
    if status == 200:
        print(f"[OK] Token TVN válido (HTTP 200) — sin cambios")
        return 0

    print(f"[INFO] Token TVN: HTTP {status} — obteniendo token nuevo...")

    # Scrapear nuevo token
    try:
        new_token = scrape_token()
    except Exception as e:
        print(f"[ERROR] No se pudo obtener token de live.tvn.cl: {e}")
        return 2

    if new_token == current_token:
        print("[WARN] Nuevo token igual al actual — el stream puede estar caído")
        return 2

    # Verificar que el nuevo token funcione
    new_status = check_token(new_token)
    if new_status != 200:
        print(f"[ERROR] Nuevo token rechazado (HTTP {new_status})")
        return 2

    # Reemplazar solo la URL de TVN en el playlist
    new_url = f"{MDSTRM_BASE}?access_token={new_token}"
    new_content = TVN_URL_RE.sub(new_url, content)

    if new_content == content:
        print("[OK] Sin cambios tras reemplazo")
        return 0

    PLAYLIST.write_text(new_content)
    print(f"[UPDATED] Token TVN renovado — HTTP {status} → {new_status}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
