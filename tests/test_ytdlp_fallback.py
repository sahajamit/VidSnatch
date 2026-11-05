"""The yt-dlp fallback engages when pytubefix fails, and never on a bad URL."""

import pytest

from src import downloader as dl
from src.downloader import YouTubeDownloader


def _sabr(*_a, **_k):
    raise Exception("SABR Maximum reload attempts reached. Stream protection status: PoToken INVALID")


def test_audio_falls_back_and_discards_partial(tmp_path, monkeypatch):
    def partial_then_fail(self, url, out, quality):
        (tmp_path / "partial.webm").write_text("x")
        _sabr()

    monkeypatch.setattr(YouTubeDownloader, "_download_audio_impl", partial_then_fail)
    calls = {}

    def fake_fallback(url, out, fmt):
        calls["fmt"] = fmt
        p = tmp_path / "song.m4a"
        p.write_text("ok")
        return str(p)

    monkeypatch.setattr(dl.ytdlp_fallback, "download_audio", fake_fallback)
    path = YouTubeDownloader().download_audio("https://youtu.be/QtRK8lwrZBk", str(tmp_path), audio_format="m4a")
    assert path.endswith("song.m4a")
    assert calls["fmt"] == "m4a"
    assert not (tmp_path / "partial.webm").exists()


def test_video_falls_back(tmp_path, monkeypatch):
    monkeypatch.setattr(YouTubeDownloader, "_download_video_impl", _sabr)
    monkeypatch.setattr(dl.ytdlp_fallback, "download_video", lambda url, out, q: f"{out}/v.mp4")
    assert YouTubeDownloader().download_video("https://youtu.be/x", str(tmp_path)).endswith("v.mp4")


def test_invalid_url_is_not_retried(tmp_path, monkeypatch):
    def bad(*_a, **_k):
        raise ValueError("Invalid YouTube URL: nope")

    monkeypatch.setattr(YouTubeDownloader, "_download_video_impl", bad)
    monkeypatch.setattr(dl.ytdlp_fallback, "download_video", lambda *a: pytest.fail("fallback must not run"))
    with pytest.raises(ValueError):
        YouTubeDownloader().download_video("nope", str(tmp_path))


def test_missing_ytdlp_reports_both_errors(tmp_path, monkeypatch):
    monkeypatch.setattr(YouTubeDownloader, "_download_video_impl", _sabr)

    def missing(*_a):
        raise dl.ytdlp_fallback.YtDlpUnavailable("yt-dlp is not installed")

    monkeypatch.setattr(dl.ytdlp_fallback, "download_video", missing)
    with pytest.raises(IOError, match="PoToken INVALID.*yt-dlp is not installed"):
        YouTubeDownloader().download_video("https://youtu.be/x", str(tmp_path))
