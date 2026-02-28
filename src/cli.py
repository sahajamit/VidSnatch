"""
VidSnatch CLI - Enhanced command-line interface with subcommands.
"""

import json
import sys
import os
import click
from pathlib import Path


def _get_tools(output_dir=None):
    """Instantiate MCPTools with config, optionally overriding download_directory."""
    from .mcp_config import load_config
    from .mcp_tools import MCPTools

    config = load_config()
    if output_dir is not None:
        config["download_directory"] = output_dir
        os.makedirs(output_dir, exist_ok=True)
    return MCPTools(config)


def _parse_timestamp(ts: str) -> float:
    """Convert HH:MM:SS or MM:SS to seconds."""
    parts = ts.strip().split(":")
    if len(parts) == 3:
        h, m, s = parts
        return int(h) * 3600 + int(m) * 60 + float(s)
    elif len(parts) == 2:
        m, s = parts
        return int(m) * 60 + float(s)
    else:
        return float(ts)


def _output(data: dict, as_json: bool):
    """Print output in human-readable or JSON format."""
    if as_json:
        click.echo(json.dumps(data, indent=2))
    else:
        _print_human(data)


def _print_human(data: dict):
    """Print a result dict in human-readable format."""
    status = data.get("status", "")
    if status == "error" or "error" in data:
        msg = data.get("error", data.get("message", str(data)))
        click.echo(f"Error: {msg}", err=True)
        return

    # info command
    if "title" in data and "duration" in data:
        click.echo(f"Title:    {data.get('title')}")
        click.echo(f"Author:   {data.get('author')}")
        click.echo(f"Duration: {data.get('duration')} seconds")
        click.echo(f"Views:    {data.get('views', 'N/A')}")
        if data.get("video_streams"):
            click.echo("\nVideo streams:")
            for s in data["video_streams"][:5]:
                mb = (s.get("file_size") or 0) / (1024 * 1024)
                click.echo(f"  {s.get('resolution')} @ {s.get('fps')}fps  ({mb:.1f} MB)")
        if data.get("audio_streams"):
            click.echo("\nAudio streams:")
            for s in data["audio_streams"][:3]:
                mb = (s.get("file_size") or 0) / (1024 * 1024)
                click.echo(f"  {s.get('abr')}  ({mb:.1f} MB)")
        return

    # list command
    if "files" in data:
        files = data.get("files", [])
        if not files:
            click.echo(f"No files in {data.get('directory', 'downloads')}")
            return
        click.echo(f"Files in {data.get('directory')}  ({data.get('total_count')} total):")
        for f in files:
            click.echo(f"  {f['filename']}  ({f['size_mb']} MB)")
        return

    # stitch command
    if "clip_count" in data and "file_path" in data:
        filename = os.path.basename(data["file_path"])
        size = data.get("file_size_mb", "?")
        click.echo(f"Stitched video:  {filename}")
        click.echo(f"Path:            {data['file_path']}")
        click.echo(f"Size:            {size} MB")
        click.echo(f"Clips joined:    {data['clip_count']}")
        return

    # download/trim commands
    if "file_path" in data:
        filename = os.path.basename(data["file_path"])
        size = data.get("file_size_mb", "?")
        click.echo(f"Downloaded: {filename}  ({size} MB)")
        click.echo(f"Path: {data['file_path']}")
        if "start_time" in data:
            click.echo(f"Segment: {data['start_time']}s – {data['end_time']}s  ({data.get('duration')}s)")
        if "language" in data:
            click.echo(f"Language: {data['language']}")
        return

    # search command
    if "results" in data and "query" in data:
        click.echo(f'Search: "{data["query"]}"  ({data["count"]} results, sorted by {data["sort_by"]})\n')
        for i, r in enumerate(data["results"], 1):
            mins = r["duration"] // 60 if r["duration"] else 0
            secs = r["duration"] % 60 if r["duration"] else 0
            click.echo(f"  {i:2d}. {r['title']}")
            click.echo(f"      {r['url']}  ({mins}:{secs:02d})  by {r.get('author', 'Unknown')}")
        return

    # config command or fallback
    click.echo(json.dumps(data, indent=2))


