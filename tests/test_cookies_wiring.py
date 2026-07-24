"""Verify the cookies.txt path end-to-end, without any network.

Two things must hold for cookies to actually help on a blocked host:
  1. the file parses as a Netscape cookie jar and carries YouTube's
     authentication cookies (SID / __Secure-*PSID / LOGIN_INFO);
  2. the path is threaded all the way from the UI through JobManager
     into download_video (and on to yt-dlp's `cookiefile`).

Point 2 always runs. Point 1 runs when a real cookie file is supplied:
    V2S_TEST_COOKIES=/path/to/cookies.txt python tests/test_cookies_wiring.py
(The cookie file itself is authentication material and never belongs in
the repository.)
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from slide_extractor import downloader
from slide_extractor.jobs import JobManager

AUTH_COOKIES = {"SID", "__Secure-1PSID", "__Secure-3PSID", "LOGIN_INFO",
                "SAPISID"}


def check_cookie_file(path: str):
    """Parse with yt-dlp's own loader — exactly what the download will do."""
    from yt_dlp.cookies import load_cookies
    jar = load_cookies(path, None, None)
    names = {c.name for c in jar if c.domain.endswith("youtube.com")}
    print(f"  cookies for youtube.com: {len(names)}")
    missing = AUTH_COOKIES - names
    assert not missing, f"missing authentication cookies: {sorted(missing)}"
    print(f"  authentication cookies present: {sorted(AUTH_COOKIES)}")


def check_wiring():
    """JobManager must forward cookies_file (and the quality/source
    hints) into download_video."""
    captured = {}

    def fake_download(url, output_dir, **kwargs):
        captured.update(kwargs)
        captured["url"] = url
        raise RuntimeError("stop here: wiring captured")

    real = downloader.download_video
    import slide_extractor.jobs as jobs_mod
    jobs_mod.download_video = fake_download
    try:
        root = tempfile.mkdtemp(prefix="cookies_wiring_")
        manager = JobManager(root=root)
        job = manager.create("https://youtu.be/xxxxxxxxxxx",
                             sensitivity="high", max_height=1080,
                             exact_height=True, source_hint="piped",
                             cookies_file="/tmp/my_cookies.txt")
        for _ in range(100):
            if job.status == "error":
                break
            import time
            time.sleep(0.05)
    finally:
        jobs_mod.download_video = real

    print(f"  forwarded: {sorted(captured)}")
    assert captured.get("cookies_file") == "/tmp/my_cookies.txt", captured
    assert captured.get("max_height") == 1080, captured
    assert captured.get("exact_height") is True, captured
    assert captured.get("source_hint") == "piped", captured
    assert captured.get("attempt_log") is not None, captured


def check_probe_options():
    """probe_video must (a) attach the cookie file, (b) not let yt-dlp's
    default format selection abort a metadata-only probe, and (c) know
    where ffmpeg is — the missing pieces that made a probe WITH cookies
    fail with 'Requested format is not available'."""
    captured = {}

    class FakeYDL:
        def __init__(self, opts):
            captured.update(opts)

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def extract_info(self, url, download=False):
            return {"title": "T", "duration": 1,
                    "formats": [{"height": 1080, "vcodec": "avc1"},
                                {"height": 360, "vcodec": "avc1"}]}

    real = downloader.yt_dlp.YoutubeDL
    downloader.yt_dlp.YoutubeDL = FakeYDL
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".txt",
                                         delete=False) as f:
            f.write("# Netscape HTTP Cookie File\n")
            cookie_path = f.name
        info = downloader.probe_video("https://youtu.be/xxxxxxxxxxx",
                                      cookies_file=cookie_path)
    finally:
        downloader.yt_dlp.YoutubeDL = real
        os.unlink(cookie_path)

    print(f"  heights read: {info['heights']}")
    assert info["heights"] == [1080, 360], info
    assert captured.get("cookiefile") == cookie_path, captured
    assert captured.get("ignore_no_formats_error") is True, captured
    assert captured.get("skip_download") is True, captured
    assert "ffmpeg_location" in captured, captured
    print("  probe options: cookiefile ✓ ignore_no_formats_error ✓ "
          "ffmpeg_location ✓")


def check_sabr_probe():
    """The production failure: YouTube answers, but every format is
    unusable (no URL — SABR streaming), so the quality list came back
    empty with no explanation. The probe must keep trying other player
    clients and, when none yields a usable format, still return the
    metadata plus diagnostics that say why."""
    calls = []

    class FakeYDL:
        def __init__(self, opts):
            self.opts = opts
            args = opts.get("extractor_args", {}).get("youtube", {})
            self.clients = args.get("player_client")
            self.logger = opts.get("logger")
            calls.append(self.clients)

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def extract_info(self, url, download=False):
            if self.logger:
                self.logger.warning(
                    "Some tv client https formats have been skipped as "
                    "they are missing a url. YouTube is forcing SABR "
                    "streaming for this client.")
            # Only the tv_simply client hands out a usable format.
            if self.clients and "tv_simply" in self.clients:
                return {"title": "T", "duration": 5,
                        "formats": [{"height": 1080, "vcodec": "avc1"}]}
            return {"title": "T", "duration": 5,
                    "formats": [{"height": 1080, "vcodec": "none"}]}

    real = downloader.yt_dlp.YoutubeDL
    downloader.yt_dlp.YoutubeDL = FakeYDL
    try:
        info = downloader.probe_video("https://youtu.be/xxxxxxxxxxx")
    finally:
        downloader.yt_dlp.YoutubeDL = real

    print(f"  clients tried: {len(calls)} | heights: {info['heights']}")
    assert info["heights"] == [1080], info
    # the combined first round must include tv_simply, so ONE call is
    # enough to recover the quality list
    assert len(calls) == 1, calls
    assert any("SABR" in d for d in info.get("diagnostics", [])), \
        info.get("diagnostics")
    print("  SABR warning captured into diagnostics ✓")

    # Now make even tv_simply unusable: the probe must exhaust the
    # clients and still return metadata + a clear explanation.
    class AllSabr(FakeYDL):
        def extract_info(self, url, download=False):
            if self.logger:
                self.logger.warning("formats have been skipped as they "
                                    "are missing a url (SABR)")
            return {"title": "T", "duration": 5,
                    "formats": [{"height": 720, "vcodec": "none"}]}

    calls.clear()
    downloader.yt_dlp.YoutubeDL = AllSabr
    try:
        info = downloader.probe_video("https://youtu.be/xxxxxxxxxxx")
    finally:
        downloader.yt_dlp.YoutubeDL = real
    print(f"  all-SABR: clients tried {len(calls)}, heights {info['heights']},"
          f" formats_count {info.get('formats_count')}")
    assert info["heights"] == [], info
    assert info["title"] == "T", info          # metadata still returned
    assert info["formats_count"] == 1, info
    assert len(calls) == len(downloader._CLIENT_ATTEMPTS), calls
    assert any("0 usable video formats" in d
               for d in info.get("diagnostics", [])), info.get("diagnostics")
    print("  exhausted every client and explained the empty list ✓")


def main():
    print("probe options:")
    check_probe_options()

    print("SABR / empty-format-list handling:")
    check_sabr_probe()

    print("wiring (UI -> JobManager -> download_video):")
    check_wiring()

    path = os.environ.get("V2S_TEST_COOKIES")
    if path and os.path.isfile(path):
        print("cookie file:")
        check_cookie_file(path)
    else:
        print("cookie file: skipped (set V2S_TEST_COOKIES to check one)")

    print("COOKIES WIRING TEST PASSED ✔")


if __name__ == "__main__":
    main()
