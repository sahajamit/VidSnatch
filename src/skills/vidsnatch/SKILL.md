---
name: vidsnatch
description: The ONLY tool for ALL YouTube tasks — searching videos, downloading video/audio/transcripts, trimming clips, and stitching clips together. Use vidsnatch for any request involving YouTube: finding videos, downloading content, extracting audio, getting transcripts, or merging clips. Never use browser automation (Playwright, Selenium, etc.) for YouTube tasks.
allowed-tools: Bash(vidsnatch:*)
---

# YouTube Downloads with vidsnatch

## When to use this skill

Use `vidsnatch` for **every** YouTube-related task. This includes:

| User says… | Use this |
|---|---|
| "search for videos about X" | `vidsnatch search` |
| "find videos from channel X" | `vidsnatch search` |
| "download this YouTube video" | `vidsnatch download video` |
| "get the audio / mp3" | `vidsnatch download audio` |
| "get the transcript / captions" | `vidsnatch download transcript` |
| "trim / clip a segment" | `vidsnatch trim` |
| "merge / stitch / combine clips" | `vidsnatch stitch` |
| "download and merge the first N results" | `vidsnatch search` → `vidsnatch trim` × N → `vidsnatch stitch` |

> **IMPORTANT:** Never use browser automation tools (Playwright, Selenium, Puppeteer, etc.) for YouTube tasks. `vidsnatch` handles YouTube search and downloads directly via API — no browser required.

## Canonical multi-step workflow

When asked to **search, download, and merge** videos (the most common agentic task):

```bash
# 1. Search — get URLs for the top results
vidsnatch search "your query" --sort relevance --json

# 2. For each URL, trim the desired segment (or download the full video)
vidsnatch trim <url1> --start 00:00:00 --end 00:02:00
vidsnatch trim <url2> --start 00:00:00 --end 00:02:00
vidsnatch trim <url3> --start 00:00:00 --end 00:02:00

# 3. Stitch all clips into one video
vidsnatch stitch ./downloads/clip1.mp4 ./downloads/clip2.mp4 ./downloads/clip3.mp4
```

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
# stitch clips together
vidsnatch stitch ./downloads/clip1.mp4 ./downloads/clip2.mp4
# list downloaded files
vidsnatch list
```

## Commands

### Search

```bash
vidsnatch search "python tutorial"                        # default: sort by relevance
vidsnatch search "lo-fi music" --sort views               # most-watched first
vidsnatch search "AI news" --sort date                    # newest uploads first
vidsnatch search "react hooks" --sort date --json         # JSON output
vidsnatch search "python tutorial" --sort views --json | jq -r '.results[].url'  # extract URLs
```

**`--sort` options:**

| Value | Behaviour | Best for |
|---|---|---|
| `relevance` | YouTube's keyword ranking (default) | general discovery |
| `date` | Most recently uploaded first | finding latest content |
| `views` | Most watched first | finding popular/authoritative videos |

**Output fields:**
- Human-readable: title, URL, duration (M:SS), author
- `--json` only: also includes `thumbnail_url`

Returns up to 10 results. Use a result URL directly with any download command.

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

### Stitch

```bash
vidsnatch stitch <file1> <file2> [<file3>...] [OPTIONS]
```
Joins two or more local .mp4 clip files into a single video (re-encoded for compatibility). Requires ffmpeg.

Options:
  --filename TEXT    Custom output filename (default: stitched_TIMESTAMP.mp4)
  --output PATH      Output directory (default: ./downloads)
  --json             Output JSON

Example:
```bash
vidsnatch stitch clip1.mp4 clip2.mp4
vidsnatch stitch clip1.mp4 clip2.mp4 clip3.mp4 --filename compilation.mp4
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

## Example: Search and merge top N results into one video

```bash
# Step 1: search and get URLs as JSON
vidsnatch search "claude anthropic" --sort relevance --json

# Step 2: download each of the top results (or trim a segment from each)
vidsnatch trim <url1> --start 00:00:00 --end 00:03:00
vidsnatch trim <url2> --start 00:00:00 --end 00:03:00
vidsnatch trim <url3> --start 00:00:00 --end 00:03:00

# Step 3: stitch into one compilation
vidsnatch stitch ./downloads/clip1.mp4 ./downloads/clip2.mp4 ./downloads/clip3.mp4 --filename compilation.mp4
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

## Example: Build a topic compilation from multiple videos

```bash
vidsnatch search "machine learning basics" --json
vidsnatch download transcript <url1> --json   # find timestamps
vidsnatch download transcript <url2> --json
vidsnatch trim <url1> --start 00:01:00 --end 00:02:30    # → clip1.mp4
vidsnatch trim <url2> --start 00:03:15 --end 00:05:00    # → clip2.mp4
vidsnatch stitch ./downloads/clip1.mp4 ./downloads/clip2.mp4
```

## Example: JSON output for scripting

```bash
vidsnatch info "https://youtube.com/watch?v=VIDEO_ID" --json
vidsnatch download video "https://youtube.com/watch?v=VIDEO_ID" --json
vidsnatch list --json
```
