---
name: new-source
description: Valida y propone una nueva fuente M3U para sources.json
---

When the user wants to add a new M3U source:

1. Fetch the URL and verify it returns valid M3U content
2. Count channels and sample metadata quality (tvg-id, tvg-logo, group-title)
3. Check for duplicates against existing sources in configs/sources.json
4. Suggest a priority value based on channel count and quality
5. Output a JSON snippet ready to paste into sources.json:
   ```json
   {
     "name": "source-name",
     "url": "https://...",
     "enabled": true,
     "priority": 5
   }
   ```
