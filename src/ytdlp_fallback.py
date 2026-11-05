"""yt-dlp fallback for downloads that pytubefix can no longer complete.

YouTube now protects many streams with PO Tokens and SABR. pytubefix cannot mint
a PO Token, so its downloads fail with errors such as
"SABR Maximum reload attempts reached. Stream protection status: PoToken INVALID".
yt-dlp can, when three things are present together:

1. the bgutil PO Token provider (plugin injected into yt-dlp, server on :4416),
2. ``--remote-components ejs:github`` for the signature and n-challenge solver,
3. a player client that YouTube currently serves real streams to.

Which client works changes on YouTube's schedule, so the client is probed rather
than hardcoded. The yt-dlp binary is used (not the Python package) because the
PO Token plugin lives in yt-dlp's own pipx venv.
"""

import json
import os
import shutil
import subprocess
import time
import urllib.request
from pathlib import Path
from typing import Optional

from .logger import get_logger

logger = get_logger("vidsnatch.ytdlp")

PLAYER_CLIENTS = ("web_embedded", "web_safari", "tv_embedded", "mweb", "web", "tv", "android_vr")

POT_SERVER_URL = os.environ.get("VIDSNATCH_POT_URL", "http://127.0.0.1:4416")
POT_SERVER_DIR = Path(
    os.environ.get("VIDSNATCH_POT_DIR", str(Path.home() / "bgutil-ytdlp-pot-provider" / "server"))
)

# Video quality names used by vidsnatch, mapped to a height cap.
_HEIGHTS = {"highest": 1080, "high": 720, "medium": 480, "low": 360, "lowest": 360}


class YtDlpUnavailable(RuntimeError):
    """yt-dlp is not installed, so there is nothing to fall back to."""


def _binary() -> str:
    path = os.environ.get("VIDSNATCH_YTDLP") or shutil.which("yt-dlp")
    if not path:
        raise YtDlpUnavailable(
            "yt-dlp is not installed. Install it with `pipx install yt-dlp` and "
            "`pipx inject yt-dlp bgutil-ytdlp-pot-provider`."
        )
    return path


def _pot_server_up() -> bool:
    try:
        with urllib.request.urlopen(f"{POT_SERVER_URL}/ping", timeout=3) as r:
            return r.status == 200
    except Exception:
        return False


def ensure_pot_server() -> bool:
    """Start the bgutil PO Token server if it is installed and not running.

    It is started detached and left running for later downloads. Returns whether
    the server is answering; a missing server is not fatal, yt-dlp may still
    succeed on unprotected videos.
    """
    if _pot_server_up():
        return True
    main_js = POT_SERVER_DIR / "build" / "main.js"
    node = shutil.which("node")
    if not (main_js.exists() and node):
        logger.warning(
            f"PO Token server not running and not found at {main_js}; "
            "protected videos will likely fail with HTTP 403."
        )
        return False
    port = POT_SERVER_URL.rsplit(":", 1)[-1].strip("/")
    logger.info("Starting the bgutil PO Token server...")
    log = open(Path(os.environ.get("TMPDIR", "/tmp")) / "bgutil-server.log", "ab")
    subprocess.Popen(
        [node, str(main_js), "--port", port],
        cwd=str(POT_SERVER_DIR), stdout=log, stderr=log, start_new_session=True,
    )
    for _ in range(20):
        time.sleep(0.5)
        if _pot_server_up():
            return True
    logger.warning("PO Token server did not come up within 10 s.")
    return False


def _has_streams(path: str, need_video: bool) -> bool:
    """True when the file has an audio stream (and a video stream if needed).

    A video-only file with a plausible duration is the classic signature of a
    download that silently went wrong, so the result is always checked.
    """
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "stream=codec_type", "-of", "json", path],
            check=True, capture_output=True, text=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return os.path.getsize(path) > 0
    types = {s.get("codec_type") for s in json.loads(out).get("streams", [])}
    return "audio" in types and (not need_video or "video" in types)


def _run(url: str, output_path: str, fmt_args: list[str], need_video: bool) -> str:
    ytdlp = _binary()
    ensure_pot_server()
    Path(output_path).mkdir(parents=True, exist_ok=True)
    errors = []
    for client in PLAYER_CLIENTS:
        cmd = [
            ytdlp, "--no-playlist", "--no-progress", "--quiet", "--no-warnings",
            "--remote-components", "ejs:github",
            "--extractor-args", f"youtube:player_client={client}",
            *fmt_args,
            "-o", "%(title)s.%(ext)s", "--paths", output_path,
            "--print", "after_move:filepath",
            url,
        ]
        logger.info(f"yt-dlp: trying player client {client}...")
        proc = subprocess.run(cmd, capture_output=True, text=True)
        lines = [l for l in proc.stdout.splitlines() if l.strip()]
        path = lines[-1].strip() if lines else ""
        if proc.returncode == 0 and path and os.path.exists(path):
            if _has_streams(path, need_video):
                logger.info(f"yt-dlp succeeded with {client}: {path}")
                return path
            os.remove(path)
            errors.append(f"{client}: missing audio/video stream")
            continue
        last = (proc.stderr.strip().splitlines() or ["unknown error"])[-1]
        errors.append(f"{client}: {last}")
    raise IOError("yt-dlp fallback failed with every player client: " + " | ".join(errors))


def download_video(url: str, output_path: str, quality: str = "highest") -> str:
    """Download a video as mp4, preferring H.264 + AAC so QuickTime can open it."""
    height = _HEIGHTS.get(quality)
    if height is None and str(quality).rstrip("p").isdigit():
        height = int(str(quality).rstrip("p"))
    height = height or 1080
    fmt = (
        f"bv*[height<={height}][vcodec^=avc1]+ba[acodec^=mp4a]"
        f"/bv*[height<={height}]+ba/b[height<={height}]/b"
    )
    return _run(url, output_path, ["-f", fmt, "--merge-output-format", "mp4"], need_video=True)


def download_audio(url: str, output_path: str, audio_format: str = "mp3") -> str:
    """Download the best audio track and convert it to mp3, m4a or wav."""
    audio_format = (audio_format or "mp3").lower()
    return _run(
        url, output_path,
        ["-f", "bestaudio/best", "-x", "--audio-format", audio_format, "--audio-quality", "0"],
        need_video=False,
    )


def get_metadata(url: str) -> dict:
    """Title and duration via yt-dlp, for when pytubefix cannot even read them."""
    ytdlp = _binary()
    proc = subprocess.run(
        [ytdlp, "--no-playlist", "--skip-download", "--no-warnings", "--remote-components", "ejs:github",
         "--print", "%(title)s\n%(duration)s", url],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        raise IOError(f"yt-dlp could not read video metadata: {proc.stderr.strip()[-300:]}")
    title, _, duration = proc.stdout.strip().partition("\n")
    return {"title": title, "duration": float(duration or 0)}
