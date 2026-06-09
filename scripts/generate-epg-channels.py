#!/usr/bin/env python3
"""
Genera configs/epg-channels.xml con solo los canales de output/playlist.m3u
que tienen cobertura en los sites del iptv-org/epg grabber.

Ejecutar después de actualizar la playlist para mantener sincronizado el EPG.
"""
import re
import os
import defusedxml.ElementTree as ET
from collections import defaultdict

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLAYLIST = os.path.join(REPO_ROOT, "output", "playlist.m3u")
SITES_DIR = os.path.join(REPO_ROOT, ".epg-tool", "sites")
OUTPUT = os.path.join(REPO_ROOT, "configs", "epg-channels.xml")

# Sites ordenados por cobertura de nuestra playlist (gatotv.com primero = 116 canales)
TARGET_SITES = [
    "gatotv.com",
    "siba.com.co",
    "reportv.com.ar",
    "tv.movistar.com.pe",
    "directv.com.uy",
    "cableplus.com.uy",
    "tvcubana.icrt.cu",
    "distro.tv",
    "tvtv.us",
]


def main():
    if not os.path.exists(PLAYLIST):
        print(f"ERROR: {PLAYLIST} no encontrado. Ejecutar update.py primero.")
        return 1

    if not os.path.exists(SITES_DIR):
        print(f"ERROR: {SITES_DIR} no encontrado. Ejecutar update-epg.sh primero (clona el repo).")
        return 1

    with open(PLAYLIST) as f:
        content = f.read()
    playlist_ids = {i.strip() for i in re.findall(r'tvg-id="([^"]+)"', content) if i.strip()}
    print(f"tvg-ids en playlist: {len(playlist_ids)}")

    channels_by_xmltv = {}
    for site in TARGET_SITES:
        xml_path = os.path.join(SITES_DIR, site, f"{site}.channels.xml")
        if not os.path.exists(xml_path):
            print(f"  SKIP (no existe): {site}")
            continue
        try:
            tree = ET.parse(xml_path)
            for ch in tree.getroot().findall("channel"):
                xmltv_id = ch.get("xmltv_id", "").strip()
                if xmltv_id and xmltv_id in playlist_ids and xmltv_id not in channels_by_xmltv:
                    channels_by_xmltv[xmltv_id] = {
                        "site": site,
                        "site_id": ch.get("site_id", ""),
                        "lang": ch.get("lang", "es"),
                        "xmltv_id": xmltv_id,
                        "name": ch.text or "",
                    }
        except Exception as e:
            print(f"  ERROR {site}: {e}")

    lines = ['<?xml version="1.0" encoding="UTF-8"?>', "<channels>"]
    for xmltv_id, e in sorted(channels_by_xmltv.items()):
        site_id = e["site_id"].replace("&", "&amp;").replace('"', "&quot;")
        name = e["name"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        lines.append(
            f'  <channel site="{e["site"]}" site_id="{site_id}" lang="{e["lang"]}" xmltv_id="{xmltv_id}">{name}</channel>'
        )
    lines.append("</channels>")

    with open(OUTPUT, "w") as f:
        f.write("\n".join(lines) + "\n")

    by_site = defaultdict(int)
    for e in channels_by_xmltv.values():
        by_site[e["site"]] += 1

    print(f"\nGenerado {OUTPUT}")
    print(f"Total canales: {len(channels_by_xmltv)}")
    for site in TARGET_SITES:
        if by_site[site]:
            print(f"  {site}: {by_site[site]}")
    return 0


if __name__ == "__main__":
    exit(main())