# ─── CLI definition ──────────────────────────────────────────────────────────

_MAIN_EPILOG = """
\b
Commands:
  search      Search YouTube by keyword and list matching videos.
  info        Show title, duration, views, and available video/audio streams.
  download    Download video, audio, or transcript (has subcommands).
  trim        Download a precise time segment of a video.
  stitch      Join multiple local video clips into one video.
  list        List files already saved to the download directory.
  serve       Start the web app or MCP server (has subcommands).
  install     Install the VidSnatch skill file into LLM tool directories.
  uninstall   Remove the VidSnatch skill file from LLM tool directories.

Workflows:

\b
  # 0. Search YouTube then download a result
  vidsnatch search "python tutorial" --sort views
  vidsnatch download video "https://youtube.com/watch?v=RESULT_ID"

\b
  # 1. Explore before downloading
  vidsnatch info "<url>"
  vidsnatch download video "<url>" --quality high

\b
  # 2. Extract audio
  vidsnatch download audio "<url>" --format mp3

\b
  # 3. Get transcript to find topics, then clip the relevant segment
  vidsnatch download transcript "<url>" --json
  vidsnatch trim "<url>" --start 00:04:12 --end 00:06:45

\b
  # 4. Machine-readable output for scripting / LLM pipelines
  vidsnatch info "<url>" --json
  vidsnatch download video "<url>" --json

\b
  # 5. Install skill file so AI assistants know how to use this CLI
  vidsnatch install --skills

\b
  # 6. Start the web app or MCP server
  vidsnatch serve web
  vidsnatch serve mcp
  vidsnatch serve mcp-http

Exit codes:  0 = success,  1 = error
"""

@click.group(epilog=_MAIN_EPILOG, context_settings={"max_content_width": 90})
def cli():
    """VidSnatch — download YouTube videos, audio, transcripts, and clips.

    Every command accepts --output DIR (override save location) and --json
    (machine-readable output). Run any command with --help for full details.
    """


# ── vidsnatch info ────────────────────────────────────────────────────────────

_INFO_EPILOG = """
Output includes:

  - Title, author, duration (seconds), view count, publish date
  - Up to 5 video streams with resolution, fps, and file size
  - Up to 3 audio streams with bitrate and file size

Examples:

  \b
  # Human-readable summary
  vidsnatch info "https://youtube.com/watch?v=VIDEO_ID"

  \b
  # JSON — pipe into jq or use in scripts
  vidsnatch info "https://youtube.com/watch?v=VIDEO_ID" --json | jq '.duration'
"""

@cli.command("info", epilog=_INFO_EPILOG)
@click.argument("url")
@click.option("--json", "as_json", is_flag=True,
              help="Output structured JSON instead of human-readable text.")
def info_cmd(url, as_json):
    """Show metadata, available formats, and duration for a YouTube video.

    URL is any valid YouTube video URL or short URL (youtu.be/...).
    Use this before downloading to check available quality levels and file sizes.
    """
    tools = _get_tools()
    raw = tools.get_video_info(url)
    data = json.loads(raw)
    if "error" in data:
        _output(data, as_json)
        sys.exit(1)
    _output(data, as_json)


# ── vidsnatch download ────────────────────────────────────────────────────────

_DOWNLOAD_EPILOG = """
\b
Subcommands:
  video       Download the video file (mp4).
  audio       Extract audio track (mp3 / m4a / wav).
  transcript  Download timestamped transcript as a text file.

Run `vidsnatch download <subcommand> --help` for per-subcommand options and examples.
"""

@cli.group("download", epilog=_DOWNLOAD_EPILOG)
def download():
    """Download video, audio, or transcript from a YouTube URL."""


