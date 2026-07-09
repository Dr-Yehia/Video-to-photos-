"""Offline test of the full download fallback chain.

Simulates the exact production scenario on cloud hosts: yt-dlp cannot
reach YouTube (blocked/403), so download_video must fall back to the
Invidious mirror layer. A local HTTP server impersonates an Invidious
instance (API JSON + video bytes), so the whole chain runs with no
internet at all.

Run:  python tests/test_fallback.py
"""

import json
import os
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from slide_extractor import downloader
from test_extractor import build_video

VIDEO_ID = "dQw4w9WgXcQ"


class MockInvidious(BaseHTTPRequestHandler):
    video_bytes = b""

    def do_GET(self):
        if self.path.startswith(f"/api/v1/videos/{VIDEO_ID}"):
            body = json.dumps({
                "title": "Mock Lecture",
                "lengthSeconds": 42,
                "formatStreams": [
                    {"url": f"http://127.0.0.1:{self.server.server_port}"
                            f"/videoplayback?itag=18",
                     "type": "video/mp4", "resolution": "360p"},
                ],
                "adaptiveFormats": [],
            }).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path.startswith("/videoplayback"):
            assert "local=true" in self.path, "stream must be proxied"
            self.send_response(200)
            self.send_header("Content-Type", "video/mp4")
            self.send_header("Content-Length", str(len(self.video_bytes)))
            self.end_headers()
            self.wfile.write(self.video_bytes)
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
    src = os.path.join(tmp, "src.mp4")
    build_video(src)
    MockInvidious.video_bytes = open(src, "rb").read()

    server = ThreadingHTTPServer(("127.0.0.1", 0), MockInvidious)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    port = server.server_port

    # Point the mirror layer at the mock; leave yt-dlp pointing at the
    # real (unreachable) YouTube so the primary layer genuinely fails.
    downloader.INVIDIOUS_INSTANCES = [f"http://127.0.0.1:{port}"]
    downloader.PIPED_INSTANCES = []

    # probe_video must fall back to the mirror too and report the REAL
    # qualities present in the video (the mock offers only 360p).
    probe = downloader.probe_video(f"https://youtu.be/{VIDEO_ID}")
    print(f"  probe    : {probe}")
    assert probe["title"] == "Mock Lecture"
    assert probe["heights"] == [360]
    assert probe["source"] == "invidious"

    events = []
    info = downloader.download_video(
        f"https://youtu.be/{VIDEO_ID}", os.path.join(tmp, "out"),
        max_height=720, progress=lambda p, m: events.append(m))

    print(f"  title    : {info['title']}")
    print(f"  duration : {info['duration']}s")
    print(f"  file     : {info['path']} "
          f"({os.path.getsize(info['path'])} bytes)")
    assert info["title"] == "Mock Lecture"
    assert os.path.getsize(info["path"]) == len(MockInvidious.video_bytes)
    assert any("mirror" in e for e in events), events

    # The downloaded file must be a decodable video.
    import cv2
    cap = cv2.VideoCapture(info["path"])
    assert cap.isOpened() and cap.read()[0], "downloaded video not decodable"
    cap.release()

    server.shutdown()
    print("FALLBACK CHAIN TEST PASSED ✔")


if __name__ == "__main__":
    main()
