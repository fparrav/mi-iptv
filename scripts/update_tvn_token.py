#!/usr/bin/env python3
"""
Actualiza SOLO el token de TVN en output/playlist.m3u.

Modos de operación:
  --verify (default, para uso local):
    1. Verifica el token actual en mdstrm.com.
    2. Si da 200: sin cambios (exit 0).
    3. Si da 401/error: scrapea nuevo token, verifica, reemplaza.

  --no-verify (para GitHub Actions, donde mdstrm.com da 403 por IP):
    1. Scrapea token de live.tvn.cl.
    2. Si es diferente al del playlist: reemplaza (exit 1).
    3. Si es igual: sin cambios (exit 0).
    El token de live.tvn.cl se asume válido por origen.

Exit codes:
  0 — no se requieren cambios
  1 — token actualizado (el llamador debe hacer git commit)
  2 — error irrecuperable
"""

import argparse
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
    resp = requests.get("https://live.tvn.cl", timeout=15, headers=HEADERS_SCRAPE)
    resp.raise_for_status()
    m = re.search(r"access_token:\s*'([A-Za-z0-9._-]+)'", resp.text)
    if not m:
        raise ValueError("access_token no encontrado en live.tvn.cl")
    return m.group(1)


def apply_token(content: str, new_token: str) -> str:
    return TVN_URL_RE.sub(f"{MDSTRM_BASE}?access_token={new_token}", content)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--no-verify",
        action="store_true",
        help="No verifica el token en mdstrm.com (para GitHub Actions donde da 403)",
    )
    args = parser.parse_args()

    content = PLAYLIST.read_text()

    match = TVN_URL_RE.search(content)
    if not match:
        print("[WARN] URL de TVN no encontrada en playlist.m3u")
        return 2

    current_token = match.group(2)

    if args.no_verify:
        # Modo GA: scrapear y actualizar si el token cambió
        try:
            new_token = scrape_token()
        except Exception as e:
            print(f"[ERROR] No se pudo obtener token de live.tvn.cl: {e}")
            return 2

        if new_token == current_token:
            print("[OK] Token sin cambios — sin actualización necesaria")
            return 0

        new_content = apply_token(content, new_token)
        PLAYLIST.write_text(new_content)
        print(f"[UPDATED] Token TVN renovado (modo --no-verify)")
        return 1

    else:
        # Modo local: verificar el token actual primero
        status = check_token(current_token)
        if status == 200:
            print("[OK] Token TVN válido (HTTP 200) — sin cambios")
            return 0

        print(f"[INFO] Token TVN: HTTP {status} — obteniendo token nuevo...")

        try:
            new_token = scrape_token()
        except Exception as e:
            print(f"[ERROR] No se pudo obtener token de live.tvn.cl: {e}")
            return 2

        if new_token == current_token:
            print("[WARN] Nuevo token igual al actual — el stream puede estar caído")
            return 2

        new_status = check_token(new_token)
        if new_status != 200:
            print(f"[ERROR] Nuevo token rechazado (HTTP {new_status})")
            return 2

        new_content = apply_token(content, new_token)
        if new_content == content:
            print("[OK] Sin cambios tras reemplazo")
            return 0

        PLAYLIST.write_text(new_content)
        print(f"[UPDATED] Token TVN renovado — HTTP {status} → {new_status}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
