"""Video downloading with a multi-layer fallback chain.

Layer 1 — yt-dlp (YouTube + 1000 other sites), retried across several
player clients: YouTube blocks datacenter/cloud IPs with HTTP 403 on the
video data even when metadata loads, but the android/ios/tv clients are
often accepted where the web client is refused.

Layer 2 — open-source mirror networks (Invidious, then Piped): their
API returns stream URLs proxied through the mirror's own servers, which
bypasses YouTube's block of the app server's IP entirely. Instances come
and go, so several are tried in order.

We download video-only streams where possible (no audio) since only
frames are needed — this halves download time and avoids merging.
"""

from __future__ import annotations

import os
import re
from typing import Callable, List, Optional

import requests
import yt_dlp

ProgressFn = Callable[[float, str], None]

# Tried in order; None = yt-dlp's default client mix.
_CLIENT_ATTEMPTS = (None, ["web_safari"], ["tv"], ["ios"], ["android"],
                    ["mweb"])

# Failures that are specific to the requesting IP/client and therefore
# worth retrying with another client or another network path. "drm" is
# here because some clients falsely report ordinary videos as
# DRM-protected while other clients serve them fine.
_RETRYABLE_MARKERS = ("403", "forbidden", "po token", "not a bot",
                      "confirm you", "unable to connect", "proxy",
                      "timed out", "429", "requested format is not available",
                      "no video formats", "drm")

def _env_instances(var: str, default: List[str]) -> List[str]:
    """Instance lists can be overridden (comma-separated) via env vars —
    used by offline tests and by deployments that run their own mirror."""
    raw = os.environ.get(var, "")
    parsed = [s.strip().rstrip("/") for s in raw.split(",") if s.strip()]
    return parsed or default


# Public mirror instances, tried in order.
INVIDIOUS_INSTANCES: List[str] = _env_instances("V2S_INVIDIOUS_INSTANCES", [
    "https://inv.nadeko.net",
    "https://yewtu.be",
    "https://invidious.nerdvpn.de",
    "https://iv.melmac.space",
])
PIPED_INSTANCES: List[str] = _env_instances("V2S_PIPED_INSTANCES", [
    "https://pipedapi.kavin.rocks",
    "https://pipedapi.adminforge.de",
    "https://api.piped.private.coffee",
])

_VIDEO_ID_RE = re.compile(
    r"(?:v=|youtu\.be/|/shorts/|/embed/|/live/)([A-Za-z0-9_-]{11})")

_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")


def _ffmpeg_location() -> Optional[str]:
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def _video_id(url: str) -> Optional[str]:
    m = _VIDEO_ID_RE.search(url)
    return m.group(1) if m else None


def _retryable(error_text: str) -> bool:
    low = error_text.lower()
    return any(marker in low for marker in _RETRYABLE_MARKERS)


# ---------------------------------------------------------------------------
# Layer 1: yt-dlp across player clients
# ---------------------------------------------------------------------------
def _ytdlp_download(url: str, output_dir: str, max_height: int,
                    progress: Optional[ProgressFn],
                    cookies_file: Optional[str],
                    exact_height: bool = False) -> dict:
    def hook(d):
        if progress and d.get("status") == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            done = d.get("downloaded_bytes")
            if total and done:
                progress(done / total,
                         f"{done / 1e6:.0f}MB / {total / 1e6:.0f}MB")

    base_opts = {
        "outtmpl": os.path.join(output_dir, "video.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "progress_hooks": [hook],
        "retries": 2,
        "socket_timeout": 20,
        # Fragmented (DASH/HLS) downloads go much faster in parallel.
        "concurrent_fragment_downloads": 4,
    }
    ffmpeg = _ffmpeg_location()
    if ffmpeg:
        base_opts["ffmpeg_location"] = os.path.dirname(ffmpeg)
    if cookies_file and os.path.isfile(cookies_file):
        base_opts["cookiefile"] = cookies_file
    # A user-supplied proxy (e.g. a residential one) is the most reliable
    # escape from YouTube's cloud-IP blocks. Set YTDLP_PROXY, e.g.
    # "http://user:pass@host:port" or "socks5://host:port".
    proxy = os.environ.get("YTDLP_PROXY")
    if proxy:
        base_opts["proxy"] = proxy

    # When the user picked a quality from the probed list, INSIST on it:
    # round 1 accepts only that exact height on every client, and only
    # if nothing serves it does round 2 accept the best height below it.
    strategies = []
    if exact_height:
        strategies.append({
            "format": (f"bv*[height={max_height}]"
                       f"/b[height={max_height}]"),
            "format_sort": ["proto:https", "vext:mp4"],
        })
    strategies.append({
        "format": "bv*/b",
        "format_sort": [f"res:{max_height}", "proto:https", "vext:mp4"],
    })

    first_error: Optional[Exception] = None
    for strategy in strategies:
        for clients in _CLIENT_ATTEMPTS:
            opts = {**base_opts, **strategy}
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
                # Keep the first (default-client) error: it describes
                # the video's real situation best; later clients add
                # noise like false DRM reports.
                first_error = first_error or exc
                if _retryable(str(exc)):
                    continue  # another client may be accepted
                raise  # bad URL / private video etc: same for all clients
    raise first_error


# ---------------------------------------------------------------------------
# Layer 2: Invidious / Piped mirrors (streams proxied by the mirror)
# ---------------------------------------------------------------------------
def _stream_height(label: str) -> int:
    m = re.search(r"(\d{3,4})", label or "")
    return int(m.group(1)) if m else 0


def _download_stream(stream_url: str, dest: str,
                     progress: Optional[ProgressFn]) -> None:
    with requests.get(stream_url, stream=True, timeout=(15, 60),
                      headers={"User-Agent": _UA}) as r:
        r.raise_for_status()
        total = int(r.headers.get("Content-Length") or 0)
        done = 0
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 18):
                f.write(chunk)
                done += len(chunk)
                if progress and total:
                    progress(done / total, "downloading (mirror)")
    if os.path.getsize(dest) < 100_000:  # an HTML error page, not a video
        raise RuntimeError("mirror returned a non-video response")


