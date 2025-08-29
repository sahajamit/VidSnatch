#!/usr/bin/env python3
"""
VidSnatch MCP Server - Model Context Protocol server for YouTube video/audio downloads
"""

import json
import os
import tempfile
from typing import List, Optional, Literal
from mcp.server.fastmcp import FastMCP
from src import YouTubeDownloader
from src.logger import setup_logger

# Load configuration
def load_config():
    """Load MCP server configuration with environment variable overrides"""
    config_path = "mcp_config.json"
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
    else:
        # Default configuration
        config = {
            "download_directory": "./downloads",
            "default_video_quality": "highest",
            "default_audio_quality": "highest",
            "max_file_size_mb": 500,
            "allowed_formats": ["mp4", "webm", "mp3", "m4a"],
            "create_subdirs": True
        }
    
    # Override with environment variables if provided
    if os.getenv("VIDSNATCH_DOWNLOAD_DIR"):
        config["download_directory"] = os.getenv("VIDSNATCH_DOWNLOAD_DIR")
    
    if os.getenv("VIDSNATCH_VIDEO_QUALITY"):
        config["default_video_quality"] = os.getenv("VIDSNATCH_VIDEO_QUALITY")
        
    if os.getenv("VIDSNATCH_AUDIO_QUALITY"):
        config["default_audio_quality"] = os.getenv("VIDSNATCH_AUDIO_QUALITY")
        
    if os.getenv("VIDSNATCH_MAX_FILE_SIZE_MB"):
        config["max_file_size_mb"] = int(os.getenv("VIDSNATCH_MAX_FILE_SIZE_MB"))
    
    return config

# Initialize configuration and components
config = load_config()
# For MCP mode, redirect logging to stderr to avoid interfering with JSON protocol on stdout
import sys
import logging

# Disable all logging for MCP mode to ensure clean stdout
logging.basicConfig(
    level=logging.CRITICAL,
    handlers=[logging.NullHandler()],
    force=True
)

logger = logging.getLogger("vidsnatch-mcp")
downloader = YouTubeDownloader()

# Ensure download directory exists
os.makedirs(config["download_directory"], exist_ok=True)

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
    try:
        logger.info(f"Getting video info for: {url}")
        video_info = downloader.get_video_info(url)
        return json.dumps(video_info, indent=2)
    except Exception as e:
        error_msg = f"Failed to get video information: {str(e)}"
        logger.error(error_msg)
        return json.dumps({"error": error_msg})

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
    try:
        logger.info(f"Downloading video: {url} with quality: {quality}")
        
        # Use resolution if provided, otherwise use quality
        download_quality = resolution if resolution else quality
        
        # Download to configured directory
        downloaded_file = downloader.download_video(
            url, 
            config["download_directory"], 
            download_quality
        )
        
        file_size_mb = os.path.getsize(downloaded_file) / (1024 * 1024)
        
        result = {
            "status": "success",
            "file_path": downloaded_file,
            "file_size_mb": round(file_size_mb, 2),
            "download_directory": config["download_directory"]
        }
        
        logger.info(f"Video downloaded successfully: {downloaded_file}")
        return json.dumps(result, indent=2)
        
    except Exception as e:
        error_msg = f"Failed to download video: {str(e)}"
        logger.error(error_msg)
        return json.dumps({"status": "error", "error": error_msg})

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
    try:
        logger.info(f"Downloading audio: {url} with quality: {quality}, format: {format}")
        
        # Download to configured directory
        downloaded_file = downloader.download_audio(
            url, 
            config["download_directory"], 
            quality
        )
        
        file_size_mb = os.path.getsize(downloaded_file) / (1024 * 1024)
        
        result = {
            "status": "success",
            "file_path": downloaded_file,
            "file_size_mb": round(file_size_mb, 2),
            "download_directory": config["download_directory"],
            "format": format
        }
        
        logger.info(f"Audio downloaded successfully: {downloaded_file}")
        return json.dumps(result, indent=2)
        
    except Exception as e:
        error_msg = f"Failed to download audio: {str(e)}"
        logger.error(error_msg)
        return json.dumps({"status": "error", "error": error_msg})

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
    try:
        logger.info(f"Downloading transcript: {url} with language: {language}")
        
        # Download to configured directory
        downloaded_file = downloader.download_transcript(
            url, 
            config["download_directory"], 
            language
        )
        
        file_size_mb = os.path.getsize(downloaded_file) / (1024 * 1024)
        
        # Read transcript content to include in response
        try:
            with open(downloaded_file, 'r', encoding='utf-8') as f:
                transcript_content = f.read()
        except Exception as read_error:
            logger.warning(f"Could not read transcript file: {read_error}")
            transcript_content = None
        
        result = {
            "status": "success",
            "file_path": downloaded_file,
            "file_size_mb": round(file_size_mb, 2),
            "download_directory": config["download_directory"],
            "language": language,
            "transcript_content": transcript_content
        }
        
        logger.info(f"Transcript downloaded successfully: {downloaded_file}")
        return json.dumps(result, indent=2)
        
    except Exception as e:
        error_msg = f"Failed to download transcript: {str(e)}"
        logger.error(error_msg)
        return json.dumps({"status": "error", "error": error_msg})

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
    try:
        logger.info(f"Downloading video segment: {url} from {start_time}s to {end_time}s")
        
        if start_time >= end_time:
            raise ValueError("Start time must be less than end time")
        
        # Download to configured directory
        downloaded_file = downloader.download_video_segment(
            url, 
            start_time,
            end_time,
            config["download_directory"], 
            quality
        )
        
        file_size_mb = os.path.getsize(downloaded_file) / (1024 * 1024)
        
        result = {
            "status": "success",
            "file_path": downloaded_file,
            "file_size_mb": round(file_size_mb, 2),
            "download_directory": config["download_directory"],
            "start_time": start_time,
            "end_time": end_time,
            "duration": end_time - start_time
        }
        
        logger.info(f"Video segment downloaded successfully: {downloaded_file}")
        return json.dumps(result, indent=2)
        
    except Exception as e:
        error_msg = f"Failed to download video segment: {str(e)}"
        logger.error(error_msg)
        return json.dumps({"status": "error", "error": error_msg})

@mcp.tool()
def list_downloads() -> str:
    """
    List all files in the download directory.
    
    Returns:
        JSON string with list of downloaded files and their information
    """
    try:
        download_dir = config["download_directory"]
        
        if not os.path.exists(download_dir):
            return json.dumps({"files": [], "total_count": 0, "directory": download_dir})
        
        files = []
        for filename in os.listdir(download_dir):
            file_path = os.path.join(download_dir, filename)
            if os.path.isfile(file_path):
                file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
                files.append({
                    "filename": filename,
                    "file_path": file_path,
                    "size_mb": round(file_size_mb, 2),
                    "modified_time": os.path.getmtime(file_path)
                })
        
        # Sort by modification time (newest first)
        files.sort(key=lambda x: x["modified_time"], reverse=True)
        
        result = {
            "files": files,
            "total_count": len(files),
            "directory": download_dir
        }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        error_msg = f"Failed to list downloads: {str(e)}"
        logger.error(error_msg)
        return json.dumps({"error": error_msg})

@mcp.tool()
def get_config() -> str:
    """
    Get the current MCP server configuration.
    
    Returns:
        JSON string with current configuration settings
    """
    return json.dumps(config, indent=2)

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
