# VidSnatch Usage Guide

## Running VidSnatch

### Web Application Mode
Start the web interface for interactive downloads:

```bash
# Using UV
uv run python3 web_app.py

# Or using the installed script
vidsnatch-web

# Or directly
python3 web_app.py
```

Access the web interface at: http://localhost:8080

### MCP Server Mode
Start as an MCP server for programmatic access:

```bash
# Using UV
uv run python3 mcp_server.py

# Or using the installed script  
vidsnatch-mcp

# Or directly
python3 mcp_server.py
```

## MCP Server Tools

The MCP server exposes these tools:

1. **get_video_info(url)** - Get video metadata
2. **download_video(url, quality, resolution)** - Download video files
3. **download_audio(url, quality, format)** - Download audio files
4. **download_transcript(url, language)** - Download transcripts
5. **download_video_segment(url, start_time, end_time, quality)** - Download video clips
6. **list_downloads()** - List downloaded files
7. **get_config()** - View server configuration

## Configuration

Edit `mcp_config.json` to customize:
- Download directory
- Default quality settings
- File size limits
- Allowed formats

## Examples

### Download Video
```bash
# Highest quality
download_video("https://youtube.com/watch?v=VIDEO_ID")

# Specific resolution
download_video("https://youtube.com/watch?v=VIDEO_ID", resolution="720p")
```

### Download Audio
```bash
# Default MP3
download_audio("https://youtube.com/watch?v=VIDEO_ID")

# Specific quality
download_audio("https://youtube.com/watch?v=VIDEO_ID", quality="128kbps")
```

All downloads are saved to the configured directory with organized filenames.
