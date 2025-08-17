"""
Main CLI interface for YouTube Downloader.
"""

import argparse
import sys
from pathlib import Path
from .downloader import YouTubeDownloader


def main():
    """Main function for command-line interface."""
    parser = argparse.ArgumentParser(
        description="Download YouTube videos and audio using pytube",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --url "https://www.youtube.com/watch?v=VIDEO_ID" --type video
  %(prog)s --url "https://www.youtube.com/watch?v=VIDEO_ID" --type audio
  %(prog)s --url "https://www.youtube.com/watch?v=VIDEO_ID" --type video --quality 720p
  %(prog)s --url "https://www.youtube.com/watch?v=VIDEO_ID" --type info
        """
    )
    
    parser.add_argument(
        "--url", "-u",
        required=True,
        help="YouTube video URL"
    )
    
    parser.add_argument(
        "--type", "-t",
        choices=["video", "audio", "info"],
        default="video",
        help="Download type: video, audio, or info (default: video)"
    )
    
    parser.add_argument(
        "--output", "-o",
        default="./downloads",
        help="Output directory (default: ./downloads)"
    )
    
    parser.add_argument(
        "--quality", "-q",
        default="highest",
        help="Video quality: highest, lowest, or specific resolution like 720p (default: highest)"
    )
    
    args = parser.parse_args()
    
    try:
        downloader = YouTubeDownloader()
        
        if args.type == "info":
            print("Getting video information...")
            info = downloader.get_video_info(args.url)
            
            print("\n" + "="*50)
            print("VIDEO INFORMATION")
            print("="*50)
            print(f"Title: {info['title']}")
            print(f"Author: {info['author']}")
            print(f"Duration: {info['duration']} seconds")
            print(f"Views: {info['views']:,}")
            print(f"Publish Date: {info['publish_date']}")
            print(f"Description: {info['description']}")
            
            print("\nAvailable Video Streams:")
            for stream in info['video_streams']:
                size_mb = stream['file_size'] / (1024 * 1024) if stream['file_size'] else 0
                print(f"  - {stream['resolution']} @ {stream['fps']}fps ({size_mb:.1f} MB)")
            
            print("\nAvailable Audio Streams:")
            for stream in info['audio_streams']:
                size_mb = stream['file_size'] / (1024 * 1024) if stream['file_size'] else 0
                print(f"  - {stream['abr']} ({size_mb:.1f} MB)")
            
        elif args.type == "video":
            print(f"Downloading video from: {args.url}")
            downloaded_file = downloader.download_video(
                url=args.url,
                output_path=args.output,
                quality=args.quality
            )
            print(f"\n✅ Successfully downloaded: {downloaded_file}")
            
        elif args.type == "audio":
            print(f"Downloading audio from: {args.url}")
            downloaded_file = downloader.download_audio(
                url=args.url,
                output_path=args.output
            )
            print(f"\n✅ Successfully downloaded: {downloaded_file}")
            
    except KeyboardInterrupt:
        print("\n❌ Download cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
