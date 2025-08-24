#!/usr/bin/env python3
"""
Test script for VidSnatch transcript functionality
"""

import os
import tempfile
import pytest
from src import YouTubeDownloader


class TestTranscriptDownload:
    """Test cases for transcript download functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.downloader = YouTubeDownloader()
        self.test_url = "https://www.youtube.com/watch?v=PDKhUknuQDg&t=9s"
    
    def test_extract_video_id(self):
        """Test video ID extraction from various URL formats"""
        test_cases = [
            ("https://www.youtube.com/watch?v=PDKhUknuQDg&t=9s", "PDKhUknuQDg"),
            ("https://www.youtube.com/watch?v=PDKhUknuQDg", "PDKhUknuQDg"),
            ("https://youtu.be/PDKhUknuQDg", "PDKhUknuQDg"),
            ("https://www.youtube.com/embed/PDKhUknuQDg", "PDKhUknuQDg"),
        ]
        
        for url, expected_id in test_cases:
            video_id = self.downloader._extract_video_id(url)
            assert video_id == expected_id, f"Failed to extract correct video ID from {url}"
    
    def test_extract_video_id_invalid_url(self):
        """Test video ID extraction with invalid URL"""
        with pytest.raises(ValueError, match="Could not extract video ID"):
            self.downloader._extract_video_id("https://example.com/not-a-youtube-url")
    
    def test_download_transcript_success(self):
        """Test successful transcript download"""
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # Download transcript
                filepath = self.downloader.download_transcript(self.test_url, temp_dir)
                
                # Verify file was created
                assert os.path.exists(filepath), "Transcript file was not created"
                
                # Verify file has content
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                assert len(content) > 0, "Transcript file is empty"
                assert "Transcript for:" in content, "Transcript file missing header"
                assert "Video URL:" in content, "Transcript file missing URL"
                assert "Video ID:" in content, "Transcript file missing video ID"
                assert "PDKhUknuQDg" in content, "Transcript file missing correct video ID"
                
                # Check filename format
                filename = os.path.basename(filepath)
                assert filename.endswith("_transcript.txt"), "Transcript file has incorrect naming format"
                
                print(f"✅ Transcript downloaded successfully: {filepath}")
                print(f"📄 File size: {os.path.getsize(filepath)} bytes")
                
                # Print first 200 characters of transcript for verification
                transcript_start = content.split("=" * 50 + "\n\n")[1][:200] if "=" * 50 + "\n\n" in content else content[:200]
                print(f"📝 Transcript preview: {transcript_start}...")
                
            except ValueError as e:
                if "Transcript not available" in str(e):
                    pytest.skip(f"Transcript not available for test video: {e}")
                else:
                    raise
            except Exception as e:
                pytest.fail(f"Unexpected error during transcript download: {e}")
    
    def test_download_transcript_no_transcript_available(self):
        """Test handling of videos without transcripts"""
        # Use a URL that likely won't have transcripts (private or restricted video)
        no_transcript_url = "https://www.youtube.com/watch?v=invalid_video_id"
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with pytest.raises((ValueError, IOError)) as exc_info:
                self.downloader.download_transcript(no_transcript_url, temp_dir)
            
            # Verify error message contains expected information
            error_msg = str(exc_info.value)
            assert any(phrase in error_msg.lower() for phrase in [
                "transcript not available",
                "could not extract video id",
                "error downloading transcript"
            ]), f"Unexpected error message: {error_msg}"
    
    def test_download_transcript_different_languages(self):
        """Test transcript download with different language preferences"""
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # Try English first (default)
                filepath_en = self.downloader.download_transcript(self.test_url, temp_dir, language='en')
                assert os.path.exists(filepath_en), "English transcript file was not created"
                
                # Try auto-detect (will get first available)
                filepath_auto = self.downloader.download_transcript(self.test_url, temp_dir, language='auto')
                assert os.path.exists(filepath_auto), "Auto-detected transcript file was not created"
                
                print("✅ Multiple language transcript downloads successful")
                
            except ValueError as e:
                if "Transcript not available" in str(e):
                    pytest.skip(f"Transcript not available for test video: {e}")
                else:
                    raise


def test_transcript_integration():
    """Integration test for transcript functionality"""
    downloader = YouTubeDownloader()
    test_url = "https://www.youtube.com/watch?v=PDKhUknuQDg&t=9s"
    
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Test the complete workflow
            print(f"🧪 Testing transcript download for: {test_url}")
            
            # Download transcript
            filepath = downloader.download_transcript(test_url, temp_dir)
            
            # Verify integration
            assert os.path.exists(filepath)
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            assert len(content) > 100, "Transcript seems too short"
            
            print("✅ Integration test passed!")
            assert True  # Test passed
            
        except ValueError as e:
            if "Transcript not available" in str(e):
                print(f"⚠️  Transcript not available for test video: {e}")
                pytest.skip("Transcript not available for test video")
            else:
                raise
        except Exception as e:
            print(f"❌ Integration test failed: {e}")
            raise


if __name__ == "__main__":
    # Run a simple test when executed directly
    print("🚀 Running VidSnatch Transcript Test...")
    
    try:
        success = test_transcript_integration()
        if success:
            print("🎉 All tests completed successfully!")
        else:
            print("⚠️  Test completed with warnings (transcript not available)")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        exit(1)