_DOWNLOAD_VIDEO_EPILOG = """
\b
Quality levels:
  highest   Best available resolution; merges separate video+audio streams
            for 1080p/1440p/4K using ffmpeg.  (default)
  high      Typically 720p.
  medium    Typically 480p.
  low       Lowest available resolution — smallest file size.

Examples:

  \b
  vidsnatch download video "https://youtube.com/watch?v=VIDEO_ID"
  vidsnatch download video "https://youtube.com/watch?v=VIDEO_ID" --quality high
  vidsnatch download video "https://youtube.com/watch?v=VIDEO_ID" --output ~/Videos
  vidsnatch download video "https://youtube.com/watch?v=VIDEO_ID" --quality low --json
"""

@download.command("video", epilog=_DOWNLOAD_VIDEO_EPILOG)
@click.argument("url")
@click.option("--quality", default="highest",
              type=click.Choice(["highest", "high", "medium", "low"], case_sensitive=False),
              show_default=True,
              help="Video quality level (highest/high/medium/low).")
@click.option("--output", "output_dir", default=None,
              help="Directory to save the file (overrides config default: ./downloads).")
@click.option("--json", "as_json", is_flag=True,
              help="Output structured JSON instead of human-readable text.")
def download_video(url, quality, output_dir, as_json):
    """Download a YouTube video as an mp4 file.

    For resolutions above 720p, video and audio streams are downloaded
    separately and merged with ffmpeg — ensure ffmpeg is installed.
    """
    tools = _get_tools(output_dir)
    raw = tools.download_video(url, quality=quality)
    data = json.loads(raw)
    if data.get("status") == "error":
        _output(data, as_json)
        sys.exit(1)
    _output(data, as_json)


_DOWNLOAD_AUDIO_EPILOG = """
\b
Formats:
  mp3   Most compatible; re-encoded from the source stream.  (default)
  m4a   Native AAC container — no re-encoding, smallest size.
  wav   Uncompressed PCM — largest size, lossless.

Quality levels:  highest (default), high, medium, low

Examples:

  \b
  vidsnatch download audio "https://youtube.com/watch?v=VIDEO_ID"
  vidsnatch download audio "https://youtube.com/watch?v=VIDEO_ID" --format m4a
  vidsnatch download audio "https://youtube.com/watch?v=VIDEO_ID" --format wav --quality highest
  vidsnatch download audio "https://youtube.com/watch?v=VIDEO_ID" --output ~/Music --json
"""

@download.command("audio", epilog=_DOWNLOAD_AUDIO_EPILOG)
@click.argument("url")
@click.option("--format", "fmt", default="mp3",
              type=click.Choice(["mp3", "m4a", "wav"], case_sensitive=False),
              show_default=True,
              help="Output audio format (mp3/m4a/wav).")
@click.option("--quality", default="highest",
              type=click.Choice(["highest", "high", "medium", "low"], case_sensitive=False),
              show_default=True,
              help="Audio quality level (highest/high/medium/low).")
@click.option("--output", "output_dir", default=None,
              help="Directory to save the file (overrides config default: ./downloads).")
@click.option("--json", "as_json", is_flag=True,
              help="Output structured JSON instead of human-readable text.")
def download_audio(url, fmt, quality, output_dir, as_json):
    """Extract the audio track from a YouTube video.

    Requires ffmpeg for mp3 and wav conversion.
    m4a skips re-encoding and is the fastest option.
    """
    tools = _get_tools(output_dir)
    raw = tools.download_audio(url, quality=quality, format=fmt)
    data = json.loads(raw)
    if data.get("status") == "error":
        _output(data, as_json)
        sys.exit(1)
    _output(data, as_json)


