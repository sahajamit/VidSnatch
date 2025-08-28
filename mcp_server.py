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
    """Load MCP server configuration"""
    config_path = "mcp_config.json"
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return json.load(f)
    else:
        # Default configuration
        return {
            "download_directory": "./downloads",
            "default_video_quality": "highest",
            "default_audio_quality": "highest",
            "max_file_size_mb": 500,
            "allowed_formats": ["mp4", "webm", "mp3", "m4a"],
            "create_subdirs": True
        }

# Initialize configuration and components
config = load_config()
# For MCP mode, redirect logging to stderr to avoid interfering with JSON protocol on stdout
import sys
import logging

# Configure logging to use stderr for MCP mode
logging.basicConfig(
    level=logging.INFO,
    format='📋 [%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stderr,
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
    Get detailed information about a YouTube video.
    
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
    Download transcript from a YouTube video to the configured download directory.
    
    Args:
        url: YouTube video URL or video ID
        language: Language code for transcript (e.g., "en", "es", "fr")
        
    Returns:
        JSON string with download status and file path
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
        
        result = {
            "status": "success",
            "file_path": downloaded_file,
            "file_size_mb": round(file_size_mb, 2),
            "download_directory": config["download_directory"],
            "language": language
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
    Download a specific segment/clip from a YouTube video.
    
    Args:
        url: YouTube video URL or video ID
        start_time: Start time in seconds
        end_time: End time in seconds
        quality: Video quality preference
        
    Returns:
        JSON string with download status and file path
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
    # Only log to stderr for MCP mode to avoid interfering with stdout JSON protocol
    print("🚀 Starting VidSnatch MCP Server...", file=sys.stderr)
    print(f"📁 Download directory: {config['download_directory']}", file=sys.stderr)
    print("🔧 Available tools: get_video_info, download_video, download_audio, download_transcript, download_video_segment, list_downloads, get_config", file=sys.stderr)
    
    # Run the MCP server
    mcp.run(transport='stdio')

if __name__ == "__main__":
    main()
