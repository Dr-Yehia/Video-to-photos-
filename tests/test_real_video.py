"""Real-video end-to-end test: download a YouTube video, extract every
slide in it, and write the PDF into examples/.

Needs internet access to YouTube (run it on your machine, or in a cloud
environment whose network policy allows youtube.com / googlevideo.com).

Usage:
    python tests/test_real_video.py                     # default test video
    python tests/test_real_video.py <url> [sensitivity]
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from slide_extractor import (ExtractorConfig, SlideExtractor, build_pdf,
                             download_video)

DEFAULT_URL = "https://youtu.be/GBkRLTlS1_g"
EXAMPLES_DIR = os.path.join(os.path.dirname(__file__), "..", "examples")


def main():
    url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URL
    sensitivity = sys.argv[2] if len(sys.argv) > 2 else "medium"

    def progress(pct, msg):
        sys.stderr.write(f"\r  [{pct * 100:5.1f}%] {msg:<40}")
        sys.stderr.flush()

    tmp = tempfile.mkdtemp(prefix="real_video_test_")
    print(f"Downloading {url} ...")
    info = download_video(url, tmp, max_height=1080, progress=progress)
    print(f"\n  Title: {info['title']}  ({info['duration']}s)")

    print("Extracting slides ...")
    extractor = SlideExtractor(ExtractorConfig.from_sensitivity(sensitivity))
    slides = extractor.extract(info["path"], os.path.join(tmp, "slides"),
                               progress=progress)
    print(f"\n  {len(slides)} unique slides extracted")
    assert slides, "no slides were extracted from the video"

    os.makedirs(EXAMPLES_DIR, exist_ok=True)
    video_id = url.rstrip("/").split("/")[-1].split("?")[0].replace("watch", "")
    pdf_path = os.path.abspath(
        os.path.join(EXAMPLES_DIR, f"{video_id or 'video'}.pdf"))
    build_pdf([s.path for s in slides], pdf_path)
    size_mb = os.path.getsize(pdf_path) / 1e6
    print(f"  PDF written: {pdf_path} ({size_mb:.1f} MB)")
    print("REAL-VIDEO TEST PASSED ✔")


if __name__ == "__main__":
    main()
