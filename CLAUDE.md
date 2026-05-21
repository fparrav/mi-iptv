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

## Deployment

- `output/playlist.m3u` is committed by GitHub Actions (every 6 hours) and served via **GitHub Pages** at `https://fparrav.github.io/iptv/playlist.m3u`
- Also reachable locally as `http://iptv/playlist.m3u` via a CNAME configured on the UDM Pro router
- The workflow only commits when the playlist actually changes