_DOWNLOAD_TRANSCRIPT_EPILOG = """
\b
Language codes (BCP-47):
  en    English  (default)
  es    Spanish
  fr    French
  de    German
  ja    Japanese
  zh    Chinese
  pt    Portuguese
  (any other BCP-47 code supported by YouTube)

\b
Output:
  Human-readable mode prints the file path and language.
  --json mode includes the full transcript_content field with
  timestamped lines — useful for searching topics or piping to an LLM.

Workflow tip — find a topic then clip it:

  \b
  # Step 1: get full transcript with timestamps
  vidsnatch download transcript "https://youtube.com/watch?v=VIDEO_ID" --json

  \b
  # Step 2: use the timestamps you found to cut the segment
  vidsnatch trim "https://youtube.com/watch?v=VIDEO_ID" --start 00:04:12 --end 00:06:45

Examples:

  \b
  vidsnatch download transcript "https://youtube.com/watch?v=VIDEO_ID"
  vidsnatch download transcript "https://youtube.com/watch?v=VIDEO_ID" --language es
  vidsnatch download transcript "https://youtube.com/watch?v=VIDEO_ID" --json
"""

@download.command("transcript", epilog=_DOWNLOAD_TRANSCRIPT_EPILOG)
@click.argument("url")
@click.option("--language", default="en", show_default=True,
              help="BCP-47 language code for the transcript (e.g. en, es, fr, de, ja).")
@click.option("--output", "output_dir", default=None,
              help="Directory to save the file (overrides config default: ./downloads).")
@click.option("--json", "as_json", is_flag=True,
              help="Output structured JSON (includes full transcript_content with timestamps).")
def download_transcript(url, language, output_dir, as_json):
    """Download a timestamped transcript from a YouTube video.

    Saves a text file with one line per spoken segment, each prefixed
    with its timestamp.  Use --json to get the full content inline —
    ideal for searching topics before trimming a segment.
    """
    tools = _get_tools(output_dir)
    raw = tools.download_transcript(url, language=language)
    data = json.loads(raw)
    if data.get("status") == "error":
        _output(data, as_json)
        sys.exit(1)
    # In human mode suppress full transcript_content to keep output readable
    if not as_json and "transcript_content" in data:
        data_display = {k: v for k, v in data.items() if k != "transcript_content"}
        _output(data_display, as_json)
    else:
        _output(data, as_json)


# ── vidsnatch trim ────────────────────────────────────────────────────────────

_TRIM_EPILOG = """
\b
Timestamp formats accepted by --start and --end:
  HH:MM:SS    e.g. 00:01:30  (1 minute 30 seconds)
  MM:SS       e.g. 01:30
  seconds     e.g. 90        (raw float seconds)

Quality levels:  highest (default), high, medium, low

Workflow tip — use the transcript to find exact timestamps:

  \b
  # 1. Get timestamped transcript
  vidsnatch download transcript "https://youtube.com/watch?v=VIDEO_ID" --json

  \b
  # 2. Search transcript for the topic, note the timestamps
  # 3. Trim the segment
  vidsnatch trim "https://youtube.com/watch?v=VIDEO_ID" --start 00:04:12 --end 00:06:45

Examples:

  \b
  # Trim using HH:MM:SS
  vidsnatch trim "https://youtube.com/watch?v=VIDEO_ID" --start 00:01:30 --end 00:03:00

  \b
  # Trim using raw seconds
  vidsnatch trim "https://youtube.com/watch?v=VIDEO_ID" --start 90 --end 180

  \b
  # Trim with quality and custom output directory
  vidsnatch trim "https://youtube.com/watch?v=VIDEO_ID" \\
      --start 00:01:30 --end 00:03:00 --quality high --output ~/Clips

  \b
  # JSON output for scripting
  vidsnatch trim "https://youtube.com/watch?v=VIDEO_ID" --start 90 --end 180 --json
"""

@cli.command("trim", epilog=_TRIM_EPILOG)
@click.argument("url")
@click.option("--start", required=True,
              help="Start time as HH:MM:SS, MM:SS, or raw seconds (e.g. 00:01:30 or 90).")
@click.option("--end", required=True,
              help="End time as HH:MM:SS, MM:SS, or raw seconds (e.g. 00:03:00 or 180).")
