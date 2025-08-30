#!/usr/bin/env python3
"""
VidSnatch - Futuristic YouTube Video Downloader Web App
"""

import io
import os
import tempfile
import logging
import re
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from src import YouTubeDownloader
from src.logger import setup_logger, get_logger

app = FastAPI(title="VidSnatch", description="Futuristic YouTube Video Downloader")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup logging
logger = setup_logger("vidsnatch")
downloader = YouTubeDownloader()

def sanitize_filename_for_header(filename):
    """
    Sanitize filename for HTTP Content-Disposition header by removing/replacing
    non-ASCII characters that can't be encoded in latin-1.
    """
    # Remove emojis and other non-ASCII characters
    sanitized = re.sub(r'[^\x00-\x7F]+', '', filename)
    # Replace multiple spaces with single space and strip
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()
    # If filename becomes empty or too short, provide a default
    if len(sanitized) < 3:
        name, ext = os.path.splitext(filename)
        sanitized = f"download{ext}"
    return sanitized

# Pydantic models for request validation
class VideoInfoRequest(BaseModel):
    url: str

class VideoDownloadRequest(BaseModel):
    url: str
    quality: str = "highest"

class AudioDownloadRequest(BaseModel):
    url: str
    quality: str = "highest"

class TranscriptDownloadRequest(BaseModel):
    url: str
    language: str = "en"

class VideoSegmentRequest(BaseModel):
    url: str
    start_time: float
    end_time: float
    quality: str = "highest"

@app.get("/favicon.ico")
async def favicon():
    """Serve the favicon"""
    return FileResponse("static/favicon_io/favicon.ico")

@app.get("/static/favicon_io/favicon-32x32.png")
async def favicon_32():
    """Serve the 32x32 favicon"""
    return FileResponse("static/favicon_io/favicon-32x32.png")

@app.get("/static/favicon_io/favicon-16x16.png")
async def favicon_16():
    """Serve the 16x16 favicon"""
    return FileResponse("static/favicon_io/favicon-16x16.png")

@app.get("/static/favicon_io/apple-touch-icon.png")
async def apple_touch_icon():
    """Serve the apple touch icon"""
    return FileResponse("static/favicon_io/apple-touch-icon.png")

