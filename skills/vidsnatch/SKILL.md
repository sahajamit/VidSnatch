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