@click.option("--quality", default="highest",
              type=click.Choice(["highest", "high", "medium", "low"], case_sensitive=False),
              show_default=True,
              help="Video quality level (highest/high/medium/low).")
@click.option("--output", "output_dir", default=None,
              help="Directory to save the clip (overrides config default: ./downloads).")
@click.option("--json", "as_json", is_flag=True,
              help="Output structured JSON instead of human-readable text.")
def trim_cmd(url, start, end, quality, output_dir, as_json):
    """Download a precise time segment (clip) from a YouTube video.

    Both --start and --end are required.  Accepts HH:MM:SS, MM:SS, or
    plain seconds.  Requires ffmpeg for frame-accurate segment extraction.

    Tip: run `vidsnatch download transcript --json` first to find the
    exact timestamps for the topic you want to clip.
    """
    try:
        start_sec = _parse_timestamp(start)
        end_sec = _parse_timestamp(end)
    except ValueError:
        click.echo("Error: Invalid timestamp format. Use HH:MM:SS or seconds.", err=True)
        sys.exit(1)

    tools = _get_tools(output_dir)
    raw = tools.download_video_segment(url, start_time=start_sec, end_time=end_sec, quality=quality)
    data = json.loads(raw)
    if data.get("status") == "error":
        _output(data, as_json)
        sys.exit(1)
    _output(data, as_json)


# ── vidsnatch stitch ──────────────────────────────────────────────────────────

_STITCH_EPILOG = """
\b
Workflow tip — build a topic compilation:

  \b
  # 1. Get transcripts to find relevant timestamps
  vidsnatch download transcript "<url1>" --json
  vidsnatch download transcript "<url2>" --json

  \b
  # 2. Trim the relevant segments
  vidsnatch trim "<url1>" --start 00:01:00 --end 00:02:30
  vidsnatch trim "<url2>" --start 00:03:15 --end 00:05:00

  \b
  # 3. Stitch the clips into a compilation
  vidsnatch stitch ./downloads/clip1.mp4 ./downloads/clip2.mp4

Examples:

  \b
  # Join two clips (output auto-named stitched_TIMESTAMP.mp4)
  vidsnatch stitch ./downloads/clip1.mp4 ./downloads/clip2.mp4

  \b
  # Three clips with a custom filename
  vidsnatch stitch clip1.mp4 clip2.mp4 clip3.mp4 --filename my_compilation.mp4

  \b
  # Custom output directory
  vidsnatch stitch clip1.mp4 clip2.mp4 --output ./final/

  \b
  # JSON output for scripting
  vidsnatch stitch clip1.mp4 clip2.mp4 --json
"""

@cli.command("stitch", epilog=_STITCH_EPILOG)
@click.argument("files", nargs=-1, required=True, type=click.Path(exists=True))
@click.option("--output", "-o", "output_dir", default=None,
              help="Output directory (overrides config default: ./downloads).")
@click.option("--filename", "-f", default=None,
              help="Output filename (default: stitched_TIMESTAMP.mp4).")
@click.option("--json", "as_json", is_flag=True,
              help="Output structured JSON instead of human-readable text.")
def stitch_cmd(files, output_dir, filename, as_json):
    """Stitch multiple local video clips together into one video.

    Accepts two or more local .mp4 file paths.  Clips are re-encoded with
    libx264 + aac for maximum compatibility across mixed sources.
    Requires ffmpeg.
    """
    if len(files) < 2:
        click.echo("Error: At least 2 files are required to stitch.", err=True)
        sys.exit(1)
    tools = _get_tools(output_dir)
    raw = tools.stitch_videos(list(files), output_filename=filename)
    data = json.loads(raw)
    if "error" in data:
        _output(data, as_json)
        sys.exit(1)
    _output(data, as_json)


# ── vidsnatch list ────────────────────────────────────────────────────────────

_LIST_EPILOG = """
Examples:

\b
  # List files in the default downloads directory
  vidsnatch list

  \b
  # List files in a custom directory
  vidsnatch list --output ~/Videos

  \b
  # JSON output — includes file paths, sizes, and modification timestamps
  vidsnatch list --json
"""

