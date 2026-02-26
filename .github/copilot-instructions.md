# VidSnatch – Copilot Instructions

## Architecture Overview

VidSnatch has three distinct interfaces that all funnel through a shared tool layer:

```
Web App (FastAPI)  ──┐
CLI (Click)        ──┤──► MCPTools (mcp_tools.py) ──► YouTubeDownloader (src/downloader.py)
MCP stdio server   ──┤                                        │
MCP HTTP server    ──┘                               pytubefix + youtube-transcript-api + ffmpeg
```

- **`src/downloader.py`** – The single source of truth for all YouTube operations. `YouTubeDownloader` is the only class that touches `pytubefix`, `youtube_transcript_api`, and `ffmpeg` directly.
- **`mcp_tools.py`** – `MCPTools` wraps `YouTubeDownloader` and is shared by the CLI and both MCP servers. Contains the canonical business logic and JSON-serialised return values.
- **`web_app.py`** – FastAPI app that calls `YouTubeDownloader` directly (bypasses `MCPTools`); streams file downloads to the browser.
- **`mcp_server.py`** / **`mcp_http_server.py`** – FastMCP stdio and HTTP transports; thin wrappers over `MCPTools`.
- **`src/cli.py`** – Click CLI; instantiates `MCPTools` via `_get_tools()` and re-uses its JSON return values for both `--json` and human-readable output.

## Entry Points

Defined in `pyproject.toml`:
```
vidsnatch          → src.cli:main
vidsnatch-web      → web_app:main       # http://localhost:8080
vidsnatch-mcp      → mcp_server:main    # stdio, for AI assistants
vidsnatch-mcp-http → mcp_http_server:main  # port 8090
```

## Key Developer Commands

```bash
uv sync                                     # install all dependencies
uv run python web_app.py                    # start web UI on :8080
uv run python mcp_http_server.py            # start MCP HTTP server on :8090
uv run python -m pytest tests/ -v           # run test suite
vidsnatch install --skills                  # install SKILL.md into AI tool configs
```

## Configuration

`mcp_config.json` is the primary config file (checked into the repo). All keys can be overridden with environment variables:

| Env var | Config key |
|---|---|
| `VIDSNATCH_DOWNLOAD_DIR` | `download_directory` |
| `VIDSNATCH_VIDEO_QUALITY` | `default_video_quality` |
| `VIDSNATCH_AUDIO_QUALITY` | `default_audio_quality` |
| `VIDSNATCH_MAX_FILE_SIZE_MB` | `max_file_size_mb` |
| `VIDSNATCH_HTTP_PORT` | `http_transport.port` |

Config loading: `mcp_config.py:load_config()` → reads JSON, then applies env overrides.

## Critical Patterns

### SSL Bypass (intentional, do not remove)
`src/downloader.py` globally patches `ssl`, `requests`, and `urllib3` to disable SSL verification. This is required for corporate proxy (Zscaler) compatibility and is applied at module import time.

### Retry Decorator
`src/utils.py` provides `@retry(tries, delay, backoff, exclude_exceptions)`. Applied to `_get_youtube_object` to handle transient YouTube API failures. `ValueError` (invalid URL) is excluded from retries.

### High-Quality Video Downloads Require ffmpeg
Downloads above the "progressive" stream quality download separate video and audio streams, then merge via `subprocess` ffmpeg call in `YouTubeDownloader._merge_files()`. ffmpeg must be installed (`brew install ffmpeg`).

### MCP stdio Logging
`mcp_server.py` sets all logging to `CRITICAL` with a `NullHandler` to keep stdout clean for the MCP stdio protocol. Never add print statements or logging to `mcp_server.py`.

### CLI Output Pattern
All CLI commands accept `--json` for machine-readable output. `src/cli.py:_output()` routes to `_print_human()` (formatted) or `json.dumps()` based on this flag. New CLI commands must follow this pattern.

### MCPTools Return Values
All `MCPTools` methods return JSON strings (not dicts). The CLI and MCP servers parse/relay these as-is. When adding new tools, return `json.dumps(result_dict, indent=2)` on success and `json.dumps({"error": message})` on failure.

## Key Files

- [src/downloader.py](../src/downloader.py) – all YouTube I/O; edit here for download behaviour
- [mcp_tools.py](../mcp_tools.py) – shared business logic; add new operations here first
- [src/cli.py](../src/cli.py) – CLI subcommands; extend with new Click commands
- [mcp_config.py](../mcp_config.py) – config loading + env var overrides
- [skills/vidsnatch/SKILL.md](../skills/vidsnatch/SKILL.md) – LLM skill file shipped with the package


<!-- vidsnatch-skill -->
---
name: vidsnatch
description: Downloads YouTube videos, audio, transcripts, and trims segments via CLI. Use when the user needs to download YouTube content, extract audio, get transcripts, or clip specific video segments.
---


# YouTube Downloads with vidsnatch

## Quick start

```bash
# search YouTube
vidsnatch search "python tutorial"
vidsnatch search "lo-fi music" --sort views
# inspect a video
vidsnatch info "https://youtube.com/watch?v=VIDEO_ID"
# download video
vidsnatch download video "https://youtube.com/watch?v=VIDEO_ID"
# download audio
vidsnatch download audio "https://youtube.com/watch?v=VIDEO_ID" --format mp3
# get transcript
vidsnatch download transcript "https://youtube.com/watch?v=VIDEO_ID"
# trim a clip
vidsnatch trim "https://youtube.com/watch?v=VIDEO_ID" --start 00:01:30 --end 00:03:00
# list downloaded files
vidsnatch list
```

## Commands

### Search

```bash
vidsnatch search "python tutorial"
vidsnatch search "lo-fi music" --sort views
vidsnatch search "react hooks" --sort date
vidsnatch search "machine learning" --json
```

