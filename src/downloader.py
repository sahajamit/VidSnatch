import os
import ssl
import subprocess
import re
import tempfile
from pathlib import Path
from typing import Optional

from pytubefix import YouTube
from pytubefix.exceptions import RegexMatchError, VideoUnavailable
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound, VideoUnavailable as TranscriptVideoUnavailable

from .utils import retry
from .logger import get_logger

# Fix SSL certificate issues on macOS
ssl._create_default_https_context = ssl._create_unverified_context


class YouTubeDownloader:
    """A class to download YouTube videos and audio using pytubefix."""

    def __init__(self):
        """Initialize the downloader with logger."""
        self.logger = get_logger("vidsnatch.downloader")

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
            self.logger.warning("Video unavailable, trying TV client...")
            yt = YouTube(url, client='TV')
            return yt
        except Exception as e:
            raise IOError(f"Error accessing video: {str(e)}") from e

    def _merge_files(self, video_path: str, audio_path: str, output_path: str):
        """Merge video and audio files using ffmpeg."""
        self.logger.info("Merging video and audio files...")
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
            self.logger.info("Files merged successfully.")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            self.logger.error("Error: `ffmpeg` is required for merging high-quality video and audio.")
            self.logger.error("Please install it and ensure it's in your system's PATH.")
            self.logger.error("On macOS, you can install it with: brew install ffmpeg")
            if isinstance(e, subprocess.CalledProcessError):
                self.logger.error(f"ffmpeg error: {e.stderr}")
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
        self.logger.info(f"Downloading video from: {url}")
        yt = self._get_youtube_object(url)

        self.logger.info(f"Title: {yt.title}")
        self.logger.info(f"Author: {yt.author}")
        self.logger.info(f"Duration: {yt.length} seconds")
        self.logger.info(f"Views: {yt.views}")

        # For specific low-res, try progressive first
        is_high_quality = quality == 'highest' or any(q in quality for q in ['1080p', '1440p', '2160p', '4320p'])
        if not is_high_quality:
            stream = yt.streams.filter(res=quality, progressive=True).first()
            if stream:
                self.logger.info(f"Downloading video in {quality} quality (progressive)...")
                return stream.download(output_path=output_path)

        # Handle adaptive streams for high quality
        self.logger.info(f"Searching for {quality} quality video stream (adaptive)...")
        video_stream = yt.streams.filter(adaptive=True, file_extension='mp4').order_by('resolution').desc().first() if quality == 'highest' else yt.streams.filter(res=quality, adaptive=True, file_extension='mp4').first()

        if not video_stream:
            self.logger.warning(f"Could not find adaptive stream for {quality}, falling back to highest resolution progressive stream.")
            video_stream = yt.streams.get_highest_resolution()
            if not video_stream:
                raise ValueError("No downloadable video streams found.")
            self.logger.info(f"Downloading video in {video_stream.resolution} quality...")
            return video_stream.download(output_path=output_path)

        # If the selected stream is progressive, no merge is needed
        if video_stream.is_progressive:
            self.logger.info(f"Downloading video in {video_stream.resolution} quality (progressive)...")
            return video_stream.download(output_path=output_path)

        audio_stream = yt.streams.get_audio_only()
        if not audio_stream:
            raise ValueError("No audio stream found to merge.")

        self.logger.info(f"Downloading video: {video_stream.resolution} ({video_stream.filesize / 1e6:.2f}MB)")
        video_filepath = video_stream.download(output_path=output_path, filename_prefix="video_")

        self.logger.info(f"Downloading audio: {audio_stream.abr} ({audio_stream.filesize / 1e6:.2f}MB)")
        audio_filepath = audio_stream.download(output_path=output_path, filename_prefix="audio_")

        final_filename = Path(video_filepath).name.replace("video_", "")
        output_filepath = str(Path(output_path) / final_filename)

        self._merge_files(video_filepath, audio_filepath, output_filepath)
        return output_filepath

    def download_audio(self, url: str, output_path: str = "./downloads", quality: str = "highest") -> str:
        """Download audio from a YouTube URL and convert to MP3."""
        self._create_output_dir(output_path)
        self.logger.info(f"Downloading audio from: {url}")
        yt = self._get_youtube_object(url)
        self.logger.info(f"Title: {yt.title}")
        self.logger.info(f"Author: {yt.author}")
        self.logger.info(f"Duration: {yt.length} seconds")

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
            self.logger.warning(f"Quality '{quality}' not found, falling back to highest available: {audio_stream.abr}")

        self.logger.info("Downloading audio...")
        downloaded_file = audio_stream.download(output_path=output_path)
        
        base, _ = os.path.splitext(downloaded_file)
        mp3_file = base + '.mp3'

        self.logger.info(f"Converting {downloaded_file} to MP3...")
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
            
            self.logger.info(f"Audio downloaded and converted successfully: {mp3_file}")
            return mp3_file
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            self.logger.error("Error during MP3 conversion. ffmpeg might be missing or an error occurred.")
            if isinstance(e, subprocess.CalledProcessError):
                self.logger.error(f"ffmpeg error: {e.stderr}")
            # Fallback to renaming if conversion fails
            os.rename(downloaded_file, mp3_file)
            return mp3_file

    def get_video_info(self, url: str) -> dict:
        """Get information and available streams for a YouTube video."""
        """Get and print information about a YouTube video."""
        self.logger.info("Getting video information...")
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

    def _extract_video_id(self, url: str) -> str:
        """Extract video ID from YouTube URL."""
        # Handle various YouTube URL formats with more specific patterns
        patterns = [
            r'(?:youtube\.com\/watch\?v=)([0-9A-Za-z_-]{11})',  # youtube.com/watch?v=
            r'(?:youtube\.com\/embed\/)([0-9A-Za-z_-]{11})',    # youtube.com/embed/
            r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})',              # youtu.be/
            r'(?:youtube\.com\/v\/)([0-9A-Za-z_-]{11})',        # youtube.com/v/
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        raise ValueError(f"Could not extract video ID from URL: {url}")

    def download_transcript(self, url: str, output_path: str = "./downloads", language: str = 'en') -> str:
        """Download transcript from a YouTube video."""
        self._create_output_dir(output_path)
        self.logger.info(f"Downloading transcript from: {url}")
        
        try:
            # Extract video ID from URL
            video_id = self._extract_video_id(url)
            self.logger.info(f"Video ID: {video_id}")
            
            # Get video info for filename
            yt = self._get_youtube_object(url)
            title = yt.title
            self.logger.info(f"Title: {title}")
            
            # Try to get transcript using the correct API
            try:
                api = YouTubeTranscriptApi()
                transcript_list_obj = api.list(video_id)
                
                # Get available transcript languages
                available_transcripts = list(transcript_list_obj)
                
                if not available_transcripts:
                    raise NoTranscriptFound(video_id)
                
                # Select transcript based on language preference
                selected_transcript = None
                if language == 'auto':
                    # Use first available transcript
                    selected_transcript = available_transcripts[0]
                elif language == 'en':
                    # Try to find English transcript
                    for transcript in available_transcripts:
                        if transcript.language_code == 'en':
                            selected_transcript = transcript
                            break
                    # Fallback to first available if English not found
                    if not selected_transcript:
                        selected_transcript = available_transcripts[0]
                else:
                    # Try to find specific language
                    for transcript in available_transcripts:
                        if transcript.language_code == language:
                            selected_transcript = transcript
                            break
                    # Fallback to first available if specific language not found
                    if not selected_transcript:
                        selected_transcript = available_transcripts[0]
                
                # Fetch the transcript data using the transcript object directly
                transcript_list = selected_transcript.fetch()
                self.logger.info(f"Found transcript in {selected_transcript.language_code} ({selected_transcript.language})")
                    
            except (NoTranscriptFound, TranscriptsDisabled) as e:
                self.logger.error(f"No transcript found: {e}")
                raise ValueError("Transcript not available for this video. This might be because:\n- The video does not have captions\n- The captions are disabled by the creator\n- The video is private or restricted")
            except Exception as e:
                self.logger.error(f"Failed to get transcript: {e}")
                raise IOError(f"Error accessing transcript: {str(e)}")
            
            # Combine transcript text with timestamps
            full_transcript = ""
            for item in transcript_list:
                # Handle the new transcript object format
                if hasattr(item, 'text') and hasattr(item, 'start'):
                    # Format timestamp as M:SS or MM:SS
                    start_time = item.start
                    minutes = int(start_time // 60)
                    seconds = int(start_time % 60)
                    timestamp = f"[{minutes:02d}:{seconds:02d}]"
                    full_transcript += f"{timestamp} {item.text}\n"
                elif isinstance(item, dict) and 'text' in item and 'start' in item:
                    # Format timestamp for dictionary format
                    start_time = item['start']
                    minutes = int(start_time // 60)
                    seconds = int(start_time % 60)
                    timestamp = f"[{minutes:02d}:{seconds:02d}]"
                    full_transcript += f"{timestamp} {item['text']}\n"
                else:
                    # Fallback without timestamp
                    text = item.text if hasattr(item, 'text') else str(item)
                    full_transcript += f"{text}\n"
            
            # Clean up the transcript text
            full_transcript = full_transcript.strip()
            
            # Create filename
            safe_title = re.sub(r'[^\w\s-]', '', title).strip()
            safe_title = re.sub(r'[-\s]+', '-', safe_title)
            filename = f"{safe_title}_transcript.txt"
            filepath = os.path.join(output_path, filename)
            
            # Write transcript to file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"Transcript for: {title}\n")
                f.write(f"Video URL: {url}\n")
                f.write(f"Video ID: {video_id}\n")
                f.write(f"Language: {selected_transcript.language_code} ({selected_transcript.language})\n")
                f.write(f"Format: [MM:SS] Text with timestamps\n")
                f.write("=" * 60 + "\n\n")
                f.write(full_transcript)
            
            self.logger.info(f"Transcript saved successfully: {filepath}")
            return filepath
            
        except (TranscriptsDisabled, NoTranscriptFound) as e:
            error_msg = f"Transcript not available for this video. This might be because:\n" \
                       f"- The video does not have captions\n" \
                       f"- The captions are disabled by the creator\n" \
                       f"- The video is private or restricted"
            self.logger.error(error_msg)
            raise ValueError(error_msg) from e
        except Exception as e:
            error_msg = f"Error downloading transcript: {str(e)}"
            self.logger.error(error_msg)
            raise IOError(error_msg) from e

    def _format_timestamp(self, seconds: float) -> str:
        """Convert seconds to HH:MM:SS format for FFmpeg."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def download_video_segment(self, url: str, start_time: float, end_time: float, 
                             output_path: str = "./downloads", quality: str = "highest") -> str:
        """Download and trim a specific segment of a video."""
        self._create_output_dir(output_path)
        self.logger.info(f"Downloading video segment from {start_time}s to {end_time}s")
        
        # Validate timestamps
        if start_time >= end_time:
            raise ValueError("Start time must be less than end time")
        if start_time < 0:
            raise ValueError("Start time cannot be negative")
            
        # Get video info first to validate duration
        yt = self._get_youtube_object(url)
        video_duration = yt.length
        
        if end_time > video_duration:
            self.logger.warning(f"Warning: End time ({end_time}s) exceeds video duration ({video_duration}s). Using video duration.")
            end_time = video_duration
            
        self.logger.info(f"Video duration: {video_duration}s, trimming from {start_time}s to {end_time}s")
        
        # Create temporary directory for full video download
        with tempfile.TemporaryDirectory() as temp_dir:
            # Download full video first
            self.logger.info("Downloading full video for trimming...")
            full_video_path = self.download_video(url, temp_dir, quality)
            
            # Create output filename with segment info
            safe_title = re.sub(r'[^\w\s-]', '', yt.title).strip()
            safe_title = re.sub(r'[-\s]+', '-', safe_title)
            
            start_str = self._format_timestamp(start_time).replace(':', '-')
            end_str = self._format_timestamp(end_time).replace(':', '-')
            segment_filename = f"{safe_title}_segment_{start_str}_to_{end_str}.mp4"
            segment_filepath = os.path.join(output_path, segment_filename)
            
            # Format timestamps for FFmpeg
            start_timestamp = self._format_timestamp(start_time)
            duration = end_time - start_time
            duration_timestamp = self._format_timestamp(duration)
            
            self.logger.info(f"Trimming video segment: {start_timestamp} for {duration_timestamp}")
            
            try:
                # Use FFmpeg with proper video trimming - seek before input for accuracy
                subprocess.run([
                    "ffmpeg",
                    "-y",  # Overwrite output file if it exists
                    "-ss", start_timestamp,  # Seek to start time before input (more accurate)
                    "-i", full_video_path,
                    "-t", duration_timestamp,  # Duration to extract
                    "-c:v", "libx264",  # Re-encode video to ensure compatibility
                    "-c:a", "aac",  # Re-encode audio to ensure compatibility
                    "-preset", "fast",  # Faster encoding
                    "-crf", "23",  # Good quality/size balance
                    "-avoid_negative_ts", "make_zero",  # Handle timestamp issues
                    segment_filepath
                ], check=True, capture_output=True, text=True)
                
                self.logger.info(f"Video segment created successfully: {segment_filepath}")
                return segment_filepath
                
            except subprocess.CalledProcessError as e:
                self.logger.error(f"FFmpeg error during trimming: {e.stderr}")
                # Fallback with stream copy if re-encoding fails
                self.logger.info("Retrying with stream copy...")
                try:
                    subprocess.run([
                        "ffmpeg",
                        "-y",
                        "-i", full_video_path,
                        "-ss", start_timestamp,
                        "-t", duration_timestamp,
                        "-c", "copy",
                        "-avoid_negative_ts", "make_zero",
                        segment_filepath
                    ], check=True, capture_output=True, text=True)
                    
                    self.logger.info(f"Video segment created with stream copy: {segment_filepath}")
                    return segment_filepath
                    
                except subprocess.CalledProcessError as e2:
                    self.logger.error(f"FFmpeg stream copy also failed: {e2.stderr}")
                    raise IOError(f"Failed to trim video segment: {e2.stderr}")
            except FileNotFoundError:
                self.logger.error("FFmpeg is required for video trimming. Please install FFmpeg and ensure it's in your system PATH.")
                raise IOError("FFmpeg is required for video trimming. Please install FFmpeg and ensure it's in your system PATH.")
