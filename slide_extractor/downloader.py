"""YouTube (and 1000+ other sites) download via yt-dlp.

We download video-only streams (no audio) since only frames are needed —
this halves download time and avoids requiring ffmpeg for merging.

YouTube aggressively blocks datacenter/cloud IPs (HTTP 403 on the video
data even though metadata loads). To maximize success on hosted
deployments we retry the download across several player clients — the
android/ios/tv clients often succeed where the web client is refused —
and optionally accept a cookies.txt file for authenticated access.
"""

from __future__ import annotations

import os
from typing import Callable, Optional

import yt_dlp

ProgressFn = Callable[[float, str], None]

# Tried in order; None = yt-dlp's default client mix.
_CLIENT_ATTEMPTS = (None, ["android"], ["ios"], ["tv"])


def _ffmpeg_location() -> Optional[str]:
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def download_video(
    url: str,
    output_dir: str,
    max_height: int = 1080,
    progress: Optional[ProgressFn] = None,
    cookies_file: Optional[str] = None,
) -> dict:
    """Download a video and return {'path': ..., 'title': ..., 'duration': ...}."""
    os.makedirs(output_dir, exist_ok=True)

    def hook(d):
        if progress and d.get("status") == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            done = d.get("downloaded_bytes")
            if total and done:
                progress(done / total, "downloading")

    fmt = (
        f"bestvideo[height<={max_height}][ext=mp4]"
        f"/bestvideo[height<={max_height}]"
        f"/best[height<={max_height}]/best"
    )
    base_opts = {
        "format": fmt,
        "outtmpl": os.path.join(output_dir, "video.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "progress_hooks": [hook],
        "retries": 3,
    }
    ffmpeg = _ffmpeg_location()
    if ffmpeg:
        base_opts["ffmpeg_location"] = os.path.dirname(ffmpeg)
    if cookies_file and os.path.isfile(cookies_file):
        base_opts["cookiefile"] = cookies_file

    last_error: Optional[Exception] = None
    for clients in _CLIENT_ATTEMPTS:
        opts = dict(base_opts)
        if clients:
            opts["extractor_args"] = {"youtube": {"player_client": clients}}
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                path = ydl.prepare_filename(info)
            return {
                "path": path,
                "title": info.get("title") or "video",
                "duration": info.get("duration") or 0,
            }
        except yt_dlp.utils.DownloadError as exc:
            last_error = exc
            # 403/bot-check refusals are per-client: another client may
            # be accepted. Anything else (bad URL, private, no network at
            # all) will fail identically, so stop retrying.
            text = str(exc).lower()
            if "403" in text or "forbidden" in text or "po token" in text:
                continue
            raise

    raise last_error  # every client was refused
