# VideoCoder

English | [Español](README_ESP.md)

VideoCoder is a terminal-based batch video compressor for personal movie and TV libraries.

It is designed to:

- reduce file size aggressively while keeping quality as high as possible
- process full folders recursively
- automatically choose what to keep from audio and subtitle tracks
- avoid replacing your original file unless you explicitly allow it
- support both English and Spanish in the UI

The current project entrypoint is [`main.py`](main.py).

## Features

- Automatic mode with per-file decisions based on codec, bitrate, resolution, and size-per-minute
- Manual mode for explicit audio/subtitle selection and CRF control
- Simulation mode with `-S` or `--simulate`
- Optional deletion of the original file only when the compressed file is smaller
- Automatic GPU encoder detection with CPU fallback
- Audio language filtering
- Subtitle cleanup, with support for keeping forced subtitles when relevant
- Output safety: compressed files are written as new files with `_compressed` in the name
- Output rejection if the compressed result is not smaller than the original

## Supported Containers

VideoCoder currently scans these extensions:

- `mp4`
- `mkv`
- `avi`
- `mov`
- `webm`
- `ts`
- `wmv`
- `m4v`

## Requirements

- Python `3.10+`
- `ffmpeg`
- `ffprobe`

Recommended:

- `ffmpeg` built with `libx265`
- `ffmpeg` built with `libopus`

## Installation

### Option 1: Simple local usage

1. Clone or download this repository.
2. Make sure Python 3.10+ is installed.
3. Make sure `ffmpeg` and `ffprobe` are available in your `PATH`.
4. Run the script:

```bash
python3 main.py
```

### Option 2: Arch Linux

The script includes a dependency check and can prompt to install missing packages with `pacman`.

If you want to install them manually:

```bash
sudo pacman -S python ffmpeg
```

### Option 3: Debian / Ubuntu

```bash
sudo apt update
sudo apt install python3 ffmpeg
```

### Option 4: Fedora

```bash
sudo dnf install python3 ffmpeg
```

## Usage

Run the tool from the project folder:

```bash
python3 main.py
```

The startup flow is:

1. Choose UI language: English or Spanish
2. Enter the input folder
3. Decide whether to delete original files when the compressed result is better
4. Choose compression mode:
   - Automatic
   - Manual

### Simulation Mode

Simulation mode analyzes everything but does not compress anything.

```bash
python3 main.py -S
```

or

```bash
python3 main.py --simulate
```

This is useful for checking decisions before processing a large library.

## Compression Modes

### Automatic Mode

Automatic mode is intended for large libraries and bulk cleanup.

It will:

- inspect codec, bitrate, resolution, and file size
- choose a compression strength automatically
- try to preserve high visual quality while reducing file size as much as possible
- skip files only when they already appear too compressed to safely improve

Track behavior in automatic mode:

- if audio exists in the selected target language, other audio languages are removed from the compressed copy
- normal subtitles are removed when matching audio is already present
- forced subtitles can be kept
- if multiple audio tracks exist in the chosen language, the script lets you choose which one to keep

### Manual Mode

Manual mode lets you:

- pick audio tracks yourself
- pick subtitle tracks yourself
- set a manual `CRF`

Use it when you want full control over a specific file or a small batch.

## Output Behavior

VideoCoder never edits the source file in place.

By default:

- the original file remains untouched
- a new output file is created with a `_compressed` suffix

Example:

- `Movie.mkv` -> `Movie_compressed.mkv`

If a `_compressed` file already exists, VideoCoder creates a unique variant such as:

- `Movie_compressed_2.mkv`

If you enable original deletion at startup:

- the original file is removed only after the compressed file is successfully created
- the compressed file must also be smaller than the original

If compression fails or the result is larger:

- the original file is kept
- the bad output is discarded

## Encoder Behavior

VideoCoder tries to use available HEVC encoders in this order:

- `hevc_nvenc`
- `hevc_amf`
- `hevc_videotoolbox`
- `libx265`

If a GPU encoder appears available but fails at runtime, the tool automatically retries with CPU `libx265`.

## Audio and Subtitle Notes

- Audio may be copied instead of re-encoded when it already uses a sensible codec and bitrate.
- Subtitle handling depends on mode and language choices.
- For `mp4`, subtitle output is limited by container compatibility and may be converted to `mov_text`.
- For `mkv`, subtitles are generally copied when possible.

## Safety Notes

- The script can delete original files only if you explicitly approve that option at startup.
- Compression decisions are heuristic-based, not magical; for important media, test on a few files first.
- Even when preserving quality aggressively, any lossy recompression can introduce some visual loss.

## Example Workflows

### Compress a full TV show folder

```bash
python3 main.py
```

- choose `English`
- select your season folder
- enable original deletion if you want a fast library cleanup
- choose `Automatic`
- select the language you want to keep

### Preview a movie library without writing files

```bash
python3 main.py -S
```

This lets you inspect the planned decisions before running the real job.

## Known Limitations

- The UI translation is functional but not yet perfectly polished in every message.
- Compression decisions are based on heuristics, so edge cases will still exist.
- Some subtitle formats depend heavily on container support.

## Roadmap Ideas

- better per-content detection for anime, grainy film, webcam, and screen captures
- target-size mode
- richer logs and reports
- sample clip comparison mode
- improved multi-language UI cleanup

## License

This project is licensed under the [MIT License](LICENSE).

If you use or redistribute substantial parts of this project, please keep the
original copyright notice and license text intact, as required by the license.
