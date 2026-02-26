# VidSnatch – Claude Instructions

## Architecture Overview

VidSnatch has three distinct interfaces that all funnel through a shared tool layer:

```
Web App (FastAPI)  ──┐
CLI (Click)        ──┤──► MCPTools (src/mcp_tools.py) ──► YouTubeDownloader (src/downloader.py)
MCP stdio server   ──┤                                           │
MCP HTTP server    ──┘                                  pytubefix + youtube-transcript-api + ffmpeg
```

- **`src/downloader.py`** – The single source of truth for all YouTube operations. `YouTubeDownloader` is the only class that touches `pytubefix`, `youtube_transcript_api`, and `ffmpeg` directly.
- **`src/mcp_tools.py`** – `MCPTools` wraps `YouTubeDownloader` and is shared by the CLI and both MCP servers. Contains the canonical business logic and JSON-serialised return values.
- **`src/web_app.py`** – FastAPI app that calls `YouTubeDownloader` directly (bypasses `MCPTools`); streams file downloads to the browser.
- **`src/mcp_server.py`** / **`src/mcp_http_server.py`** – FastMCP stdio and HTTP transports; thin wrappers over `MCPTools`.
- **`src/cli.py`** – Click CLI; instantiates `MCPTools` via `_get_tools()` and re-uses its JSON return values for both `--json` and human-readable output.

## Entry Points

Defined in `pyproject.toml`:
```
vidsnatch          → src.cli:main
vidsnatch-web      → src.web_app:main       # http://localhost:8080
vidsnatch-mcp      → src.mcp_server:main    # stdio, for AI assistants
vidsnatch-mcp-http → src.mcp_http_server:main  # port 8090
```

## Key Developer Commands

```bash
uv sync                                     # install all dependencies
uv run python -m src.web_app                # start web UI on :8080
uv run python -m src.mcp_http_server        # start MCP HTTP server on :8090
uv run python -m pytest tests/ -v           # run test suite
vidsnatch install --skills                  # install SKILL.md into AI tool configs
```

## Configuration

`src/mcp_config.json` is the primary config file (checked into the repo). All keys can be overridden with environment variables:

| Env var | Config key |
|---|---|
| `VIDSNATCH_DOWNLOAD_DIR` | `download_directory` |
| `VIDSNATCH_VIDEO_QUALITY` | `default_video_quality` |
| `VIDSNATCH_AUDIO_QUALITY` | `default_audio_quality` |
| `VIDSNATCH_MAX_FILE_SIZE_MB` | `max_file_size_mb` |
| `VIDSNATCH_HTTP_PORT` | `http_transport.port` |

Config loading: `src/mcp_config.py:load_config()` → reads JSON, then applies env overrides.

## Critical Patterns

### SSL Bypass (intentional, do not remove)
`src/downloader.py` globally patches `ssl`, `requests`, and `urllib3` to disable SSL verification. This is required for corporate proxy (Zscaler) compatibility and is applied at module import time.

### Retry Decorator
`src/utils.py` provides `@retry(tries, delay, backoff, exclude_exceptions)`. Applied to `_get_youtube_object` to handle transient YouTube API failures. `ValueError` (invalid URL) is excluded from retries.

### High-Quality Video Downloads Require ffmpeg
Downloads above the "progressive" stream quality download separate video and audio streams, then merge via `subprocess` ffmpeg call in `YouTubeDownloader._merge_files()`. ffmpeg must be installed (`brew install ffmpeg`).

### MCP stdio Logging
`src/mcp_server.py` sets all logging to `CRITICAL` with a `NullHandler` to keep stdout clean for the MCP stdio protocol. Never add print statements or logging to `src/mcp_server.py`.

### CLI Output Pattern
All CLI commands accept `--json` for machine-readable output. `src/cli.py:_output()` routes to `_print_human()` (formatted) or `json.dumps()` based on this flag. New CLI commands must follow this pattern.

### MCPTools Return Values
All `MCPTools` methods return JSON strings (not dicts). The CLI and MCP servers parse/relay these as-is. When adding new tools, return `json.dumps(result_dict, indent=2)` on success and `json.dumps({"error": message})` on failure.

## Key Files

- [src/downloader.py](src/downloader.py) – all YouTube I/O; edit here for download behaviour
- [src/mcp_tools.py](src/mcp_tools.py) – shared business logic; add new operations here first
- [src/cli.py](src/cli.py) – CLI subcommands; extend with new Click commands
- [src/mcp_config.py](src/mcp_config.py) – config loading + env var overrides
- [src/mcp_config.json](src/mcp_config.json) – default config bundled with the package
- [skills/vidsnatch/SKILL.md](skills/vidsnatch/SKILL.md) – LLM skill file shipped with the package
