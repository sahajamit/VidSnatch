<div align="center">
  <img src="static/vidsnatch-logo.png" alt="VidSnatch Logo" width="200">
  
  # VidSnatch 🚀
  
  *The future of YouTube video downloading*
</div>

VidSnatch is a futuristic YouTube video downloader with both a sleek web interface and powerful command-line tools. Built for the next generation with a stunning UI that appeals to Gen Z and Gen Alpha users.

## Features

- 🌟 **Futuristic Web Interface**: Beautiful glassmorphism UI with aurora background
- 📱 **Mobile-First Design**: Responsive design that works on all devices
- 🎥 **High-Quality Downloads**: Support for up to 4K video downloads with automatic audio merging
- 🎵 **Audio Extraction**: Download audio-only files as MP3
- 📝 **Transcript Download**: Extract video transcripts with timestamps
- ✂️ **Video Trimming**: Download specific segments of videos with precise timestamp control
- ⚡ **Real-Time Processing**: Live video info fetching and download progress
- 💻 **Command-Line Interface**: Powerful CLI for automation and scripting
- 🚀 **Modern Tech Stack**: Built with UV, Flask, and Tailwind CSS

## Installation

Make sure you have UV installed. If not, install it first:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then install the project dependencies:

```bash
uv sync
```

## Testing

To run the test suite:

```bash
# Run all tests
uv run python -m pytest tests/ -v

# Run specific test file
uv run python -m pytest tests/test_transcript.py -v
```

## Usage

### 🐳 Running with Docker

You can run VidSnatch using the pre-built Docker image from Docker Hub.

1.  **Pull the Docker image:**
    ```bash
    docker pull sahajamit/vidsnatch:0.3
    ```

2.  **Run the Docker container:**
    ```bash
    docker run -p 8080:8080 sahajamit/vidsnatch:0.3
    ```

3.  **Open your browser:**
    Navigate to `http://localhost:8080`

### 🌐 Web Interface (Recommended)

VidSnatch features a stunning futuristic web interface that's perfect for everyday use:

![VidSnatch Web Interface](vidsnatch_ui_screenshot.png)

#### Launch the Web App

1. **Start the server:**
   ```bash
   uv run python web_app.py
   ```

2. **Open your browser:**
   Navigate to `http://localhost:8080`

3. **Start downloading:**
   - Paste any YouTube URL into the input field
   - Click "Snatch" to fetch video info
   - Select your desired video quality or transcript language
   - Click "Download Video", "Download MP3", or "Download Transcript"

#### ✂️ Video Trimming Feature

VidSnatch now supports precise video trimming to download specific segments:

1. **Load a video:** Paste a YouTube URL and click "Snatch Video Info"
2. **Navigate to Trim Video section:** Scroll down to the "✂️ Trim Video" panel
3. **Select time range using sliders:**
   - **Start Time Slider:** Drag to set the beginning of your segment
   - **End Time Slider:** Drag to set the end of your segment
   - **Visual Timeline:** See your selection highlighted on the progress bar
   - **Time Display:** View exact start/end times and segment duration
4. **Choose quality:** Select video quality for the trimmed segment
5. **Download:** Click "Download Trimmed Video" to get your custom segment

**Features:**
- **Precise Control:** Frame-accurate trimming with visual feedback
- **Real-time Preview:** See exact timestamps and duration as you adjust
- **Quality Selection:** Choose from available video qualities
- **Smart Validation:** Prevents invalid time ranges automatically

The web interface features:
- **Real-time video info fetching**
- **Quality selection with visual feedback**
- **Video trimming with interactive sliders**
- **Transcript download with timestamps**
- **Fancy loading animations**
- **Automatic file downloads**
- **Mobile-responsive design**

### 💻 As a Python module

```python
from youtube_downloader import YouTubeDownloader

# Create downloader instance
downloader = YouTubeDownloader()

# Download video
downloader.download_video("https://www.youtube.com/watch?v=VIDEO_ID", output_path="./downloads")

# Download audio only
downloader.download_audio("https://www.youtube.com/watch?v=VIDEO_ID", output_path="./downloads")

# Download transcript with timestamps
downloader.download_transcript("https://www.youtube.com/watch?v=VIDEO_ID", output_path="./downloads")

# Download a trimmed video segment (start_time and end_time in seconds)
downloader.download_video_segment("https://www.youtube.com/watch?v=VIDEO_ID", 
                                 start_time=30, end_time=120, 
                                 output_path="./downloads", quality="720p")
```

### ⚡ Command Line Interface

VidSnatch also provides a powerful command-line interface for automation and scripting:

**Download a Video**

To download a video at the highest available resolution, run:
```bash
uv run python -m youtube_downloader --url "https://www.youtube.com/watch?v=VIDEO_ID" --type video
```

To save the video to a specific folder, use the `--output` flag:
```bash
uv run python -m youtube_downloader --url "https://www.youtube.com/watch?v=VIDEO_ID" --type video --output ./my_videos
```

**Control Video Quality**

You can control the video quality using the `--quality` flag. Here are the available options:

-   **`highest`**: Automatically selects the best available resolution. For qualities above 720p, it will download and merge separate video and audio files to provide the best quality.
-   **`lowest`**: Selects the lowest available resolution.
-   **Specific Resolutions**: You can provide a specific resolution string. Common options include:
    -   `144p`
    -   `240p`
    -   `360p`
    -   `480p`
    -   `720p`
    -   `1080p` (Full HD)
    -   `1440p` (2K)
    -   `2160p` (4K)

*Note: The availability of these resolutions depends on the original video uploaded to YouTube.*

```bash
# Download in 720p
uv run python -m youtube_downloader --url "https://www.youtube.com/watch?v=-8A1iyh1-CM" --type video --quality 720p

# Download in lowest quality
uv run python -m youtube_downloader --url "https://www.youtube.com/watch?v=-8A1iyh1-CM" --type video --quality lowest
```

**Download Audio Only**

To download only the audio from a video, use `--type audio`. The audio will be saved as an MP3 file.

```bash
uv run python -m youtube_downloader --url "https://www.youtube.com/watch?v=-8A1iyh1-CM" --type audio --quality 720p --output ./my_audio
```

**Get Video Information**

To see information about a video without downloading it, use `--type info`:
```bash
uv run python -m youtube_downloader --url "https://www.youtube.com/watch?v=VIDEO_ID" --type info
```

### Building and Publishing Docker Images

To build and push multi-platform Docker images:

1. **Create or use a buildx builder:**
   ```bash
   # Option 1: Create new builder (remove existing if needed)
   docker buildx rm multiplatform 2>/dev/null || true
   docker buildx create --name multiplatform --use
   
   # Option 2: Use existing builder
   docker buildx use multiplatform
   
   # Option 3: Use default builder
   docker buildx use default
   ```

2. **Build and push for multiple platforms:**
   ```bash
   docker buildx build --platform linux/amd64,linux/arm64 -t sahajamit/vidsnatch:latest -t sahajamit/vidsnatch:0.3 --push .
   ```

3. **Build for linux/amd64 only (cloud platform compatible):**
   ```bash
   docker buildx build --platform linux/amd64 -t sahajamit/vidsnatch:latest -t sahajamit/vidsnatch:0.3 --push .
   ```

4. **Clean up Docker system (optional):**
   ```bash
   docker system prune -a
   ```

## Requirements

- Python 3.8+
- pytubefix library
- youtube-transcript-api library
- UV package manager
- ffmpeg (for audio conversion and video merging)

## License

MIT License