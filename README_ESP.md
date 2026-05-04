# VideoCoder

[English](README.md) | Español

VideoCoder es un compresor de vídeo para terminal orientado a bibliotecas de películas y series. Está pensado para trabajar por lotes: recorrido recursivo de carpetas, recompresión HEVC agresiva, limpieza opcional de pistas por idioma, renombrado inteligente local y fallback automático de GPU a CPU `libx265`.

## Características

- Escaneo recursivo para `mp4`, `mkv`, `avi`, `mov`, `webm`, `ts`, `wmv`, `m4v`
- Dos modos principales:
  - `Automático`
  - `Manual`
- Perfiles de compresión automática:
  - `Intermedia`
  - `Alta`
  - `Extrema`
  - `Tamaño objetivo personalizado por archivo`
- Decisiones por archivo según codec, bitrate, resolución, duración y tamaño por minuto
- Escalado inteligente de resolución:
  - `4K -> 1080p`
  - `1080p / clase 960p -> 720p`
  - `720p -> 480p` solo en casos más extremos
- Limpieza opcional de audio y subtítulos por idioma
- Conservación de subtítulos forzados cuando corresponde
- Compresión de audio más agresiva con objetivos según número de canales
- Renombrado inteligente local, sin consultas online
- Eliminación opcional del original solo cuando ya existe una salida válida y más pequeña
- Modo simulación con `-S` / `--simulate`
- Detección de encoder GPU con reintento automático en CPU

## Requisitos

- Python `3.10+`
- `ffmpeg`
- `ffprobe`

Recomendado en FFmpeg:

- `libx265`
- `libopus`

## Instalación

Clona el repositorio y ejecuta `main.py`. No hay paquetes Python extra que instalar.

Ejemplos de paquetes del sistema:

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

## Uso

```bash
python3 main.py
```

Solo simulación:

```bash
python3 main.py -S
```

Flujo de arranque:

1. Elegir idioma de interfaz
2. Elegir carpeta de entrada
3. Elegir si borrar el original cuando el comprimido sea menor
4. Elegir si activar renombrado inteligente
5. Elegir modo

Si eliges `Automático`, después se pide:

1. Perfil de compresión
2. Si quieres activar limpieza de audio/subtítulos por idioma
3. Idioma(s) objetivo, solo si la limpieza está activada

## Modos

### Automático

Pensado para compresión por lotes con la mínima intervención posible.

Perfiles:

- `Intermedia`
  - prioriza la calidad visible
  - solo baja resolución cuando la fuente supera aproximadamente `2K`, y entonces apunta a `1080p`
  - usa decisiones de `CRF` más conservadoras
- `Alta`
  - equilibrio entre conservar calidad y ahorrar bastante espacio
  - puede bajar fuentes tipo `1080p / 960p` a `720p`
  - evita el comportamiento más agresivo de `Extrema`
- `Extrema`
  - máximo ahorro automático
  - aplica las reglas más fuertes de `CRF` y escalado
  - puede llevar algunas fuentes `720p` muy infladas a `480p`
- `Tamaño objetivo personalizado por archivo`
  - pide un tamaño objetivo por archivo durante el proceso
  - estima el bitrate de vídeo a partir de la duración y de las pistas conservadas
  - también puede ajustar resolución automáticamente para acercarse al objetivo

El modo automático puede limpiar pistas por idioma de forma opcional:

- si se activa, conserva solo el idioma elegido cuando existe audio coincidente
- elimina audios de otros idiomas
- elimina subtítulos normales cuando ya existe audio en ese idioma
- conserva subtítulos forzados cuando conviene
- si hay varias pistas en el idioma elegido, deja escoger cuál conservar

Si la limpieza está desactivada:

- no aparecen menús de idioma
- se conservan todas las pistas de audio y subtítulos

### Manual

Pensado para control explícito por archivo.

- selección manual de audio
- selección manual de subtítulos
- `CRF` manual
- resolución de salida manual

## Estrategia de Vídeo

VideoCoder no aplica una única regla fija a todas las fuentes. El modo automático evalúa cada archivo usando:

- codec de origen
- bitrate de vídeo o del contenedor
- clase de resolución
- duración
- tamaño por minuto

Con esos datos decide dos cosas:

- el `CRF`
- el posible escalado de resolución

La idea es reducir almacenamiento de forma agresiva, pero relacionando la compresión con la calidad real aparente de la fuente, no machacando todo con exactamente el mismo ajuste.

## Estrategia de Audio

El audio ya no se trata con un único bitrate fijo.

- Pistas `AAC` y `Opus` ya eficientes pueden copiarse
- `AC3` y `EAC3` normalmente se recodifican para ahorrar espacio
- El audio recodificado usa objetivos según canales:
  - mono: `64k`
  - estéreo: `96k`
  - `5.1`: `144k`
  - `7.1+`: `192k`

Esto suele recortar bastante el tamaño total en releases con varios audios, sin castigar demasiado el uso normal.

## Renombrado Inteligente

El renombrado inteligente funciona en local y no consulta proveedores online.

Está pensado para:

- eliminar ruido típico de releases
- quitar webs y basura de descarga
- normalizar separadores
- conservar códigos de episodio como `S01E05` o `E05`
- mantener el año en películas cuando aparece claramente

Ejemplos:

- `Movie.Title.2019.1080p.BluRay.x264-GROUP.mkv`
  queda aproximadamente como `Movie Title (2019)`
- `Show.Name.S01E05.720p.WEBRip.x265-GROUP.mkv`
  queda aproximadamente como `Show Name S01E05`

## Comportamiento de Salida

VideoCoder nunca modifica el archivo original en el mismo nombre.

Comportamiento por defecto:

- el original se conserva
- la salida se escribe como archivo nuevo
- el sufijo estándar es `_compressed`

Si el renombrado inteligente está activo, primero se limpia el título y luego se añade `_compressed`.

Si activas el borrado del original:

- el original solo se elimina después de una compresión correcta
- la salida tiene que ser más pequeña que el original
- si el renombrado inteligente está activo, el archivo final puede quedarse con el nombre limpio

Si la compresión falla o la salida no mejora tamaño:

- el original permanece intacto
- la salida mala se elimina

## Encoders

VideoCoder comprueba encoders HEVC en este orden:

- `hevc_nvenc`
- `hevc_amf`
- `hevc_videotoolbox`
- `libx265`

Si detecta un encoder GPU pero falla al ejecutarse, reintenta automáticamente el mismo trabajo con `libx265` en CPU.

## Notas

- El tratamiento de subtítulos depende del contenedor de salida.
- En `mp4`, algunos subtítulos pueden requerir conversión a `mov_text`.
- Toda recompresión con pérdida puede reducir calidad. Los perfiles automáticos existen precisamente para exponer ese equilibrio de forma clara.

## Licencia

Este proyecto está licenciado bajo la [Licencia MIT](LICENSE).

Si redistribuyes partes sustanciales del proyecto, conserva el aviso de copyright y el texto de la licencia, tal como exige la licencia.
