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


# Static fallback mirror instances (public instances rot quickly, so
# the live registries below are consulted first).
INVIDIOUS_INSTANCES: List[str] = _env_instances("V2S_INVIDIOUS_INSTANCES", [
    "https://inv.nadeko.net",
    "https://yewtu.be",
    "https://invidious.nerdvpn.de",
])
PIPED_INSTANCES: List[str] = _env_instances("V2S_PIPED_INSTANCES", [
    "https://pipedapi.kavin.rocks",
    "https://api.piped.private.coffee",
])

# Live instance discovery from the official registries: public mirrors
# die weekly, so a hardcoded list alone guarantees eventual failure.
# Disabled in offline tests via V2S_DISCOVER=0.
DISCOVER_INSTANCES = os.environ.get("V2S_DISCOVER", "1") != "0"
_REGISTRY_CACHE: dict = {}


def _discover_instances(kind: str) -> List[str]:
    if not DISCOVER_INSTANCES:
        return []
    if kind in _REGISTRY_CACHE:
        return _REGISTRY_CACHE[kind]
    found: List[str] = []
    try:
        if kind == "invidious":
            r = requests.get("https://api.invidious.io/instances.json",
                             params={"sort_by": "health"}, timeout=10,
                             headers={"User-Agent": _UA})
            r.raise_for_status()
            for _name, info in r.json():
                if info.get("type") == "https" and info.get("api") is not False:
                    uri = str(info.get("uri", "")).rstrip("/")
                    if uri.startswith("https://"):
                        found.append(uri)
        else:
            r = requests.get("https://piped-instances.kavin.rocks/",
                             timeout=10, headers={"User-Agent": _UA})
            r.raise_for_status()
            for inst in r.json():
                api_url = str(inst.get("api_url", "")).rstrip("/")
                if api_url.startswith("https://"):
                    found.append(api_url)
    except Exception:
        found = []
    _REGISTRY_CACHE[kind] = found[:8]  # healthiest few; keep runtime sane
    return _REGISTRY_CACHE[kind]


def _mirror_instances(kind: str) -> List[str]:
    """Live registry instances first (healthiest), the static list as a
    backup, de-duplicated preserving order."""
    static = INVIDIOUS_INSTANCES if kind == "invidious" else PIPED_INSTANCES
    seen, merged = set(), []
    for inst in _discover_instances(kind) + static:
        if inst not in seen:
            seen.add(inst)
            merged.append(inst)
    return merged

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
                    exact_height: bool = False,
                    client_attempts=_CLIENT_ATTEMPTS,
                    log: Optional[list] = None) -> dict:
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
        for clients in client_attempts:
            opts = {**base_opts, **strategy}
            if clients:
                opts["extractor_args"] = {"youtube": {"player_client": clients}}
            try:
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    path = ydl.prepare_filename(info)
                _log(log, f"yt-dlp {clients or 'default'}: downloaded ✓")
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
                _log(log, f"yt-dlp {clients or 'default'}: "
                          f"{str(exc).splitlines()[0][:140]}")
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


def _log(log: Optional[list], message: str):
    if log is not None:
        log.append(message)


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


def _candidate_height(s: dict, label_keys: tuple) -> int:
    for k in label_keys:
        h = _stream_height(str(s.get(k, "")))
        if h:
            return h
    return 0


def _ordered_candidates(streams: List[dict], max_height: int,
                        url_key: str, label_keys: tuple,
                        exact_height: bool = False) -> List[dict]:
    """ALL usable streams in the order they should be attempted: when a
    stream fails to download, the next candidate (same height in another
    codec, then the next height down) still gets its chance — one broken
    stream must never collapse the quality all the way to the bottom."""
    def is_mp4(s):
        return "mp4" in str(s.get("type", "") or s.get("mimeType", "")).lower()

    usable = [s for s in streams if s.get(url_key)]
    if exact_height:
        # Strict round: only the requested height counts.
        pool = [s for s in usable
                if _candidate_height(s, label_keys) == max_height]
    else:
        pool = [s for s in usable
                if 0 < _candidate_height(s, label_keys) <= max_height]
        pool = pool or usable
    return sorted(pool, key=lambda s: (_candidate_height(s, label_keys),
                                       is_mp4(s)), reverse=True)


