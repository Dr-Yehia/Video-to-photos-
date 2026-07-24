"""The JS runtime is what makes YouTube's ciphered formats readable.

Without one, yt-dlp silently skips every format whose URL is encrypted,
the format list comes back empty, and the download dies with the
misleading "Requested format is not available" — the exact production
failure, even with valid cookies.

Checks (all offline):
  1. a runtime is detected on this machine, or bootstrapped;
  2. the runtime and remote components reach EVERY yt-dlp call site
     (probe, download, HLS) — not just one of them;
  3. with no runtime and downloading disabled, everything degrades
     gracefully instead of raising.

Run:  python tests/test_js_runtime.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from slide_extractor import downloader
from slide_extractor import jsruntime


def check_detection():
    opts, status = jsruntime.js_runtimes()
    print(f"  detected: {status}")
    assert opts, "no JS runtime available — YouTube formats would be empty"
    name, cfg = next(iter(opts.items()))
    assert name in ("deno", "node", "bun", "quickjs"), opts
    assert os.path.isfile(cfg["path"]), cfg
    print(f"  yt-dlp option: {{{name}: ...}} ✓")


def check_all_call_sites():
    """probe, download and HLS must each carry the runtime."""
    seen = []

    class FakeYDL:
        def __init__(self, opts):
            seen.append(opts)

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def extract_info(self, url, download=False):
            return {"title": "T", "duration": 1,
                    "formats": [{"height": 720, "vcodec": "avc1"}]}

        def prepare_filename(self, info):
            return os.path.join("/tmp", "probe_target.mp4")

    real = downloader.yt_dlp.YoutubeDL
    downloader.yt_dlp.YoutubeDL = FakeYDL
    try:
        downloader.probe_video("https://youtu.be/xxxxxxxxxxx")
        try:
            downloader._ytdlp_download("https://youtu.be/xxxxxxxxxxx", "/tmp",
                                       720, None, None)
        except Exception:
            pass
        try:
            downloader._download_hls("https://example.invalid/master.m3u8",
                                     "/tmp", 720, True, None)
        except Exception:
            pass
    finally:
        downloader.yt_dlp.YoutubeDL = real

    assert len(seen) >= 3, f"expected probe+download+hls option sets, got {len(seen)}"
    for i, opts in enumerate(seen[:3]):
        assert opts.get("js_runtimes"), f"call site {i} has no js_runtimes"
        assert opts.get("remote_components") == downloader._REMOTE_COMPONENTS, \
            f"call site {i} missing remote components"
    print(f"  {len(seen)} yt-dlp option sets, all carry the runtime ✓")


def check_graceful_without_runtime():
    """A host with nothing installed and no download allowed must still
    run (just without ciphered formats), never crash."""
    saved_cache, saved_find = jsruntime._cached, jsruntime._find_existing
    jsruntime._cached = None
    jsruntime._find_existing = lambda: None
    os.environ["V2S_DENO_DOWNLOAD"] = "0"
    try:
        opts, status = jsruntime.js_runtimes()
        assert opts == {}, opts
        assert "none" in status
        assert downloader._js_opts() == {}
        print(f"  no runtime -> status: {status[:60]}… ✓")
    finally:
        os.environ.pop("V2S_DENO_DOWNLOAD", None)
        jsruntime._find_existing = saved_find
        jsruntime._cached = saved_cache


def main():
    print("runtime detection:")
    check_detection()
    print("yt-dlp call sites:")
    check_all_call_sites()
    print("graceful degradation:")
    check_graceful_without_runtime()
    print("JS RUNTIME TEST PASSED ✔")


if __name__ == "__main__":
    main()
