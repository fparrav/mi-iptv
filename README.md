# IPTV Personal

Lista IPTV personalizada agregada de fuentes públicas, con enfoque en canales chilenos.

## Fuentes

- [Alpox json-teles](https://github.com/Alplox/json-teles) - M3U con canales de Chile y Latinoamérica
- [m3u.cl](https://m3u.cl/lista/CL.m3u) - Lista de canales chilenos
- [Televito TDT-Mundo](https://github.com/Televito/TDT-Mundo) - IPTV de mundo hispanohablante

## Playlist

La lista generada se encuentra en:
- **Local (red):** `http://iptv/playlist.m3u` (via CNAME en UDM Pro)
- **Remote:** `https://fparrav.github.io/mi-iptv/playlist.m3u`

## Actualización automática

El playlist se actualiza cada 6 horas vía GitHub Actions.

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

Soporte EPG pendiente de implementación.