@cli.command("list", epilog=_LIST_EPILOG)
@click.option("--output", "output_dir", default=None,
              help="Directory to list (overrides config default: ./downloads).")
@click.option("--json", "as_json", is_flag=True,
              help="Output structured JSON with file paths, sizes, and modification times.")
def list_cmd(output_dir, as_json):
    """List files in the download directory, sorted newest first.

    Shows filename and size in MB.  Use --json to get full paths and
    modification timestamps suitable for scripting.
    """
    tools = _get_tools(output_dir)
    raw = tools.list_downloads()
    data = json.loads(raw)
    if "error" in data:
        _output(data, as_json)
        sys.exit(1)
    _output(data, as_json)


# ── vidsnatch install ─────────────────────────────────────────────────────────

_INSTALL_EPILOG = """
\b
Installed locations:
  Claude Code      ~/.claude/skills/vidsnatch/SKILL.md
  OpenClaw         ~/.openclaw/workspace/skills/vidsnatch/SKILL.md
  Copilot          ~/.copilot/skills/vidsnatch/SKILL.md
  Cursor           ~/.cursor/rules/vidsnatch.md
  GitHub Copilot   .github/copilot-instructions.md  (appended, current repo)

Targets are skipped silently when their parent directory does not exist
(i.e. the tool has never been launched on this machine).  A summary of
what was installed and what was skipped is printed after the command runs.

Example:

  \b
  vidsnatch install --skills
"""

@cli.command("install", epilog=_INSTALL_EPILOG)
@click.option("--skills", is_flag=True, required=True,
              help="Copy SKILL.md into Claude Code, OpenClaw, Copilot, Cursor, and GitHub Copilot directories.")
def install_cmd(skills):
    """Install the VidSnatch skill file into LLM tool directories.

    The skill file (SKILL.md) teaches AI coding assistants (Claude Code,
    OpenClaw, Copilot, Cursor, GitHub Copilot) what commands are available and how to use them,
    enabling prompt-driven downloads without memorising the CLI syntax.
    """
    if skills:
        from src.installer import install_skills
        install_skills()


# ── vidsnatch search ─────────────────────────────────────────────────────────

_SEARCH_EPILOG = """
\b
Sort options:
  relevance   YouTube's default ranking — best keyword match.  (default)
  date        Most recently uploaded videos first.
  views       Most viewed videos first — great for finding popular content.

\b
Output fields (human-readable):
  title, URL, duration (M:SS), author

\b
Output fields (--json only):
  title, url, duration, author, thumbnail_url

Returns up to 10 results.

Examples:

  \b
  # Basic search — default relevance sort
  vidsnatch search "python tutorial"

  \b
  # Find the most-watched videos on a topic
  vidsnatch search "lo-fi music" --sort views

  \b
  # Find the latest uploads
  vidsnatch search "AI news" --sort date

  \b
  # Combine sort + JSON for scripting or LLM pipelines
  vidsnatch search "react hooks" --sort date --json

  \b
  # Pipe JSON into jq to extract just the URLs
  vidsnatch search "python tutorial" --sort views --json | jq -r '.results[].url'
"""

@cli.command("search", epilog=_SEARCH_EPILOG)
@click.argument("query")
@click.option("--sort", "sort_by", default="relevance",
              type=click.Choice(["relevance", "date", "views"], case_sensitive=False),
              show_default=True,
              help="Sort order: relevance (default) | date (newest first) | views (most watched first).")
@click.option("--json", "as_json", is_flag=True,
              help="Output structured JSON (includes thumbnail_url in addition to human-readable fields).")