def _pick_stream(streams: List[dict], max_height: int,
                 url_key: str, label_keys: tuple,
                 exact_height: bool = False) -> Optional[dict]:
    def height(s):
        for k in label_keys:
            h = _stream_height(str(s.get(k, "")))
            if h:
                return h
        return 0

    usable = [s for s in streams if s.get(url_key)]
    mp4 = [s for s in usable if "mp4" in str(
        s.get("type", "") or s.get("mimeType", "")).lower()]
    pool = mp4 or usable
    if exact_height:
        # Strict round: only the requested height counts; returning None
        # lets the caller try other instances / the relaxed round.
        exact = [s for s in pool if height(s) == max_height]
        return exact[0] if exact else None
    fitting = [s for s in pool if 0 < height(s) <= max_height]
    pool = fitting or pool
    return max(pool, key=height) if pool else None


def _invidious_download(video_id: str, output_dir: str, max_height: int,
                        progress: Optional[ProgressFn],
                        exact_height: bool = False) -> dict:
    last_error: Optional[Exception] = None
    for inst in INVIDIOUS_INSTANCES:
        try:
            r = requests.get(
                f"{inst}/api/v1/videos/{video_id}",
                params={"fields": "title,lengthSeconds,formatStreams,"
                                  "adaptiveFormats"},
                timeout=15, headers={"User-Agent": _UA})
            r.raise_for_status()
            data = r.json()
            streams = list(data.get("formatStreams") or [])
            streams += [s for s in (data.get("adaptiveFormats") or [])
                        if "video" in str(s.get("type", "")).lower()]
            chosen = _pick_stream(streams, max_height, "url",
                                  ("resolution", "qualityLabel"),
                                  exact_height=exact_height)
            if not chosen:
                raise RuntimeError("no usable stream in mirror response")
            # local=true proxies the bytes through the mirror instance,
            # sidestepping YouTube's block of our own IP.
            stream_url = chosen["url"]
            stream_url += ("&" if "?" in stream_url else "?") + "local=true"
            dest = os.path.join(output_dir, "video.mp4")
            _download_stream(stream_url, dest, progress)
            return {
                "path": dest,
                "title": data.get("title") or "video",
                "duration": data.get("lengthSeconds") or 0,
            }
        except Exception as exc:
            last_error = exc
    raise last_error or RuntimeError("no Invidious instance available")


def _piped_download(video_id: str, output_dir: str, max_height: int,
                    progress: Optional[ProgressFn],
                    exact_height: bool = False) -> dict:
    last_error: Optional[Exception] = None
    for api in PIPED_INSTANCES:
        try:
            r = requests.get(f"{api}/streams/{video_id}", timeout=15,
                             headers={"User-Agent": _UA})
            r.raise_for_status()
            data = r.json()
            chosen = _pick_stream(list(data.get("videoStreams") or []),
                                  max_height, "url", ("quality",),
                                  exact_height=exact_height)
            if not chosen:
                raise RuntimeError("no usable stream in mirror response")
            dest = os.path.join(output_dir, "video.mp4")
            _download_stream(chosen["url"], dest, progress)
            return {
                "path": dest,
                "title": data.get("title") or "video",
                "duration": data.get("duration") or 0,
            }
        except Exception as exc:
            last_error = exc
    raise last_error or RuntimeError("no Piped instance available")


