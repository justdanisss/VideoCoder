# VideoCoder

[English](README.md) | Español

VideoCoder es un compresor por lotes para terminal orientado a bibliotecas de películas y series. La idea es sencilla: reducir almacenamiento de forma agresiva, limpiar pistas innecesarias, renombrar mejor los archivos y tomar decisiones automáticas razonables sin depender de servicios externos.

## Resumen

- Procesamiento recursivo para `mp4`, `mkv`, `avi`, `mov`, `webm`, `ts`, `wmv`, `m4v`
- Tres modos de trabajo:
  - `Automático`
  - `Tamaño objetivo`
  - `Manual`
- Decisiones automáticas por archivo según codec, bitrate, resolución, duración y tamaño por minuto
- Escalado inteligente de resolución:
  - `2160p -> 1080p`
  - `1080p -> 720p`
  - `720p -> 480p` solo en casos más restrictivos
- Selección de audio y subtítulos por idioma
- Conservación de subtítulos forzados cuando conviene
- Renombrado inteligente local, sin consultas online
- Eliminación opcional del original solo si la salida es correcta y más pequeña
- Modo simulación con `-S` / `--simulate`
- Detección de encoder GPU con fallback automático a CPU `libx265`

## Requisitos

- Python `3.10+`
- `ffmpeg`
- `ffprobe`

Recomendado en FFmpeg:

- `libx265`
- `libopus`

## Instalación

Clona el repositorio y ejecuta `main.py`. No hay dependencias Python adicionales que instalar.

Ejemplos de dependencias del sistema:

### Arch Linux

```bash
sudo pacman -S python ffmpeg
```

### Debian / Ubuntu

```bash
sudo apt update
sudo apt install python3 ffmpeg
```

### Fedora

```bash
sudo dnf install python3 ffmpeg
```

## Inicio Rápido

```bash
python3 main.py
```

Solo simulación:

```bash
python3 main.py -S
```

Al arrancar, la herramienta te deja elegir:

1. Idioma de la interfaz
2. Carpeta de entrada
3. Si quieres borrar el original cuando la salida sea mejor
4. Si quieres usar renombrado inteligente en la salida
5. Modo de compresión

## Modos

### 1. Automático

Pensado para comprimir una biblioteca grande con la menor intervención posible.

Comportamiento:

- selecciona audio y subtítulos automáticamente según el idioma objetivo
- elimina audios de otros idiomas cuando ya existe audio en el idioma elegido
- elimina subtítulos normales cuando el audio del idioma objetivo ya existe
- conserva subtítulos forzados cuando corresponde
- decide el `CRF` automáticamente
- puede bajar resolución si detecta que el archivo está claramente sobredimensionado

### 2. Tamaño objetivo

Pensado para trabajar con una meta aproximada de MB por archivo.

Comportamiento:

- pide un tamaño objetivo en MB
- estima el bitrate de salida a partir de la duración y de las pistas conservadas
- también puede bajar resolución automáticamente si hace falta para acercarse al objetivo
- sigue descartando resultados que no mejoren el tamaño del archivo original

No es un bloqueo exacto de tamaño final; es una aproximación basada en bitrate objetivo.

### 3. Manual

Pensado para control total sobre cada archivo.

Comportamiento:

- selección manual de audio y subtítulos
- `CRF` manual
- resolución de salida manual

## Estrategia de Resolución

La resolución forma parte de la compresión, no es un detalle secundario.

- `Automático` y `Tamaño objetivo` pueden decidir la resolución por sí solos
- `Manual` te deja elegirla explícitamente
- `480p` está limitado de forma bastante conservadora en los modos automáticos

## Renombrado Inteligente

La opción de renombrado inteligente trabaja en local y no consulta bases de datos online.

Su objetivo es:

- eliminar basura típica de releases
- quitar nombres de webs o fuentes de descarga
- normalizar separadores
- conservar patrones de episodio como `S01E05` o `E05`
- mantener el año en películas cuando está claramente presente

Ejemplos:

- `Movie.Title.2019.1080p.BluRay.x264-GROUP.mkv`
  queda aproximadamente como `Movie Title (2019)`
- `Show.Name.S01E05.720p.WEBRip.x265-GROUP.mkv`
  queda aproximadamente como `Show Name S01E05`

## Reglas de Salida

VideoCoder nunca modifica el archivo fuente en el mismo nombre.

Comportamiento por defecto:

- el original se conserva
- la salida se escribe como archivo nuevo
- el patrón estándar usa sufijo `_compressed`

Si el renombrado inteligente está activo, primero limpia el nombre base y luego aplica `_compressed`.

Si activas el borrado del original:

- el original solo se elimina después de una compresión correcta
- la salida debe ser además más pequeña que el original
- si el renombrado inteligente está activo, el archivo final superviviente puede quedarse con el nombre limpio

Si la compresión falla o la salida no mejora tamaño:

- el original se conserva
- la salida mala se descarta

## Encoders

VideoCoder busca encoders HEVC en este orden:

- `hevc_nvenc`
- `hevc_amf`
- `hevc_videotoolbox`
- `libx265`

Si detecta un encoder GPU pero falla al ejecutarse, reintenta automáticamente con `libx265` en CPU.

## Notas

- El audio puede copiarse en lugar de recodificarse si ya parece suficientemente eficiente.
- El tratamiento de subtítulos depende del contenedor y de la compatibilidad de salida.
- En `mp4`, algunos subtítulos pueden requerir conversión a `mov_text`.
- Toda recompresión con pérdida puede reducir calidad. El objetivo aquí es equilibrar ese coste visual con un ahorro real de espacio.

## Roadmap

- heurísticas más finas por tipo de contenido
- mejores logs e informes
- flujos opcionales de comparación por muestras
- más pulido en la interfaz bilingüe

## Licencia

Este proyecto está licenciado bajo la [Licencia MIT](LICENSE).

Si redistribuyes partes sustanciales del proyecto, conserva el aviso de copyright y el texto de la licencia, tal como exige la licencia.
