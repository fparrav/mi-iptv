# IPTV Personal

Lista IPTV personalizada agregada de fuentes públicas, con enfoque en canales chilenos.

## Fuentes

- [Alpox json-teles](https://github.com/Alplox/json-teles) - M3U con canales de Chile y Latinoamérica
- [m3u.cl](https://m3u.cl/lista/CL.m3u) - Lista de canales chilenos
- [Televito TDT-Mundo](https://github.com/Televito/TDT-Mundo) - IPTV de mundo hispanohablante

## Playlist

La lista generada se encuentra en:
- **Local (red):** `http://iptv/playlist.m3u` (A record + Traefik)
- **Remote:** `https://fparrav.github.io/mi-iptv/playlist.m3u`

## Actualización automática

El playlist se actualiza cada 24 horas vía GitHub Actions (cron diario a medianoche UTC). También puede dispararse manualmente desde la pestaña **Actions** de GitHub.

## Configuración local

```bash
pip install -r requirements.txt
python scripts/update.py
```

## Agregar fuentes

Editar `configs/sources.json` y añadir nuevas fuentes al array `sources`.

## Apple TV

Configurar el player IPTV con la URL del playlist.

## EPG

La playlist generada incluye las URLs de EPG en el header `url-tvg`, consumidas automáticamente por el player IPTV:

- `http://epg/puticastillo.xml`
- `http://epg/programadorx.xml`