def search_cmd(query, sort_by, as_json):
    """Search YouTube and display up to 10 matching videos.

    QUERY is the search term. Each result shows title, URL, duration, and author.
    Use --json to also get thumbnail_url, suitable for scripting or LLM pipelines.
    Pass a result URL directly to any download command to fetch that video.
    """
    tools = _get_tools()
    raw = tools.search_videos(query, sort_by=sort_by)
    data = json.loads(raw)
    if data.get("status") == "error":
        _output(data, as_json)
        sys.exit(1)
    _output(data, as_json)


# ── vidsnatch uninstall ──────────────────────────────────────────────────────

_UNINSTALL_EPILOG = """
\b
Removes skill files from:
  Claude Code      ~/.claude/skills/vidsnatch/SKILL.md
  OpenClaw         ~/.openclaw/workspace/skills/vidsnatch/SKILL.md
  Copilot          ~/.copilot/skills/vidsnatch/SKILL.md
  Cursor           ~/.cursor/rules/vidsnatch.md
  GitHub Copilot   .github/copilot-instructions.md  (vidsnatch block removed)

Example:

  \b
  vidsnatch uninstall --skills
"""

@cli.command("uninstall", epilog=_UNINSTALL_EPILOG)
@click.option("--skills", is_flag=True, required=True,
              help="Remove SKILL.md from Claude Code, OpenClaw, Copilot, Cursor, and GitHub Copilot directories.")
def uninstall_cmd(skills):
    """Remove the VidSnatch skill file from LLM tool directories.

    Reverses the effect of `vidsnatch install --skills` by deleting
    copied skill files and cleaning up the GitHub Copilot instructions block.
    """
    if skills:
        from src.installer import uninstall_skills
        uninstall_skills()


# ── vidsnatch serve ─────────────────────────────────────────────────────────

_SERVE_EPILOG = """
\b
Subcommands:
  web         Start the web application (FastAPI + Tailwind CSS UI).
  mcp         Start the MCP server using stdio transport (for AI assistants).
  mcp-http    Start the MCP server using HTTP transport (remote access).

Examples:

  \b
  # Start the web app on default port 8080
  vidsnatch serve web

  \b
  # Start on a custom port
  vidsnatch serve web --port 9000

  \b
  # Start the MCP stdio server (for Claude Desktop, etc.)
  vidsnatch serve mcp

  \b
  # Start the MCP HTTP server on default port 8090
  vidsnatch serve mcp-http

  \b
  # Start MCP HTTP server on a custom port
  vidsnatch serve mcp-http --port 9090
"""

@cli.group("serve", epilog=_SERVE_EPILOG)
def serve():
    """Start the web app or MCP server.

    Use subcommands to launch VidSnatch in different modes.
    The CLI is the universal entry point for all three channels:
    CLI commands, Web UI, and MCP server.
    """


@serve.command("web")
@click.option("--host", default=None, help="Host to bind to (default: 0.0.0.0).")
@click.option("--port", default=None, type=int, help="Port to listen on (default: 8080).")
def serve_web(host, port):
    """Start the VidSnatch web application.

    Launches a FastAPI server with a web UI for interactive downloads.
    Open http://localhost:8080 (or your custom port) in a browser.
    """
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from web_app import main as web_main
    web_main(host=host, port=port)


@serve.command("mcp")
def serve_mcp():
    """Start the MCP server using stdio transport.

    Used by AI assistants like Claude Desktop that communicate over
    standard input/output.  Configure your MCP client to run:
    vidsnatch serve mcp
    """
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from mcp_server import main as mcp_main
    mcp_main()


@serve.command("mcp-http")
@click.option("--host", default=None, help="Host to bind to (default: 0.0.0.0).")
@click.option("--port", default=None, type=int, help="Port to listen on (default: 8090).")
def serve_mcp_http(host, port):
    """Start the MCP server using HTTP transport.

    Launches an HTTP server with SSE streaming for remote AI assistants
    and web-based MCP clients.  Default endpoint: http://localhost:8090/mcp
    """
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from mcp_http_server import main as mcp_http_main
    mcp_http_main(host=host, port=port)


def main():
    cli()


if __name__ == "__main__":
    main()
