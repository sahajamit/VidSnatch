#!/usr/bin/env python3
"""
VidSnatch - Futuristic YouTube Video Downloader Web App
"""

import io
import os
import tempfile
import logging
from flask import Flask, render_template, request, jsonify, send_file
from src import YouTubeDownloader
from src.logger import setup_logger, get_logger
from flask_cors import CORS

app = Flask(__name__, static_folder='static', static_url_path='/static')
CORS(app)

# Setup logging
logger = setup_logger("vidsnatch", level=logging.INFO)
downloader = YouTubeDownloader()

@app.route('/')
def index():
    """Serve the main HTML interface"""
    with open('static/index.html', 'r', encoding='utf-8') as f:
        return f.read()

@app.route('/api/video-info', methods=['POST'])
def get_video_info():
    """Get video information from YouTube URL"""
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'No URL provided'}), 400
            
        # Get video info using the downloader's method
        video_info = downloader.get_video_info(url)
        return jsonify(video_info)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download-video', methods=['POST'])
def download_video():
    """Download video file"""
    try:
        data = request.get_json()
        url = data.get('url')
        quality = data.get('quality', 'highest')
        
        if not url:
            return jsonify({'error': 'No URL provided'}), 400
            
        # Create temporary directory for download
        with tempfile.TemporaryDirectory() as temp_dir:
            # Download video
            downloaded_file = downloader.download_video(url, temp_dir, quality)
            
            # Get filename for response
            filename = os.path.basename(downloaded_file)
            
            # Read file into memory
            with open(downloaded_file, 'rb') as f:
                file_data = f.read()
            
            # Create BytesIO object
            file_obj = io.BytesIO(file_data)
            file_obj.seek(0)
            
            return send_file(
                file_obj,
                as_attachment=True,
                download_name=filename,
                mimetype='video/mp4'
            )
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download-audio', methods=['POST'])
def download_audio():
    """Download audio file"""
    try:
        data = request.get_json()
        url = data.get('url')
        quality = data.get('quality', 'highest')
        
        print(f"Audio download request: URL={url}, Quality={quality}")
        
        if not url:
            return jsonify({'error': 'No URL provided'}), 400
            
        # Create temporary directory for download
        with tempfile.TemporaryDirectory() as temp_dir:
            # Download audio
            downloaded_file = downloader.download_audio(url, temp_dir, quality)
            
            # Get filename for response
            filename = os.path.basename(downloaded_file)
            
            # Read file into memory
            with open(downloaded_file, 'rb') as f:
                file_data = f.read()
            
            # Create BytesIO object
            file_obj = io.BytesIO(file_data)
            file_obj.seek(0)
            
            return send_file(
                file_obj,
                as_attachment=True,
                download_name=filename,
                mimetype='audio/mpeg'
            )
            
    except Exception as e:
        print(f"Audio download error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/download-transcript', methods=['POST'])
def download_transcript():
    """Download transcript file"""
    try:
        data = request.get_json()
        url = data.get('url')
        language = data.get('language', 'en')
        
        if not url:
            return jsonify({'error': 'No URL provided'}), 400
            
        # Create temporary directory for download
        with tempfile.TemporaryDirectory() as temp_dir:
            # Download transcript
            downloaded_file = downloader.download_transcript(url, temp_dir, language)
            
            # Get filename for response
            filename = os.path.basename(downloaded_file)
            
            # Read file into memory
            with open(downloaded_file, 'r', encoding='utf-8') as f:
                file_data = f.read()
            
            # Create BytesIO object
            file_obj = io.BytesIO(file_data.encode('utf-8'))
            file_obj.seek(0)
            
            return send_file(
                file_obj,
                as_attachment=True,
                download_name=filename,
                mimetype='text/plain'
            )
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download-video-segment', methods=['POST'])
def download_video_segment():
    """Download a trimmed video segment"""
    try:
        data = request.get_json()
        url = data.get('url')
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        quality = data.get('quality', 'highest')
        
        if not url:
            return jsonify({'error': 'No URL provided'}), 400
        if start_time is None or end_time is None:
            return jsonify({'error': 'Start time and end time are required'}), 400
        if start_time >= end_time:
            return jsonify({'error': 'Start time must be less than end time'}), 400
            
        # Create temporary directory for download
        with tempfile.TemporaryDirectory() as temp_dir:
            # Download video segment
            downloaded_file = downloader.download_video_segment(url, float(start_time), float(end_time), temp_dir, quality)
            
            # Get filename for response
            filename = os.path.basename(downloaded_file)
            
            # Read file into memory
            with open(downloaded_file, 'rb') as f:
                file_data = f.read()
            
            # Create BytesIO object
            file_obj = io.BytesIO(file_data)
            file_obj.seek(0)
            
            return send_file(
                file_obj,
                as_attachment=True,
                download_name=filename,
                mimetype='video/mp4'
            )
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/placeholder-thumb')
def placeholder_thumbnail():
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
    return svg_content, 200, {'Content-Type': 'image/svg+xml'}

if __name__ == '__main__':
    logger.info("🚀 Starting VidSnatch server...")
    logger.info("📱 Open http://localhost:8080 in your browser")
    app.run(host='0.0.0.0', port=8080, debug=True)
