#!/usr/bin/env python3
"""
VidSnatch - Futuristic YouTube Video Downloader Web App
"""

import io
import os
import tempfile
from flask import Flask, request, jsonify, send_file, render_template_string
from flask_cors import CORS

from youtube_downloader import YouTubeDownloader

app = Flask(__name__, static_folder='static', static_url_path='/static')
CORS(app)

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
            
        # Get YouTube object to extract info
        yt = downloader._get_youtube_object(url)
        
        # Get video thumbnail URL
        thumbnail_url = yt.thumbnail_url if hasattr(yt, 'thumbnail_url') else None
        
        video_info = {
            'url': url,
            'title': yt.title,
            'author': yt.author,
            'duration': yt.length,
            'views': yt.views,
            'thumbnail': thumbnail_url,
            'publish_date': str(yt.publish_date) if yt.publish_date else None
        }
        
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
        
        if not url:
            return jsonify({'error': 'No URL provided'}), 400
            
        # Create temporary directory for download
        with tempfile.TemporaryDirectory() as temp_dir:
            # Download audio
            downloaded_file = downloader.download_audio(url, temp_dir)
            
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
    print("🚀 Starting VidSnatch server...")
    print("📱 Open http://localhost:8080 in your browser")
    app.run(debug=True, host='0.0.0.0', port=8080)