@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve the main HTML interface"""
    with open('static/index.html', 'r', encoding='utf-8') as f:
        return f.read()

@app.post("/api/video-info")
async def get_video_info(request: VideoInfoRequest):
    """Get video information from YouTube URL"""
    try:
        if not request.url:
            raise HTTPException(status_code=400, detail="No URL provided")
            
        # Get video info using the downloader's method
        video_info = downloader.get_video_info(request.url)
        return video_info
        
    except ValueError as e:
        # Handle specific YouTube URL/ID errors
        error_msg = str(e)
        raise HTTPException(status_code=400, detail=error_msg)
    except Exception as e:
        logger.error(f"Video info error: {str(e)}")
        error_msg = str(e)
        # Check if it's a YouTube-related error that should be 400 instead of 500
        if any(keyword in error_msg.lower() for keyword in ['unavailable', 'private', 'deleted', 'not found', 'invalid', 'restricted']):
            raise HTTPException(status_code=400, detail=f"Video error: {error_msg}")
        else:
            raise HTTPException(status_code=500, detail=f"Failed to get video information: {error_msg}")

@app.post("/api/download-video")
async def download_video(request: VideoDownloadRequest):
    """Download video file"""
    try:
        if not request.url:
            raise HTTPException(status_code=400, detail="No URL provided")
            
        # Create temporary directory for download
        with tempfile.TemporaryDirectory() as temp_dir:
            # Download video
            downloaded_file = downloader.download_video(request.url, temp_dir, request.quality)
            
            # Get filename for response
            filename = os.path.basename(downloaded_file)
            
            # Read file into memory
            with open(downloaded_file, 'rb') as f:
                file_data = f.read()
            
            # Create BytesIO object
            file_obj = io.BytesIO(file_data)
            file_obj.seek(0)
            
            return StreamingResponse(
                io.BytesIO(file_data),
                media_type='video/mp4',
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/download-audio")
async def download_audio(request: AudioDownloadRequest):
    """Download audio file"""
    try:
        logger.info(f"Audio download request: URL={request.url}, Quality={request.quality}")
        
        if not request.url:
            raise HTTPException(status_code=400, detail="No URL provided")
            
        # Create temporary directory for download
        with tempfile.TemporaryDirectory() as temp_dir:
            # Download audio
            downloaded_file = downloader.download_audio(request.url, temp_dir, request.quality)
            
            # Get filename for response
            filename = os.path.basename(downloaded_file)
            safe_filename = sanitize_filename_for_header(filename)
            
            # Read file into memory
            with open(downloaded_file, 'rb') as f:
                file_data = f.read()
            
            return StreamingResponse(
                io.BytesIO(file_data),
                media_type='audio/mpeg',
                headers={"Content-Disposition": f"attachment; filename={safe_filename}"}
            )
            
    except Exception as e:
        logger.error(f"Audio download error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/download-transcript")
async def download_transcript(request: TranscriptDownloadRequest):
    """Download transcript file"""
    try:
        if not request.url:
            raise HTTPException(status_code=400, detail="No URL provided")
            
        # Create temporary directory for download
        with tempfile.TemporaryDirectory() as temp_dir:
            # Download transcript
            downloaded_file = downloader.download_transcript(request.url, temp_dir, request.language)
            
            # Get video info
            video_info = downloader.get_video_info(request.url)
            
            # Get filename for response
            filename = f"{video_info['title']}.txt"
            safe_filename = sanitize_filename_for_header(filename)
            
            # Read file into memory
            with open(downloaded_file, 'r', encoding='utf-8') as f:
                file_data = f.read()
            
            return StreamingResponse(
                io.BytesIO(file_data.encode('utf-8')),
                media_type='text/plain',
                headers={"Content-Disposition": f"attachment; filename={safe_filename}"}
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/download-video-segment")
async def download_video_segment(request: VideoSegmentRequest):
    """Download a trimmed video segment"""
    try:
        if not request.url:
            raise HTTPException(status_code=400, detail="No URL provided")
        if request.start_time >= request.end_time:
            raise HTTPException(status_code=400, detail="Start time must be less than end time")
            
        # Create temporary directory for download
        with tempfile.TemporaryDirectory() as temp_dir:
            # Download video segment
            downloaded_file = downloader.download_video_segment(
                request.url, request.start_time, request.end_time, temp_dir, request.quality
            )
            
            # Get filename for response
            filename = os.path.basename(downloaded_file)
            safe_filename = sanitize_filename_for_header(filename)
            
            # Read file into memory
            with open(downloaded_file, 'rb') as f:
                file_data = f.read()
            
            return StreamingResponse(
                io.BytesIO(file_data),
                media_type='video/mp4',
                headers={"Content-Disposition": f"attachment; filename={safe_filename}"}
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/placeholder-thumb")
async def placeholder_thumbnail():
    """Serve a placeholder thumbnail when video thumbnail is not available"""
    # Return a simple SVG placeholder
    svg_content = '''
    <svg width="320" height="180" xmlns="http://www.w3.org/2000/svg">
        <rect width="320" height="180" fill="#1F1A33"/>
        <text x="160" y="90" font-family="Arial" font-size="14" fill="#00FFFF" text-anchor="middle">
            Video Thumbnail
        </text>
    </svg>
    '''
    return StreamingResponse(
        io.BytesIO(svg_content.encode()),
        media_type='image/svg+xml'
    )

def main():
    """Main entry point for web application"""
    import uvicorn
    logger.info("🚀 Starting VidSnatch web server...")
    logger.info("📱 Open http://localhost:8080 in your browser")
    uvicorn.run(app, host='0.0.0.0', port=8080)

if __name__ == '__main__':
    main()
