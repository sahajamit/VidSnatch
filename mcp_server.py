#!/usr/bin/env python3
"""
VidSnatch MCP Server - Model Context Protocol server for YouTube video/audio downloads (stdio transport)
"""

import sys
import logging
from typing import Optional
from mcp.server.fastmcp import FastMCP
from mcp_config import load_config, ensure_download_directory
from mcp_tools import MCPTools

# Initialize configuration and components
config = load_config()

# For MCP stdio mode, disable all logging to ensure clean stdout
logging.basicConfig(
    level=logging.CRITICAL,
    handlers=[logging.NullHandler()],
    force=True
)

logger = logging.getLogger("vidsnatch-mcp-stdio")

# Ensure download directory exists
ensure_download_directory(config)

# Initialize shared tools
tools = MCPTools(config, logger)

# Initialize FastMCP server
mcp = FastMCP("vidsnatch")

@mcp.tool()
def get_video_info(url: str) -> str:
    """
    Get detailed information about a YouTube video including title, duration, and available formats.
    
    Use this tool to understand video content before processing. For long videos where users want
    specific segments, consider following up with download_transcript to get timestamped content
    that can help locate specific topics or discussions.
    
    Args:
        url: YouTube video URL or video ID
        
    Returns:
        JSON string containing video information including title, duration, formats, etc.
    """
    return tools.get_video_info(url)

@mcp.tool()
def download_video(
    url: str, 
    quality: str = "highest",
    resolution: Optional[str] = None
) -> str:
    """
    Download a YouTube video to the configured download directory.
    
    Args:
        url: YouTube video URL or video ID
        quality: Video quality preference ("highest", "lowest", or specific quality like "720p")
        resolution: Specific resolution (e.g., "1080p", "720p", "480p") - overrides quality if provided
        
    Returns:
        JSON string with download status and file path
    """
    return tools.download_video(url, quality, resolution)

@mcp.tool()
def download_audio(
    url: str, 
    quality: str = "highest",
    format: str = "mp3"
) -> str:
    """
    Download audio from a YouTube video to the configured download directory.
    
    Args:
        url: YouTube video URL or video ID
        quality: Audio quality preference ("highest", "lowest", or specific bitrate like "128kbps")
        format: Audio format preference ("mp3", "m4a", "wav")
        
    Returns:
        JSON string with download status and file path
    """
    return tools.download_audio(url, quality, format)

@mcp.tool()
def download_transcript(
    url: str, 
    language: str = "en"
) -> str:
    """
    Download transcript with timestamps from a YouTube video. This is ESSENTIAL for finding specific topics or segments in videos.
    
    The transcript includes precise timestamps for each spoken segment, making it perfect for:
    - Locating when specific topics are discussed (e.g., "Windsurf deal", "AI features", etc.)
    - Finding exact time ranges for creating video clips
    - Searching through long videos to identify relevant sections
    
    WORKFLOW TIP: Always download the transcript FIRST when users ask for clips about specific topics,
    then use the timestamps to determine start_time and end_time for download_video_segment.
    
    Args:
        url: YouTube video URL or video ID
        language: Language code for transcript (e.g., "en", "es", "fr")
        
    Returns:
        JSON string with download status, file path, and full transcript content with timestamps.
        The transcript_content field contains the complete transcript text that can be analyzed directly.
    """
    return tools.download_transcript(url, language)

@mcp.tool()
def download_video_segment(
    url: str,
    start_time: float,
    end_time: float,
    quality: str = "highest"
) -> str:
    """
    Download a specific segment/clip from a YouTube video using precise timestamps.
    
    IMPORTANT: When users request clips about specific topics (e.g., "download the part about X"),
    you should FIRST use download_transcript to get the timestamped transcript, then analyze it to
    find the exact time range when that topic is discussed, and finally use those timestamps here.
    
    This tool is perfect for:
    - Creating short clips from long videos
    - Extracting specific discussions or segments
    - Sharing relevant portions without downloading entire videos
    
    Args:
        url: YouTube video URL or video ID
        start_time: Start time in seconds (get from transcript analysis)
        end_time: End time in seconds (get from transcript analysis)
        quality: Video quality preference ("highest", "720p", "480p", etc.)
        
    Returns:
        JSON string with download status and file path to the video segment
    """
    return tools.download_video_segment(url, start_time, end_time, quality)

@mcp.tool()
def list_downloads() -> str:
    """
    List all files in the download directory.
    
    Returns:
        JSON string with list of downloaded files and their information
    """
    return tools.list_downloads()

@mcp.tool()
def search_videos(query: str, sort_by: str = "relevance") -> str:
    """
    Search YouTube for videos matching a query. Returns up to 10 results.

    Use this tool to find YouTube videos by keyword before downloading.
    The returned URLs can be passed directly to get_video_info, download_video,
    download_audio, or download_transcript.

    Args:
        query: Search query string (e.g., "python tutorial", "lo-fi music")
        sort_by: Sort order -- "relevance" (default), "date", or "views"

    Returns:
        JSON string with search results, each containing title, url, and duration.
    """
    return tools.search_videos(query, sort_by=sort_by)

@mcp.tool()
def get_config() -> str:
    """
    Get the current MCP server configuration.
    
    Returns:
        JSON string with current configuration settings
    """
    return tools.get_config()

def main():
    """Main entry point for MCP server"""
    try:
        # Run the MCP server - FastMCP handles asyncio internally
        mcp.run(transport='stdio')
    except Exception as e:
        import sys
        print(f"MCP Server error: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        raise

if __name__ == "__main__":
    main()
