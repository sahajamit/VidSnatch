import os
import ssl
import subprocess
from pathlib import Path
from typing import Optional

from pytubefix import YouTube
from pytubefix.exceptions import RegexMatchError, VideoUnavailable

from .utils import retry

# Fix SSL certificate issues on macOS
ssl._create_default_https_context = ssl._create_unverified_context


class YouTubeDownloader:
    """A class to download YouTube videos and audio using pytubefix."""

    def _create_output_dir(self, path: str) -> Path:
        """Create output directory if it doesn't exist."""
        output_path = Path(path)
        output_path.mkdir(parents=True, exist_ok=True)
        return output_path

    @retry(tries=3, delay=5, backoff=2)
    def _get_youtube_object(self, url: str) -> YouTube:
        """Create and return a YouTube object from URL."""
        try:
            yt = YouTube(url)
            return yt
        except RegexMatchError:
            raise ValueError(f"Invalid YouTube URL: {url}")
        except VideoUnavailable:
            # Try switching client for some unavailable videos
            print("Video unavailable, trying TV client...")
            yt = YouTube(url, client='TV')
            return yt
        except Exception as e:
            raise IOError(f"Error accessing video: {str(e)}") from e

    def _merge_files(self, video_path: str, audio_path: str, output_path: str):
        """Merge video and audio files using ffmpeg."""
        print("Merging video and audio files...")
        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-i", video_path,
                    "-i", audio_path,
                    "-c:v", "copy",
                    "-c:a", "aac",
                    "-strict", "experimental",
                    output_path,
                ],
                check=True, capture_output=True, text=True
            )
            print("Files merged successfully.")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print("\nError: `ffmpeg` is required for merging high-quality video and audio.")
            print("Please install it and ensure it's in your system's PATH.")
            print("On macOS, you can install it with: brew install ffmpeg")
            if isinstance(e, subprocess.CalledProcessError):
                print(f"ffmpeg error:\n{e.stderr}")
            raise
        finally:
            # Clean up temporary files
            if os.path.exists(video_path):
                os.remove(video_path)
            if os.path.exists(audio_path):
                os.remove(audio_path)

    def download_video(self, url: str, output_path: str = "./downloads", quality: str = "highest") -> str:
        """Download a video from a YouTube URL."""
        self._create_output_dir(output_path)
        print(f"Downloading video from: {url}")
        yt = self._get_youtube_object(url)

        print(f"Title: {yt.title}")
        print(f"Author: {yt.author}")
        print(f"Duration: {yt.length} seconds")
        print(f"Views: {yt.views}")

        # For specific low-res, try progressive first
        is_high_quality = quality == 'highest' or any(q in quality for q in ['1080p', '1440p', '2160p', '4320p'])
        if not is_high_quality:
            stream = yt.streams.filter(res=quality, progressive=True).first()
            if stream:
                print(f"Downloading video in {quality} quality (progressive)...")
                return stream.download(output_path=output_path)

        # Handle adaptive streams for high quality
        print(f"Searching for {quality} quality video stream (adaptive)...")
        video_stream = yt.streams.filter(adaptive=True, file_extension='mp4').order_by('resolution').desc().first() if quality == 'highest' else yt.streams.filter(res=quality, adaptive=True, file_extension='mp4').first()

        if not video_stream:
            print(f"Could not find adaptive stream for {quality}, falling back to highest resolution progressive stream.")
            video_stream = yt.streams.get_highest_resolution()
            if not video_stream:
                raise ValueError("No downloadable video streams found.")
            print(f"Downloading video in {video_stream.resolution} quality...")
            return video_stream.download(output_path=output_path)

        # If the selected stream is progressive, no merge is needed
        if video_stream.is_progressive:
            print(f"Downloading video in {video_stream.resolution} quality (progressive)...")
            return video_stream.download(output_path=output_path)

        audio_stream = yt.streams.get_audio_only()
        if not audio_stream:
            raise ValueError("No audio stream found to merge.")

        print(f"Downloading video: {video_stream.resolution} ({video_stream.filesize / 1e6:.2f}MB)")
        video_filepath = video_stream.download(output_path=output_path, filename_prefix="video_")

        print(f"Downloading audio: {audio_stream.abr} ({audio_stream.filesize / 1e6:.2f}MB)")
        audio_filepath = audio_stream.download(output_path=output_path, filename_prefix="audio_")

        final_filename = Path(video_filepath).name.replace("video_", "")
        output_filepath = str(Path(output_path) / final_filename)

        self._merge_files(video_filepath, audio_filepath, output_filepath)
        return output_filepath

    def download_audio(self, url: str, output_path: str = "./downloads", quality: str = "highest") -> str:
        """Download audio from a YouTube URL and convert to MP3."""
        self._create_output_dir(output_path)
        print(f"Downloading audio from: {url}")
        yt = self._get_youtube_object(url)
        print(f"Title: {yt.title}")
        print(f"Author: {yt.author}")
        print(f"Duration: {yt.length} seconds")

        abr = quality.replace('kbps', '') if isinstance(quality, str) else quality
        if quality == "highest":
            audio_stream = yt.streams.get_audio_only()
        else:
            audio_stream = yt.streams.filter(only_audio=True, abr=abr).first()

        if not audio_stream:
            # Fallback to highest if specific quality not found
            audio_stream = yt.streams.get_audio_only()
            if not audio_stream:
                raise ValueError(f"No audio stream available for quality '{quality}'.")
            print(f"Quality '{quality}' not found, falling back to highest available: {audio_stream.abr}")

        print("Downloading audio...")
        downloaded_file = audio_stream.download(output_path=output_path)
        
        base, _ = os.path.splitext(downloaded_file)
        mp3_file = base + '.mp3'

        print(f"Converting {downloaded_file} to MP3...")
        try:
            subprocess.run([
                'ffmpeg',
                '-i', downloaded_file,
                '-vn',
                '-ar', '44100',
                '-ac', '2',
                '-b:a', (audio_stream.abr.replace('kbps', 'k') if audio_stream.abr else '192k'),
                mp3_file
            ], check=True, capture_output=True, text=True)
            
            # Remove the original downloaded file
            os.remove(downloaded_file)
            
            print(f"Audio downloaded and converted successfully: {mp3_file}")
            return mp3_file
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"\nError during MP3 conversion. ffmpeg might be missing or an error occurred.")
            if isinstance(e, subprocess.CalledProcessError):
                print(f"ffmpeg error:\n{e.stderr}")
            # Fallback to renaming if conversion fails
            os.rename(downloaded_file, mp3_file)
            return mp3_file

    def get_video_info(self, url: str) -> dict:
        """Get information and available streams for a YouTube video."""
        """Get and print information about a YouTube video."""
        print("Getting video information...")
        yt = self._get_youtube_object(url)

        video_streams = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc()
        audio_streams = yt.streams.filter(only_audio=True).order_by('abr').desc()

        video_qualities = sorted(list(set([s.resolution for s in video_streams if s.resolution])), key=lambda x: int(x.replace('p', '')), reverse=True)
        audio_qualities = sorted(list(set([s.abr for s in audio_streams if s.abr])), key=lambda x: int(x.replace('kbps', '')), reverse=True)

        info = {
            'title': yt.title,
            'author': yt.author,
            'duration': yt.length,
            'views': yt.views,
            'publish_date': str(yt.publish_date) if yt.publish_date else None,
            'thumbnail': yt.thumbnail_url,
            'video_qualities': ['highest'] + video_qualities + ['lowest'],
            'audio_qualities': ['highest'] + audio_qualities + ['lowest'],
        }
        return info
