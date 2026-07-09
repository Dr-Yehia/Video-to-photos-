"""Offline test of the full download fallback chain and quality
enforcement.

Simulates the exact production scenario on cloud hosts: yt-dlp cannot
reach YouTube (blocked/403), so download_video must fall back to the
Invidious mirror layer. A local HTTP server impersonates an Invidious
instance offering TWO real qualities (360p and 720p), so we can verify:

  - probe_video reports exactly the qualities that exist: [720, 360]
  - exact_height=True downloads the requested height, verified by
    MEASURING the downloaded file (not trusting labels)
  - the whole chain runs with no internet at all

Run:  python tests/test_fallback.py
"""

import json
import os
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import cv2

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from slide_extractor import downloader
from test_extractor import build_video

VIDEO_ID = "dQw4w9WgXcQ"


def upscale_video(src: str, dest: str, width: int, height: int):
    cap = cv2.VideoCapture(src)
    vw = cv2.VideoWriter(dest, cv2.VideoWriter_fourcc(*"mp4v"),
                         cap.get(cv2.CAP_PROP_FPS) or 10, (width, height))
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        vw.write(cv2.resize(frame, (width, height)))
    cap.release()
    vw.release()


class MockInvidious(BaseHTTPRequestHandler):
    # itag -> raw video bytes, or None to simulate a stream that exists
    # in the metadata but fails to download (the real production case:
    # 1080p is listed but its proxied stream errors out).
    streams = {}

    def do_GET(self):
        port = self.server.server_port
        if self.path.startswith(f"/api/v1/videos/{VIDEO_ID}"):
            body = json.dumps({
                "title": "Mock Lecture",
                "lengthSeconds": 42,
                "formatStreams": [
                    {"url": f"http://127.0.0.1:{port}/videoplayback?itag=18",
                     "type": "video/mp4", "resolution": "360p"},
                ],
                "adaptiveFormats": [
                    {"url": f"http://127.0.0.1:{port}/videoplayback?itag=137",
                     "type": "video/mp4; codecs=\"avc1\"",
                     "qualityLabel": "1080p"},
                    {"url": f"http://127.0.0.1:{port}/videoplayback?itag=136",
                     "type": "video/mp4; codecs=\"avc1\"",
                     "qualityLabel": "720p"},
                ],
            }).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path.startswith("/videoplayback"):
            assert "local=true" in self.path, "stream must be proxied"
            itag = 137 if "itag=137" in self.path else (
                136 if "itag=136" in self.path else 18)
            data = self.streams.get(itag)
            if data is None:  # broken stream
                self.send_response(500)
                self.end_headers()
                return
            self.send_response(200)
            self.send_header("Content-Type", "video/mp4")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *a):
        pass


def main():
    # A false "DRM protected" report from one player client must not
    # abort the chain: it has to be retryable so other clients and the
    # mirror layer still get their turn.
    assert downloader._retryable("ERROR: This video is DRM protected")
    assert downloader._retryable("HTTP Error 403: Forbidden")
    assert not downloader._retryable("Private video. Sign in if you've "
                                     "been granted access")

    tmp = tempfile.mkdtemp(prefix="fallback_test_")
    src360 = os.path.join(tmp, "src360.mp4")
    src720 = os.path.join(tmp, "src720.mp4")
    build_video(src360)                       # 640x360 lecture
    upscale_video(src360, src720, 1280, 720)  # same content at 720p
    # 1080p (itag 137) is listed in the metadata but BROKEN on download
    # — the exact production failure the graceful degradation must fix.
    MockInvidious.streams = {18: open(src360, "rb").read(),
                             136: open(src720, "rb").read(),
                             137: None}

    server = ThreadingHTTPServer(("127.0.0.1", 0), MockInvidious)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    port = server.server_port

    # Point the mirror layer at the mock; leave yt-dlp pointing at the
    # real (unreachable) YouTube so the primary layer genuinely fails.
    # Live registry discovery is disabled so only the mock is consulted.
    downloader.DISCOVER_INSTANCES = False
    downloader.INVIDIOUS_INSTANCES = [f"http://127.0.0.1:{port}"]
    downloader.PIPED_INSTANCES = []
    url = f"https://youtu.be/{VIDEO_ID}"

    # 1) probe reports exactly the qualities that exist
    probe = downloader.probe_video(url)
    print(f"  probe    : {probe}")
    assert probe["title"] == "Mock Lecture"
    assert probe["heights"] == [1080, 720, 360]
    assert probe["source"] == "invidious"

    # 2) exact quality selection, verified by measuring the file
    for want in (720, 360):
        info = downloader.download_video(
            url, os.path.join(tmp, f"out{want}"), max_height=want,
            exact_height=True, source_hint=probe["source"])
        print(f"  requested {want}p -> measured {info['actual_height']}p "
              f"({os.path.getsize(info['path'])} bytes)")
        assert info["actual_height"] == want, info

    # 3) graceful degradation: 1080p exists but its stream is broken —
    # the chain must fall to the NEXT height (720p), not collapse to
    # the bottom (360p), and the attempt log must tell the story.
    log = []
    info = downloader.download_video(
        url, os.path.join(tmp, "out1080"), max_height=1080,
        exact_height=True, source_hint=probe["source"], attempt_log=log)
    print(f"  requested 1080p (broken) -> measured "
          f"{info['actual_height']}p")
    print("  attempt log:")
    for line in log:
        print(f"    {line}")
    assert info["actual_height"] == 720, info
    assert any("1080p" in e for e in log), log

    # 4) the downloaded file must be a decodable video
    cap = cv2.VideoCapture(info["path"])
    assert cap.isOpened() and cap.read()[0], "downloaded video not decodable"
    cap.release()

    server.shutdown()
    print("FALLBACK CHAIN TEST PASSED ✔")


if __name__ == "__main__":
    main()
