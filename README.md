# VideoCoder

English | [Español](README_ESP.md)

VideoCoder is a terminal batch compressor for movie and TV libraries. It focuses on practical storage reduction: recursive folder processing, language-aware track cleanup, optional smart renaming, and aggressive HEVC recompression with automatic fallbacks.

## Highlights

- Recursive processing for `mp4`, `mkv`, `avi`, `mov`, `webm`, `ts`, `wmv`, `m4v`
- Three operating modes:
  - `Automatic`
  - `Target Size`
  - `Manual`
- Automatic per-file decisions based on codec, bitrate, resolution, duration, and size-per-minute
- Intelligent downscaling:
  - `2160p -> 1080p`
  - `1080p -> 720p`
  - `720p -> 480p` only under strict conditions
- Language-aware audio/subtitle selection
- Forced subtitle preservation when relevant
- Smart output renaming without network lookups
- Optional original-file deletion only after a successful, smaller output
- Simulation mode with `-S` / `--simulate`
- GPU encoder detection with automatic fallback to CPU `libx265`

## Requirements

- Python `3.10+`
- `ffmpeg`
- `ffprobe`

Recommended FFmpeg features:

- `libx265`
- `libopus`

## Installation

Clone the repository and run `main.py`. No Python package install step is required.

Example dependencies:

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

## Quick Start

```bash
python3 main.py
```

Simulation-only:

```bash
python3 main.py -S
```

At startup the tool lets you choose:

1. UI language
2. Input folder
3. Whether the original file should be deleted if the compressed output is better
4. Whether output files should be smart-renamed
5. Compression mode

## Modes

### 1. Automatic

Best for bulk library compression.

Behavior:

- chooses audio/subtitle tracks automatically from the selected target language
- removes other-language audio when target-language audio exists
- removes normal subtitles when matching audio exists
- keeps forced subtitles when appropriate
- chooses CRF automatically
- may reduce resolution automatically when the source is clearly oversized for its effective quality

### 2. Target Size

Best when you want a predictable size budget per file.

Behavior:

- asks for a target size in MB
- estimates output bitrate from duration and selected tracks
- can also downscale automatically to help hit the target more realistically
- still rejects results that are not smaller than the source

This mode is approximate, not mathematically exact. It is bitrate-targeted, not strict final-size locking.

### 3. Manual

Best when you want explicit control.

Behavior:

- manual audio/subtitle selection
- manual CRF
- manual output resolution selection

## Resolution Strategy

Resolution is part of the compression strategy, not just a cosmetic option.

- `Automatic` and `Target Size` can decide resolution on their own
- `Manual` lets you select the output resolution explicitly
- `480p` is intentionally conservative in automatic modes and is only used in stronger edge cases

## Smart Rename

The smart rename option works locally and does not query online databases.

It is intended to:

- remove common release noise
- strip download-site clutter
- normalize separators
- preserve episode codes such as `S01E05` or `E05`
- keep movie years when they are clearly present

Examples:

- `Movie.Title.2019.1080p.BluRay.x264-GROUP.mkv`
  becomes roughly `Movie Title (2019)`
- `Show.Name.S01E05.720p.WEBRip.x265-GROUP.mkv`
  becomes roughly `Show Name S01E05`

## Output Rules

VideoCoder never edits the source file in place.

Default behavior:

- source file is kept
- output is written as a new file
- standard naming uses `_compressed`

If smart rename is enabled, the output stem is cleaned before the `_compressed` suffix is applied.

If original deletion is enabled:

- the original file is removed only after a successful encode
- the output must also be smaller than the original
- if smart rename is enabled, the final surviving file can be renamed to the cleaned title

If compression fails or the output is not smaller:

- the original is kept
- the bad output is discarded

## Encoders

VideoCoder checks for HEVC encoders in this order:

- `hevc_nvenc`
- `hevc_amf`
- `hevc_videotoolbox`
- `libx265`

If a GPU encoder is detected but fails at runtime, the job is retried automatically with CPU `libx265`.

## Notes

- Audio may be copied instead of re-encoded when it already looks efficient enough.
- Subtitle behavior depends on container compatibility.
- `mp4` subtitle output may require conversion to `mov_text`.
- Any lossy recompression can reduce quality. The tool is designed to balance that risk against storage savings, not eliminate it.

## Roadmap

- more robust content-type heuristics
- better reporting / logging
- optional sample-based comparison workflows
- further UI translation cleanup

## License

This project is licensed under the [MIT License](LICENSE).

If you redistribute substantial portions of the project, keep the copyright notice and license text intact, as required by the license.
