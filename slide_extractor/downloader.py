"""YouTube (and 1000+ other sites) download via yt-dlp.

We download video-only streams (no audio) since only frames are needed —
this halves download time and avoids requiring ffmpeg for merging.
"""

from __future__ import annotations

import os
from typing import Callable, Optional

import yt_dlp

ProgressFn = Callable[[float, str], None]


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
    opts = {
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
        opts["ffmpeg_location"] = os.path.dirname(ffmpeg)

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        path = ydl.prepare_filename(info)

    return {
        "path": path,
        "title": info.get("title") or "video",
        "duration": info.get("duration") or 0,
    }