Sort options: `relevance` (default), `date`, `views`.
Returns up to 10 results with title, URL, and duration.

### Info

```bash
vidsnatch info "https://youtube.com/watch?v=VIDEO_ID"
vidsnatch info "https://youtube.com/watch?v=VIDEO_ID" --json
```

### Download video

```bash
vidsnatch download video "https://youtube.com/watch?v=VIDEO_ID"
vidsnatch download video "https://youtube.com/watch?v=VIDEO_ID" --quality highest
vidsnatch download video "https://youtube.com/watch?v=VIDEO_ID" --quality high
vidsnatch download video "https://youtube.com/watch?v=VIDEO_ID" --quality medium
vidsnatch download video "https://youtube.com/watch?v=VIDEO_ID" --quality low
vidsnatch download video "https://youtube.com/watch?v=VIDEO_ID" --output ~/Videos
vidsnatch download video "https://youtube.com/watch?v=VIDEO_ID" --quality high --json
```

### Download audio

```bash
vidsnatch download audio "https://youtube.com/watch?v=VIDEO_ID"
vidsnatch download audio "https://youtube.com/watch?v=VIDEO_ID" --format mp3
vidsnatch download audio "https://youtube.com/watch?v=VIDEO_ID" --format m4a
vidsnatch download audio "https://youtube.com/watch?v=VIDEO_ID" --format wav
vidsnatch download audio "https://youtube.com/watch?v=VIDEO_ID" --quality highest
vidsnatch download audio "https://youtube.com/watch?v=VIDEO_ID" --output ~/Music --json
```

### Download transcript

```bash
vidsnatch download transcript "https://youtube.com/watch?v=VIDEO_ID"
vidsnatch download transcript "https://youtube.com/watch?v=VIDEO_ID" --language en
vidsnatch download transcript "https://youtube.com/watch?v=VIDEO_ID" --language es
vidsnatch download transcript "https://youtube.com/watch?v=VIDEO_ID" --json
```

### Trim (clip a segment)

```bash
# using HH:MM:SS
vidsnatch trim "https://youtube.com/watch?v=VIDEO_ID" --start 00:01:30 --end 00:03:00
# using MM:SS
vidsnatch trim "https://youtube.com/watch?v=VIDEO_ID" --start 01:30 --end 03:00
# using raw seconds
vidsnatch trim "https://youtube.com/watch?v=VIDEO_ID" --start 90 --end 180
# with quality and output
vidsnatch trim "https://youtube.com/watch?v=VIDEO_ID" --start 00:01:30 --end 00:03:00 --quality high --output ~/Clips
vidsnatch trim "https://youtube.com/watch?v=VIDEO_ID" --start 90 --end 180 --json
```

### List downloads

```bash
vidsnatch list
vidsnatch list --output ~/Videos
vidsnatch list --json
```

### Serve (start web app or MCP server)

```bash
# Start the web app (opens at http://localhost:8080)
vidsnatch serve web
vidsnatch serve web --port 9000
vidsnatch serve web --host 127.0.0.1 --port 9000

# Start the MCP stdio server (for Claude Desktop and AI assistants)
vidsnatch serve mcp

# Start the MCP HTTP server (opens at http://localhost:8090)
vidsnatch serve mcp-http
vidsnatch serve mcp-http --port 9090
```

### Install / Uninstall

```bash
vidsnatch install --skills
vidsnatch uninstall --skills
```

## Global options

```bash
--output DIR    # save to this directory (default: ./downloads)
--json          # output structured JSON instead of human-readable text
--help          # show command help
```

## Reference

### Quality levels

- `highest` — best available resolution (default); uses ffmpeg for 1080p+
- `high` — typically 720p
- `medium` — typically 480p
- `low` — smallest file size

### Audio formats

- `mp3` — most compatible, re-encoded (default)
- `m4a` — native AAC, no re-encoding, smallest
- `wav` — uncompressed PCM, lossless, largest

### Timestamp formats (for trim)

- `HH:MM:SS` — e.g. `00:01:30`
- `MM:SS` — e.g. `01:30`
- raw seconds — e.g. `90`

### Exit codes

- `0` — success
- `1` — error

## Example: Search then download

```bash
# Step 1: search for videos
vidsnatch search "python tutorial" --sort views

# Step 2: pick a result URL and download it
vidsnatch download video "https://youtube.com/watch?v=RESULT_ID" --quality high
```

## Example: Explore then download a clip

```bash
vidsnatch info "https://youtube.com/watch?v=VIDEO_ID"
vidsnatch download video "https://youtube.com/watch?v=VIDEO_ID" --quality high
```

## Example: Find a topic in transcript, then clip it

```bash
# Step 1: get timestamped transcript
vidsnatch download transcript "https://youtube.com/watch?v=VIDEO_ID" --json

# Step 2: search the transcript output for the topic, note the timestamps
# Step 3: trim the relevant segment
vidsnatch trim "https://youtube.com/watch?v=VIDEO_ID" --start 00:04:12 --end 00:06:45
```

## Example: Batch download audio for multiple videos

```bash
vidsnatch download audio "https://youtube.com/watch?v=VIDEO_1" --format mp3 --output ~/Podcasts
vidsnatch download audio "https://youtube.com/watch?v=VIDEO_2" --format mp3 --output ~/Podcasts
vidsnatch list --output ~/Podcasts
```

## Example: JSON output for scripting

```bash
vidsnatch info "https://youtube.com/watch?v=VIDEO_ID" --json
vidsnatch download video "https://youtube.com/watch?v=VIDEO_ID" --json
vidsnatch list --json
```

<!-- vidsnatch-skill -->
