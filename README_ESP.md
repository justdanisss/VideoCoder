# VideoCoder

[English](README.md) | Español

VideoCoder es un compresor de vídeo por lotes para terminal, pensado para bibliotecas personales de películas y series.

Está diseñado para:

- reducir el tamaño de los archivos de forma agresiva manteniendo la mayor calidad posible
- procesar carpetas completas de forma recursiva
- decidir automáticamente qué pistas de audio y subtítulos conservar
- evitar reemplazar el archivo original salvo que tú lo autorices
- ofrecer interfaz tanto en inglés como en español

El punto de entrada actual del proyecto es [`main.py`](main.py).

## Características

- Modo automático con decisiones por archivo basadas en codec, bitrate, resolución y tamaño por minuto
- Modo manual para elegir pistas de audio/subtítulos y controlar el CRF
- Modo simulación con `-S` o `--simulate`
- Eliminación opcional del archivo original solo si el archivo comprimido es más pequeño
- Detección automática de encoder GPU con fallback a CPU
- Filtrado de audio por idioma
- Limpieza de subtítulos, con soporte para conservar subtítulos forzados cuando convenga
- Seguridad en la salida: los archivos comprimidos se escriben como archivos nuevos con sufijo `_compressed`
- Descarte automático si el resultado comprimido no mejora el tamaño del original

## Contenedores Soportados

Actualmente VideoCoder analiza estas extensiones:

- `mp4`
- `mkv`
- `avi`
- `mov`
- `webm`
- `ts`
- `wmv`
- `m4v`

## Requisitos

- Python `3.10+`
- `ffmpeg`
- `ffprobe`

Recomendado:

- `ffmpeg` compilado con `libx265`
- `ffmpeg` compilado con `libopus`

## Instalación

### Opción 1: uso local simple

1. Clona o descarga este repositorio.
2. Asegúrate de tener Python 3.10 o superior instalado.
3. Asegúrate de que `ffmpeg` y `ffprobe` estén disponibles en tu `PATH`.
4. Ejecuta el script:

```bash
python3 main.py
```

### Opción 2: Arch Linux

El script incluye una comprobación de dependencias y puede pedirte instalar paquetes faltantes con `pacman`.

Si prefieres instalarlos manualmente:

```bash
sudo pacman -S python ffmpeg
```

### Opción 3: Debian / Ubuntu

```bash
sudo apt update
sudo apt install python3 ffmpeg
```

### Opción 4: Fedora

```bash
sudo dnf install python3 ffmpeg
```

## Uso

Ejecuta la herramienta desde la carpeta del proyecto:

```bash
python3 main.py
```

El flujo inicial es:

1. Elegir idioma de la interfaz: inglés o español
2. Introducir la carpeta de entrada
3. Decidir si quieres borrar los archivos originales cuando la versión comprimida sea mejor
4. Elegir modo de compresión:
   - Automático
   - Manual

### Modo Simulación

El modo simulación analiza todo pero no comprime nada.

```bash
python3 main.py -S
```

o

```bash
python3 main.py --simulate
```

Es útil para revisar decisiones antes de procesar una biblioteca grande.

## Modos de Compresión

### Modo Automático

El modo automático está pensado para bibliotecas grandes y limpiezas por lotes.

Hace lo siguiente:

- inspecciona codec, bitrate, resolución y tamaño del archivo
- elige automáticamente una intensidad de compresión
- intenta preservar la mayor calidad visual posible mientras reduce al máximo el tamaño
- solo omite archivos cuando parecen ya demasiado comprimidos como para mejorarlos con seguridad

Comportamiento de pistas en modo automático:

- si existe audio en el idioma objetivo seleccionado, los demás idiomas de audio se eliminan de la copia comprimida
- los subtítulos normales se eliminan cuando ya existe audio en el idioma correspondiente
- los subtítulos forzados pueden conservarse
- si hay varias pistas de audio en el idioma elegido, el script te deja escoger cuál conservar

### Modo Manual

El modo manual te permite:

- elegir tú mismo las pistas de audio
- elegir tú mismo las pistas de subtítulos
- fijar un `CRF` manualmente

Úsalo cuando quieras control total sobre un archivo concreto o un lote pequeño.

## Comportamiento de la Salida

VideoCoder nunca edita el archivo original en el mismo sitio.

Por defecto:

- el archivo original permanece intacto
- se crea un archivo nuevo con sufijo `_compressed`

Ejemplo:

- `Pelicula.mkv` -> `Pelicula_compressed.mkv`

Si ya existe un archivo `_compressed`, VideoCoder crea una variante única, por ejemplo:

- `Pelicula_compressed_2.mkv`

Si activas la eliminación del original al inicio:

- el archivo original se elimina solo después de crear correctamente el archivo comprimido
- además, el archivo comprimido debe ser más pequeño que el original

Si la compresión falla o el resultado sale más grande:

- el original se conserva
- la salida mala se descarta

## Comportamiento del Encoder

VideoCoder intenta usar encoders HEVC disponibles en este orden:

- `hevc_nvenc`
- `hevc_amf`
- `hevc_videotoolbox`
- `libx265`

Si un encoder GPU parece disponible pero falla al ejecutarse, la herramienta reintenta automáticamente con `libx265` en CPU.

## Notas sobre Audio y Subtítulos

- El audio puede copiarse en lugar de recodificarse cuando ya usa un codec y bitrate razonables.
- El tratamiento de subtítulos depende del modo y del idioma seleccionado.
- En `mp4`, la salida de subtítulos está limitada por la compatibilidad del contenedor y puede convertirse a `mov_text`.
- En `mkv`, los subtítulos normalmente se copian cuando es posible.

## Notas de Seguridad

- El script solo puede borrar archivos originales si tú apruebas explícitamente esa opción al inicio.
- Las decisiones de compresión están basadas en heurísticas; no son mágicas, así que conviene probar antes con unos pocos archivos importantes.
- Incluso intentando preservar al máximo la calidad, cualquier recompresión con pérdida puede introducir alguna degradación visual.

## Ejemplos de Uso

### Comprimir una carpeta completa de una serie

```bash
python3 main.py
```

- elige `English` o `Español`
- selecciona la carpeta de la temporada
- activa la eliminación del original si quieres limpiar la biblioteca más rápido
- elige `Automatico`
- selecciona el idioma que quieres conservar

### Previsualizar una biblioteca de películas sin escribir archivos

```bash
python3 main.py -S
```

Esto te permite inspeccionar las decisiones previstas antes de lanzar el trabajo real.

## Limitaciones Conocidas

- La traducción de la interfaz funciona, pero todavía no está perfectamente pulida en todos los mensajes.
- Las decisiones de compresión están basadas en heurísticas, así que seguirán existiendo casos límite.
- Algunos formatos de subtítulos dependen mucho del soporte del contenedor.

## Ideas de Futuro

- mejor detección por tipo de contenido: anime, cine con grano, webcam, capturas de pantalla, etc.
- modo con tamaño objetivo
- logs e informes más ricos
- modo de comparación con clips de prueba
- mejora del pulido general de la interfaz bilingüe

## Licencia

Este proyecto está licenciado bajo la [Licencia MIT](LICENSE).

Si usas o redistribuyes partes sustanciales de este proyecto, conserva el aviso
de copyright original y el texto de la licencia, tal como exige la licencia.
