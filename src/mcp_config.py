#!/usr/bin/env python3
"""
VidSnatch MCP Configuration - Shared configuration for both stdio and HTTP transports
"""

import json
import os
import pathlib
from typing import Dict, Any


def load_config() -> Dict[str, Any]:
    """Load MCP server configuration with environment variable overrides"""
    config_path = str(pathlib.Path(__file__).parent / "mcp_config.json")
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
            "create_subdirs": True,
            "http_transport": {
                "enabled": False,
                "host": "0.0.0.0",
                "port": 8090,
                "enable_cors": True,
                "stream_downloads": True
            }
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
    
    # HTTP transport environment overrides
    if os.getenv("VIDSNATCH_HTTP_HOST"):
        config["http_transport"]["host"] = os.getenv("VIDSNATCH_HTTP_HOST")
        
    if os.getenv("VIDSNATCH_HTTP_PORT"):
        config["http_transport"]["port"] = int(os.getenv("VIDSNATCH_HTTP_PORT"))
        
    if os.getenv("VIDSNATCH_HTTP_ENABLE_CORS"):
        config["http_transport"]["enable_cors"] = os.getenv("VIDSNATCH_HTTP_ENABLE_CORS").lower() == "true"
        
    if os.getenv("VIDSNATCH_HTTP_STREAM_DOWNLOADS"):
        config["http_transport"]["stream_downloads"] = os.getenv("VIDSNATCH_HTTP_STREAM_DOWNLOADS").lower() == "true"
    
    return config


def ensure_download_directory(config: Dict[str, Any]) -> None:
    """Ensure the download directory exists"""
    os.makedirs(config["download_directory"], exist_ok=True)
