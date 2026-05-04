# VideoCoder

English | [Español](README_ESP.md)

VideoCoder is a terminal video compressor for movie and TV libraries. It is designed for batch use: recursive processing, aggressive HEVC recompression, optional language-based track cleanup, smart local renaming, and automatic fallback from GPU encoders to CPU `libx265`.

## Features

- Recursive scanning for `mp4`, `mkv`, `avi`, `mov`, `webm`, `ts`, `wmv`, `m4v`
- Two top-level modes:
  - `Automatic`
  - `Manual`
- Automatic compression profiles:
  - `Medium`
  - `High`
  - `Extreme`
  - `Custom target size per file`
- Per-file decisions based on codec, bitrate, resolution, duration, and size-per-minute
- Intelligent resolution scaling:
  - `4K -> 1080p`
  - `1080p / 960p-class -> 720p`
  - `720p -> 480p` only in stronger edge cases
- Optional language-based cleanup for audio and subtitles
- Forced subtitle preservation when relevant
- More aggressive audio compression with channel-aware Opus/AAC targets
- Smart local renaming without network lookups
- Optional original deletion only after a smaller successful output exists
- Simulation mode with `-S` / `--simulate`
- GPU encoder detection with automatic retry on CPU

## Requirements

- Python `3.10+`
- `ffmpeg`
- `ffprobe`

Recommended FFmpeg features:

- `libx265`
- `libopus`

## Installation

Clone the repository and run `main.py`. No extra Python packages are required.

System package examples:

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

## Usage

```bash
python3 main.py
```

Simulation only:

```bash
python3 main.py -S
```

Startup flow:

1. Choose UI language
2. Choose input folder
3. Choose whether to delete the source when the compressed file is smaller
4. Choose whether to smart-rename outputs
5. Choose mode

If you choose `Automatic`, the tool then asks for:

1. Compression profile
2. Whether language-based audio/subtitle cleanup should be enabled
3. Target language(s), only if cleanup is enabled

## Modes

### Automatic

Best for batch compression with minimal manual work.

Profiles:

- `Medium`
  - prioritizes visible quality
  - only downscales when the source is above roughly `2K`, then targets `1080p`
  - uses more conservative CRF decisions
- `High`
  - balance between quality retention and strong savings
  - can downscale `1080p / 960p-class` sources to `720p`
  - avoids the most aggressive behavior of `Extreme`
- `Extreme`
  - maximum automatic savings
  - uses the strongest automatic CRF and scaling rules
  - may push some oversized `720p` sources to `480p`
- `Custom target size per file`
  - asks for a target size per file during processing
  - estimates a target video bitrate from duration and kept tracks
  - can still scale resolution automatically to make the target more realistic

Automatic mode can optionally clean tracks by language:

- if enabled, it keeps only the chosen language when matching audio exists
- other-language audio is removed
- normal subtitles are removed when matching audio already exists
- forced subtitles are preserved when relevant
- if multiple tracks exist in the chosen language, the tool asks which one to keep

If cleanup is disabled:

- no language menus are shown
- all audio and subtitle tracks are kept

### Manual

Best for explicit control per file.

- manual audio selection
- manual subtitle selection
- manual CRF
- manual output resolution

## Video Strategy

VideoCoder does not apply one fixed rule to every source. Automatic mode evaluates each file using:

- source codec
- video or container bitrate
- resolution class
- duration
- size-per-minute

That data drives both:

- CRF selection
- resolution scaling

The goal is storage reduction that still tracks source quality reasonably well, rather than blindly forcing every file through the same settings.

## Audio Strategy

Audio is no longer treated with a single fixed bitrate.

- Efficient low-bitrate `AAC` and `Opus` tracks may be copied
- `AC3` and `EAC3` are typically re-encoded to save space
- Re-encoded audio uses channel-aware targets:
  - mono: `64k`
  - stereo: `96k`
  - `5.1`: `144k`
  - `7.1+`: `192k`

This tends to cut total output size noticeably on multi-audio releases without over-penalizing normal playback.

## Smart Rename

Smart rename works locally and does not use online metadata providers.

It is meant to:

- remove common release noise
- strip site names and download clutter
- normalize separators
- preserve episode codes such as `S01E05` or `E05`
- preserve movie years when clearly present

Example transformations:

- `Movie.Title.2019.1080p.BluRay.x264-GROUP.mkv`
  becomes roughly `Movie Title (2019)`
- `Show.Name.S01E05.720p.WEBRip.x265-GROUP.mkv`
  becomes roughly `Show Name S01E05`

## Output Behavior

VideoCoder never edits the source file in place.

Default behavior:

- the source is preserved
- output is written to a new file
- the standard suffix is `_compressed`

If smart rename is enabled, the cleaned title is used before `_compressed` is appended.

If original deletion is enabled:

- the original is deleted only after a successful encode
- the output must be smaller than the source
- if smart rename is enabled, the surviving output can be renamed to the cleaned title

If compression fails or the output is not smaller:

- the original stays untouched
- the bad output is removed

## Encoders

VideoCoder checks HEVC encoders in this order:

- `hevc_nvenc`
- `hevc_amf`
- `hevc_videotoolbox`
- `libx265`

If a GPU encoder is detected but fails at runtime, the same job is retried automatically with CPU `libx265`.

## Notes

- Subtitle handling depends on the output container.
- `mp4` subtitle output may require conversion to `mov_text`.
- Any lossy recompression can reduce quality. The automatic profiles are there to expose that tradeoff explicitly instead of hiding it.

## License

This project is licensed under the [MIT License](LICENSE).

If you redistribute substantial portions of the project, keep the copyright notice and license text intact, as required by the license.
