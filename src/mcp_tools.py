#!/usr/bin/env python3
"""
VidSnatch MCP Tools - Shared tools for both stdio and HTTP transports
"""

import json
import os
import logging
from typing import Optional, Dict, Any, Callable
from . import YouTubeDownloader


class MCPTools:
    """Shared MCP tools implementation that can be used by both stdio and HTTP transports"""
    
    def __init__(self, config: Dict[str, Any], logger: Optional[logging.Logger] = None):
        self.config = config
        self.logger = logger or logging.getLogger("vidsnatch-mcp-tools")
        self.downloader = YouTubeDownloader()
        
    def get_video_info(self, url: str) -> str:
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
            self.logger.info(f"Getting video info for: {url}")
            video_info = self.downloader.get_video_info(url)
            return json.dumps(video_info, indent=2)
        except Exception as e:
            error_msg = f"Failed to get video information: {str(e)}"
            self.logger.error(error_msg)
            return json.dumps({"error": error_msg})

    def download_video(
        self, 
        url: str, 
        quality: str = "highest",
        resolution: Optional[str] = None,
        progress_callback: Optional[Callable[[dict], None]] = None
    ) -> str:
        """
        Download a YouTube video to the configured download directory.
        
        Args:
            url: YouTube video URL or video ID
            quality: Video quality preference ("highest", "lowest", or specific quality like "720p")
            resolution: Specific resolution (e.g., "1080p", "720p", "480p") - overrides quality if provided
            progress_callback: Optional callback for progress updates (HTTP streaming)
            
        Returns:
            JSON string with download status and file path
        """
        try:
            self.logger.info(f"Downloading video: {url} with quality: {quality}")
            
            if progress_callback:
                progress_callback({
                    "status": "starting", 
                    "message": f"Starting video download for: {url}",
                    "progress": 0
                })
            
            # Use resolution if provided, otherwise use quality
            download_quality = resolution if resolution else quality
            
            # Download to configured directory
            downloaded_file = self.downloader.download_video(
                url, 
                self.config["download_directory"], 
                download_quality
            )
            
            if progress_callback:
                progress_callback({
                    "status": "processing", 
                    "message": "Processing downloaded file...",
                    "progress": 90
                })
            
            file_size_mb = os.path.getsize(downloaded_file) / (1024 * 1024)
            
            result = {
                "status": "success",
                "file_path": downloaded_file,
                "file_size_mb": round(file_size_mb, 2),
                "download_directory": self.config["download_directory"]
            }
            
            if progress_callback:
                progress_callback({
                    "status": "completed", 
                    "message": f"Video downloaded successfully: {os.path.basename(downloaded_file)}",
                    "progress": 100,
                    "result": result
                })
            
            self.logger.info(f"Video downloaded successfully: {downloaded_file}")
            return json.dumps(result, indent=2)
            
        except Exception as e:
            error_msg = f"Failed to download video: {str(e)}"
            self.logger.error(error_msg)
            error_result = {"status": "error", "error": error_msg}
            
            if progress_callback:
                progress_callback({
                    "status": "error", 
                    "message": error_msg,
                    "result": error_result
                })
            
            return json.dumps(error_result)

    def download_audio(
        self, 
        url: str, 
        quality: str = "highest",
        format: str = "mp3",
        progress_callback: Optional[Callable[[dict], None]] = None
    ) -> str:
        """
        Download audio from a YouTube video to the configured download directory.
        
        Args:
            url: YouTube video URL or video ID
            quality: Audio quality preference ("highest", "lowest", or specific bitrate like "128kbps")
            format: Audio format preference ("mp3", "m4a", "wav")
            progress_callback: Optional callback for progress updates (HTTP streaming)
            
        Returns:
            JSON string with download status and file path
        """
        try:
            self.logger.info(f"Downloading audio: {url} with quality: {quality}, format: {format}")
            
            if progress_callback:
                progress_callback({
                    "status": "starting", 
                    "message": f"Starting audio download for: {url}",
                    "progress": 0
                })
            
            # Download to configured directory
            downloaded_file = self.downloader.download_audio(
                url, 
                self.config["download_directory"], 
                quality
            )
            
            if progress_callback:
                progress_callback({
                    "status": "processing", 
                    "message": "Processing downloaded audio...",
                    "progress": 90
                })
            
            file_size_mb = os.path.getsize(downloaded_file) / (1024 * 1024)
            
            result = {
                "status": "success",
                "file_path": downloaded_file,
                "file_size_mb": round(file_size_mb, 2),
                "download_directory": self.config["download_directory"],
                "format": format
            }
            
            if progress_callback:
                progress_callback({
                    "status": "completed", 
                    "message": f"Audio downloaded successfully: {os.path.basename(downloaded_file)}",
                    "progress": 100,
                    "result": result
                })
            
            self.logger.info(f"Audio downloaded successfully: {downloaded_file}")
            return json.dumps(result, indent=2)
            
        except Exception as e:
            error_msg = f"Failed to download audio: {str(e)}"
            self.logger.error(error_msg)
            error_result = {"status": "error", "error": error_msg}
            
            if progress_callback:
                progress_callback({
                    "status": "error", 
                    "message": error_msg,
                    "result": error_result
                })
            
            return json.dumps(error_result)

    def download_transcript(
        self, 
        url: str, 
        language: str = "en",
        progress_callback: Optional[Callable[[dict], None]] = None
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
            progress_callback: Optional callback for progress updates (HTTP streaming)
            
        Returns:
            JSON string with download status, file path, and full transcript content with timestamps.
            The transcript_content field contains the complete transcript text that can be analyzed directly.
        """
        try:
            self.logger.info(f"Downloading transcript: {url} with language: {language}")
            
            if progress_callback:
                progress_callback({
                    "status": "starting", 
                    "message": f"Starting transcript download for: {url}",
                    "progress": 0
                })
            
            # Download to configured directory
            downloaded_file = self.downloader.download_transcript(
                url, 
                self.config["download_directory"], 
                language
            )
            
            if progress_callback:
                progress_callback({
                    "status": "processing", 
                    "message": "Processing transcript...",
                    "progress": 80
                })
            
            file_size_mb = os.path.getsize(downloaded_file) / (1024 * 1024)
            
            # Read transcript content to include in response
            try:
                with open(downloaded_file, 'r', encoding='utf-8') as f:
                    transcript_content = f.read()
            except Exception as read_error:
                self.logger.warning(f"Could not read transcript file: {read_error}")
                transcript_content = None
            
            result = {
                "status": "success",
                "file_path": downloaded_file,
                "file_size_mb": round(file_size_mb, 2),
                "download_directory": self.config["download_directory"],
                "language": language,
                "transcript_content": transcript_content
            }
            
            if progress_callback:
                progress_callback({
                    "status": "completed", 
                    "message": f"Transcript downloaded successfully: {os.path.basename(downloaded_file)}",
                    "progress": 100,
                    "result": result
                })
            
            self.logger.info(f"Transcript downloaded successfully: {downloaded_file}")
            return json.dumps(result, indent=2)
            
        except Exception as e:
            error_msg = f"Failed to download transcript: {str(e)}"
            self.logger.error(error_msg)
            error_result = {"status": "error", "error": error_msg}
            
            if progress_callback:
                progress_callback({
                    "status": "error", 
                    "message": error_msg,
                    "result": error_result
                })
            
            return json.dumps(error_result)

    def download_video_segment(
        self,
        url: str,
        start_time: float,
        end_time: float,
        quality: str = "highest",
        progress_callback: Optional[Callable[[dict], None]] = None
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
            progress_callback: Optional callback for progress updates (HTTP streaming)
            
        Returns:
            JSON string with download status and file path to the video segment
        """
        try:
            self.logger.info(f"Downloading video segment: {url} from {start_time}s to {end_time}s")
            
            if start_time >= end_time:
                raise ValueError("Start time must be less than end time")
            
            if progress_callback:
                progress_callback({
                    "status": "starting", 
                    "message": f"Starting video segment download: {start_time}s to {end_time}s",
                    "progress": 0
                })
            
            # Download to configured directory
            downloaded_file = self.downloader.download_video_segment(
                url, 
                start_time,
                end_time,
                self.config["download_directory"], 
                quality
            )
            
            if progress_callback:
                progress_callback({
                    "status": "processing", 
                    "message": "Processing video segment...",
                    "progress": 90
                })
            
            file_size_mb = os.path.getsize(downloaded_file) / (1024 * 1024)
            
            result = {
                "status": "success",
                "file_path": downloaded_file,
                "file_size_mb": round(file_size_mb, 2),
                "download_directory": self.config["download_directory"],
                "start_time": start_time,
                "end_time": end_time,
                "duration": end_time - start_time
            }
            
            if progress_callback:
                progress_callback({
                    "status": "completed", 
                    "message": f"Video segment downloaded successfully: {os.path.basename(downloaded_file)}",
                    "progress": 100,
                    "result": result
                })
            
            self.logger.info(f"Video segment downloaded successfully: {downloaded_file}")
            return json.dumps(result, indent=2)
            
        except Exception as e:
            error_msg = f"Failed to download video segment: {str(e)}"
            self.logger.error(error_msg)
            error_result = {"status": "error", "error": error_msg}
            
            if progress_callback:
                progress_callback({
                    "status": "error", 
                    "message": error_msg,
                    "result": error_result
                })
            
            return json.dumps(error_result)

    def list_downloads(self) -> str:
        """
        List all files in the download directory.
        
        Returns:
            JSON string with list of downloaded files and their information
        """
        try:
            download_dir = self.config["download_directory"]
            
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
            self.logger.error(error_msg)
            return json.dumps({"error": error_msg})

    def get_config(self) -> str:
        """
        Get the current MCP server configuration.

        Returns:
            JSON string with current configuration settings
        """
        return json.dumps(self.config, indent=2)

    def search_videos(self, query: str, sort_by: str = "relevance") -> str:
        """
        Search YouTube for videos matching a query. Returns up to 10 results.

        Use this tool to find YouTube videos by keyword before downloading.
        The returned URLs can be passed directly to get_video_info, download_video,
        download_audio, or download_transcript.

        Args:
            query: Search query string (e.g., "python tutorial", "lo-fi music")
            sort_by: Sort order -- "relevance" (default), "date", or "views"

        Returns:
            JSON string with list of video results, each containing title, url, and duration.
        """
        try:
            self.logger.info(f"Searching YouTube for: {query} (sort_by={sort_by})")
            results = self.downloader.search_videos(query, sort_by=sort_by)
            return json.dumps({
                "status": "success",
                "query": query,
                "sort_by": sort_by,
                "count": len(results),
                "results": results
            }, indent=2)
        except Exception as e:
            error_msg = f"Failed to search YouTube: {str(e)}"
            self.logger.error(error_msg)
            return json.dumps({"status": "error", "error": error_msg})
