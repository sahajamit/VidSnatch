# VidSnatch MCP Server

VidSnatch now includes Model Context Protocol (MCP) server functionality, allowing AI assistants and other MCP clients to download YouTube videos and audio programmatically.

## Features

The MCP server exposes the following tools:

- **get_video_info**: Get detailed information about a YouTube video
- **download_video**: Download video with specified quality/resolution
- **download_audio**: Download audio in various formats and qualities
- **download_transcript**: Download video transcripts in different languages
- **download_video_segment**: Download specific time segments from videos
- **list_downloads**: List all downloaded files
- **get_config**: View current server configuration

## Configuration

The MCP server uses `mcp_config.json` for configuration:

```json
{
  "download_directory": "./downloads",
  "default_video_quality": "highest",
  "default_audio_quality": "highest",
  "max_file_size_mb": 500,
  "allowed_formats": ["mp4", "webm", "mp3", "m4a"],
  "create_subdirs": true
}
```

## Usage

### Starting the MCP Server

```bash
# Using UV scripts
uv run python3 mcp_server.py

# Or directly with Python
python3 mcp_server.py

# Or using the installed script
vidsnatch-mcp
```

### Starting the Web Application

```bash
# Using UV scripts
uv run web

# Or directly with Python
python web_app.py

# Or using the installed script
vidsnatch-web
```

### Development Mode

```bash
# Start development server with auto-reload
uv run dev
```

## MCP Client Integration

To use VidSnatch as an MCP server in your MCP client configuration:

```json
{
  "mcpServers": {
    "vidsnatch": {
      "command": "python",
      "args": ["/path/to/vidsnatch/mcp_server.py"],
      "cwd": "/path/to/vidsnatch"
    }
  }
}
```

## Tool Examples

### Download Video
```python
# Download highest quality video
result = download_video("https://youtube.com/watch?v=VIDEO_ID")

# Download specific resolution
result = download_video("https://youtube.com/watch?v=VIDEO_ID", resolution="720p")
```

### Download Audio
```python
# Download highest quality audio as MP3
result = download_audio("https://youtube.com/watch?v=VIDEO_ID")

# Download specific quality
result = download_audio("https://youtube.com/watch?v=VIDEO_ID", quality="128kbps")
```

### Download Video Segment
```python
# Download 30-second clip from 1:00 to 1:30
result = download_video_segment(
    "https://youtube.com/watch?v=VIDEO_ID", 
    start_time=60, 
    end_time=90
)
```

## File Organization

Downloaded files are organized in the configured download directory with meaningful filenames based on video titles and metadata.

## Error Handling

All tools return JSON responses with either success status and file information, or error status with detailed error messages for troubleshooting.
