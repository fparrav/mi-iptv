---
name: playlist-validator
description: Valida la estructura y consistencia de playlist.m3u
---

Validate the generated playlist at `output/playlist.m3u`:

1. Verify header has `#EXTM3U` and optional `url-tvg`
2. Check every `#EXTINF` has a matching URL
3. Detect malformed tags or missing metadata
4. Count total channels and categorize by group
5. Report: total channels, malformed entries, missing tvg-id/tvg-logo

Output a summary: channels parsed, groups found, issues detected.