def _invidious_download(video_id: str, output_dir: str, max_height: int,
                        progress: Optional[ProgressFn],
                        exact_height: bool = False,
                        log: Optional[list] = None) -> dict:
    last_error: Optional[Exception] = None
    for inst in _mirror_instances("invidious"):
        try:
            r = requests.get(
                f"{inst}/api/v1/videos/{video_id}",
                params={"fields": "title,lengthSeconds,formatStreams,"
                                  "adaptiveFormats"},
                timeout=15, headers={"User-Agent": _UA})
            r.raise_for_status()
            data = r.json()
        except Exception as exc:
            last_error = exc
            _log(log, f"invidious {inst}: API unreachable ({exc})")
            continue
        streams = list(data.get("formatStreams") or [])
        streams += [s for s in (data.get("adaptiveFormats") or [])
                    if "video" in str(s.get("type", "")).lower()]
        label_keys = ("resolution", "qualityLabel")
        candidates = _ordered_candidates(streams, max_height, "url",
                                         label_keys,
                                         exact_height=exact_height)
        if not candidates:
            _log(log, f"invidious {inst}: no stream at "
                      f"{'exactly ' if exact_height else '≤'}{max_height}p")
        for s in candidates:
            h = _candidate_height(s, label_keys)
            # local=true proxies the bytes through the mirror instance,
            # sidestepping YouTube's block of our own IP.
            stream_url = s["url"]
            stream_url += ("&" if "?" in stream_url else "?") + "local=true"
            dest = os.path.join(output_dir, "video.mp4")
            try:
                _download_stream(stream_url, dest, progress)
                _log(log, f"invidious {inst}: downloaded {h}p ✓")
                return {
                    "path": dest,
                    "title": data.get("title") or "video",
                    "duration": data.get("lengthSeconds") or 0,
                }
            except Exception as exc:
                last_error = exc
                _log(log, f"invidious {inst} {h}p: {exc}")
    raise last_error or RuntimeError("no Invidious instance available")


def _piped_download(video_id: str, output_dir: str, max_height: int,
                    progress: Optional[ProgressFn],
                    exact_height: bool = False,
                    log: Optional[list] = None) -> dict:
    last_error: Optional[Exception] = None
    for api in _mirror_instances("piped"):
        try:
            r = requests.get(f"{api}/streams/{video_id}", timeout=15,
                             headers={"User-Agent": _UA})
            r.raise_for_status()
            data = r.json()
        except Exception as exc:
            last_error = exc
            _log(log, f"piped {api}: API unreachable ({exc})")
            continue
        candidates = _ordered_candidates(
            list(data.get("videoStreams") or []), max_height, "url",
            ("quality",), exact_height=exact_height)
        if not candidates:
            _log(log, f"piped {api}: no stream at "
                      f"{'exactly ' if exact_height else '≤'}{max_height}p")
        for s in candidates:
            h = _candidate_height(s, ("quality",))
            dest = os.path.join(output_dir, "video.mp4")
            try:
                _download_stream(s["url"], dest, progress)
                _log(log, f"piped {api}: downloaded {h}p ✓")
                return {
                    "path": dest,
                    "title": data.get("title") or "video",
                    "duration": data.get("duration") or 0,
                }
            except Exception as exc:
                last_error = exc
                _log(log, f"piped {api} {h}p: {exc}")
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
        for inst in _mirror_instances("invidious"):
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
        for api in _mirror_instances("piped"):
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
    source_hint: Optional[str] = None,
    attempt_log: Optional[list] = None,
) -> dict:
    """Download a video and return
    {'path', 'title', 'duration', 'actual_height'}.

    Tries yt-dlp (several player clients), then Invidious mirrors, then
    Piped mirrors. With exact_height=True the requested height is
    demanded on every channel first, and only if nothing at all serves
    it is the best lower height accepted. actual_height is measured
    from the downloaded file, never assumed.

    source_hint (from probe_video's 'source') skips the long yt-dlp
    client parade when the probe already proved YouTube is blocked for
    this server, and tries the mirror network that worked first.
    attempt_log, if given, collects a human-readable line per attempt.
    """
    os.makedirs(output_dir, exist_ok=True)

    def _finish(info: dict) -> dict:
        info["actual_height"] = measure_height(info["path"])
        return info

    # If the probe already reached the video through a mirror, YouTube
    # itself is blocked here: one quick yt-dlp try (in case the network
    # recovered), then straight to the mirrors instead of 12 doomed
    # attempts.
    mirror_hint = source_hint in ("invidious", "piped")
    clients = (None,) if mirror_hint else _CLIENT_ATTEMPTS

    try:
        return _finish(_ytdlp_download(url, output_dir, max_height, progress,
                                       cookies_file,
                                       exact_height=exact_height,
                                       client_attempts=clients,
                                       log=attempt_log))
    except Exception as primary_error:
        if not _retryable(str(primary_error)):
            raise
        vid = _video_id(url)
        if not vid:
            raise
        if progress:
            progress(0.0, "trying mirror networks")
        fallbacks = [_invidious_download, _piped_download]
        if source_hint == "piped":
            fallbacks.reverse()
        # Strict rounds on BOTH mirror networks first, then relaxed.
        rounds = [True, False] if exact_height else [False]
        for want_exact in rounds:
            for fallback in fallbacks:
                try:
                    return _finish(fallback(vid, output_dir, max_height,
                                            progress,
                                            exact_height=want_exact,
                                            log=attempt_log))
                except Exception:
                    continue
        raise primary_error
