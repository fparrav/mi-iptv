---
name: add-source
description: Agrega una nueva fuente M3U a configs/sources.json, le asigna la siguiente prioridad disponible, ejecuta scripts/update.py y reporta cuántos canales aportó la fuente.
---

Se te proporcionará un nombre y una URL para la nueva fuente M3U. Sigue estos pasos:

1. Leer `configs/sources.json`
2. Calcular la siguiente prioridad (max prioridad existente + 1)
3. Agregar la fuente con `enabled: true` y la prioridad calculada
4. Escribir el archivo actualizado
5. Ejecutar `python scripts/update.py` y reportar el total de canales antes y después del filtrado, y cuántos trajo la nueva fuente