# ---------------------------------------------------------------------------
def probe_video(url: str, cookies_file: Optional[str] = None) -> dict:
    """Read the video's metadata WITHOUT downloading it: title, duration
    and — crucially — the list of video heights that actually exist in
    this specific video, so the user chooses among real qualities
    instead of assumed ones.

    Returns {'title', 'duration', 'heights': [1080, 720, ...],
             'source': 'youtube' | 'invidious' | 'piped'}.
    """
    opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "socket_timeout": 20,
    }
    if cookies_file and os.path.isfile(cookies_file):
        opts["cookiefile"] = cookies_file
    proxy = os.environ.get("YTDLP_PROXY")
    if proxy:
        opts["proxy"] = proxy

    first_error: Optional[Exception] = None
    for clients in _CLIENT_ATTEMPTS:
        o = dict(opts)
        if clients:
            o["extractor_args"] = {"youtube": {"player_client": clients}}
        try:
            with yt_dlp.YoutubeDL(o) as ydl:
                info = ydl.extract_info(url, download=False)
            heights = sorted({
                int(f["height"]) for f in info.get("formats", [])
                if f.get("height") and f.get("vcodec") not in (None, "none")
                and not f.get("has_drm")
            }, reverse=True)
            return {
                "title": info.get("title") or "video",
                "duration": info.get("duration") or 0,
                "heights": heights,
                "source": "youtube",
            }
        except yt_dlp.utils.DownloadError as exc:
            first_error = first_error or exc
            if _retryable(str(exc)):
                continue
            raise

    vid = _video_id(url)
    if vid:
        for inst in INVIDIOUS_INSTANCES:
            try:
                r = requests.get(
                    f"{inst}/api/v1/videos/{vid}",
                    params={"fields": "title,lengthSeconds,formatStreams,"
                                      "adaptiveFormats"},
                    timeout=15, headers={"User-Agent": _UA})
                r.raise_for_status()
                data = r.json()
                streams = list(data.get("formatStreams") or [])
                streams += [s for s in (data.get("adaptiveFormats") or [])
                            if "video" in str(s.get("type", "")).lower()]
                heights = sorted({
                    h for s in streams
                    for h in [_stream_height(str(s.get("resolution") or
                                                 s.get("qualityLabel") or ""))]
                    if h
                }, reverse=True)
                return {
                    "title": data.get("title") or "video",
                    "duration": data.get("lengthSeconds") or 0,
                    "heights": heights,
                    "source": "invidious",
                }
            except Exception:
                continue
        for api in PIPED_INSTANCES:
            try:
                r = requests.get(f"{api}/streams/{vid}", timeout=15,
                                 headers={"User-Agent": _UA})
                r.raise_for_status()
                data = r.json()
                heights = sorted({
                    h for s in (data.get("videoStreams") or [])
                    for h in [_stream_height(str(s.get("quality", "")))]
                    if h
                }, reverse=True)
                return {
                    "title": data.get("title") or "video",
                    "duration": data.get("duration") or 0,
                    "heights": heights,
                    "source": "piped",
                }
            except Exception:
                continue

    raise first_error or RuntimeError("could not read video info")


# ---------------------------------------------------------------------------
def measure_height(video_path: str) -> int:
    """The ACTUAL height of a downloaded file, read from the file itself
    — the honest answer to 'what quality did I really get?'."""
    import cv2
    cap = cv2.VideoCapture(video_path)
    try:
        return int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    finally:
        cap.release()


def download_video(
    url: str,
    output_dir: str,
    max_height: int = 1080,
    progress: Optional[ProgressFn] = None,
    cookies_file: Optional[str] = None,
    exact_height: bool = False,
) -> dict:
    """Download a video and return
    {'path', 'title', 'duration', 'actual_height'}.

    Tries yt-dlp (several player clients), then Invidious mirrors, then
    Piped mirrors. With exact_height=True the requested height is
    demanded on every channel first, and only if nothing at all serves
    it is the best lower height accepted. actual_height is measured
    from the downloaded file, never assumed.
    """
    os.makedirs(output_dir, exist_ok=True)

    def _finish(info: dict) -> dict:
        info["actual_height"] = measure_height(info["path"])
        return info

    try:
        return _finish(_ytdlp_download(url, output_dir, max_height, progress,
                                       cookies_file,
                                       exact_height=exact_height))
    except Exception as primary_error:
        if not _retryable(str(primary_error)):
            raise
        vid = _video_id(url)
        if not vid:
            raise
        if progress:
            progress(0.0, "trying mirror networks")
        for fallback in (_invidious_download, _piped_download):
            # Two rounds on the mirrors as well: exact height first.
            rounds = [True, False] if exact_height else [False]
            for want_exact in rounds:
                try:
                    return _finish(fallback(vid, output_dir, max_height,
                                            progress,
                                            exact_height=want_exact))
                except Exception:
                    continue
        raise primary_error
