# source-auditor

Auditor de fuentes M3U para el aggregator IPTV.

## Task

Para cada fuente en `configs/sources.json`:

1. Fetch la URL y verificar que retorna M3U válido
2. Contar canales y detectar si la fuente cambió significativamente
3. Reportar fuentes deshabilitadas o con errores
4. Sugerir si hay fuentes nuevas populares en GitHub (buscar `iptv m3u lista`)

## Output

Reporte con: fuente, estado (ok/fail), canal count, canales duplicados, observaciones.
