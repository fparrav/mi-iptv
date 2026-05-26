# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Setup
pip install -r requirements.txt

# Run the aggregator (generates output/playlist.m3u)
python scripts/update.py
```

No test suite exists. Validate changes by running the script and inspecting `output/playlist.m3u`.

To publish: commit `output/playlist.m3u` and push — GitHub Pages sirve el archivo automáticamente. El workflow de GitHub Actions (`workflow_dispatch`) también puede dispararse manualmente desde la UI de GitHub.

## Architecture

Single-script pipeline in `scripts/update.py`:

1. **Fetch** — downloads each enabled source from `configs/sources.json` in priority order
2. **Parse** — `parse_m3u()` converts raw M3U text into `Channel` dataclass instances
3. **Deduplicate** — `deduplicate()` keeps the entry with richer metadata when names collide
4. **Filter placeholders** — `is_placeholder()` drops separator/non-channel entries
5. **Filter by country** — `filter_channels()` keeps channels matching `default_country` (default: `"CL"`) plus channels with no country (grouped as `"Other"`)
6. **Sort** — by `group_title` then `name`
7. **Write** — `write_m3u()` outputs to `output/playlist.m3u`

## Configuration (`configs/sources.json`)

- `sources[]` — list of M3U URLs; toggle with `"enabled": false`, order via `"priority"`
- `default_country` — ISO country code to filter by (e.g. `"CL"`)
- `enabled_groups` — list of group titles to include, or `["all"]` to skip group filtering
- `epg_urls[]` — EPG URLs embebidas en el header `url-tvg` del M3U (consumidas por el player IPTV)

### Fuentes activas

| Nombre | URL | Prioridad |
|---|---|---|
| alpox-json-teles | github.com/Alplox/json-teles | 1 |
| m3u.cl | m3u.cl/lista/CL.m3u (incluye `tvg-id` numéricos propios) | 2 |
| televito-tdt | github.com/Televito/TDT-Mundo | 3 |
| iptv-org-cl | iptv-org.github.io/iptv/countries/cl.m3u (81 canales con `tvg-id` estandarizados) | 4 |

### Deduplicación

`normalize_key()` strips resolución y tags antes de comparar: `"TVN (1080p) [Geo-blocked]"` → `"tvn"`. Cuando hay duplicados, gana el entry con más metadata (`tvg-id` > `tvg_logo` > `group_title`). Por esto, iptv-org gana sobre otras fuentes para canales que tienen `tvg-id`.

## Documentación

Los avances y modificaciones se documentan en el vault de Obsidian (`/Users/felipe/Library/Mobile Documents/iCloud~md~obsidian/Documents/MyVault`) según las reglas del `CLAUDE.md` del mismo vault.

## Deployment

- `output/playlist.m3u` is committed by GitHub Actions (every 6 hours) and served via **GitHub Pages** at `https://fparrav.github.io/iptv/playlist.m3u`
- Also reachable locally as `http://iptv/playlist.m3u` via:
  - DNS A record in UDM Pro: `iptv` → `10.0.0.205` (rpi1)
  - Traefik dynamic config in rpi-stack: `traefik/iptv.yml` proxies to GitHub Pages
- The workflow only commits when the playlist actually changes
