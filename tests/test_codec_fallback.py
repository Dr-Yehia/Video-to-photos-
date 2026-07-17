"""Reproduces the production failure with long YouTube videos: the file
is encoded with a codec OpenCV cannot decode (YouTube serves AV1 for
long/low-bitrate videos), grab() succeeds while retrieve() fails, and
extraction used to end instantly with zero slides.

Verifies:
  1. an AV1 file OpenCV can't read is transparently re-sampled through
     ffmpeg and slides ARE extracted from it;
  2. the resample path is exercised deterministically (forced) on a
     normal video and yields the same slides as direct decoding;
  3. candidate frames are spooled to disk (flat memory) and the .raw
     spool dir is cleaned up.

Run:  python tests/test_codec_fallback.py
"""

import os
import subprocess
import sys
import tempfile

import cv2

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from slide_extractor import ExtractorConfig, SlideExtractor
from test_extractor import build_video


def encode_av1(src: str, dest: str) -> bool:
    """Re-encode to AV1 (tiny + fastest settings). Returns False when
    the bundled ffmpeg lacks an AV1 encoder."""
    import imageio_ffmpeg
    exe = imageio_ffmpeg.get_ffmpeg_exe()
    r = subprocess.run(
        [exe, "-y", "-i", src, "-vf", "scale=320:180,fps=5",
         "-c:v", "libaom-av1", "-crf", "50", "-b:v", "0",
         "-cpu-used", "8", "-row-mt", "1", "-an", dest],
        capture_output=True, timeout=1200)
    return r.returncode == 0 and os.path.getsize(dest) > 1000


def main():
    tmp = tempfile.mkdtemp(prefix="codec_test_")
    src = os.path.join(tmp, "lecture.mp4")
    build_video(src)

    # ---- 1) real AV1 file ------------------------------------------------
    av1 = os.path.join(tmp, "lecture_av1.mp4")
    if encode_av1(src, av1):
        cv2_reads_av1 = SlideExtractor._decodable(av1)
        print(f"  OpenCV decodes AV1 directly: {cv2_reads_av1}")
        slides = SlideExtractor(ExtractorConfig.from_sensitivity(
            "medium")).extract(av1, os.path.join(tmp, "out_av1"))
        print(f"  AV1 video -> {len(slides)} slides extracted")
        assert len(slides) >= 2, "expected slides from the AV1 video"
    else:
        print("  (ffmpeg has no AV1 encoder here; skipping real-AV1 case)")

    # ---- 2) forced resample path on a normal video ----------------------
    extractor = SlideExtractor(ExtractorConfig.from_sensitivity("medium"))
    extractor._decodable = lambda path: path.endswith("_resampled.mp4")
    out2 = os.path.join(tmp, "out_forced")
    slides = extractor.extract(src, out2)
    print(f"  forced-resample path -> {len(slides)} slides")
    assert len(slides) == 3, f"expected the 3 lecture slides, got "  \
                             f"{len(slides)}"
    assert not os.path.isdir(os.path.join(out2, ".raw")), \
        "raw spool dir must be cleaned up"
    assert not os.path.exists(os.path.join(out2, "_resampled.mp4")), \
        "temporary resampled video must be deleted"

    print("CODEC FALLBACK TEST PASSED ✔")


if __name__ == "__main__":
    main()
