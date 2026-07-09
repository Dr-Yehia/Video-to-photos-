"""End-to-end test of the smart extraction core.

Builds a synthetic 10 fps "lecture" video that reproduces the hard cases:

  1. Slide A shown static.
  2. Slide B written INCREMENTALLY, one text line per second (the case
     that makes naive tools emit thousands of pages).
  3. A fade transition (must not become a slide).
  4. Slide C static.
  5. Slide A shown AGAIN (must be de-duplicated).

Expected result: exactly 3 unique slides, and slide B must be captured
in its FINAL state (all 5 lines present, verified by ink density).

Run:  python tests/test_extractor.py
"""

import os
import sys
import tempfile

import cv2
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from slide_extractor import ExtractorConfig, SlideExtractor, build_pdf

W, H, FPS = 640, 360, 10


def make_slide(color, seed):
    """A slide = colored background + distinctive random header blocks."""
    img = np.full((H, W, 3), color, np.uint8)
    rng = np.random.RandomState(seed)
    for _ in range(6):
        x, y = rng.randint(0, W - 90), rng.randint(0, 70)
        c = tuple(int(v) for v in rng.randint(0, 255, 3))
        cv2.rectangle(img, (x, y), (x + 80, y + 28), c, -1)
    return img


def add_lines(slide, n):
    """Simulate handwriting: draw the first n text lines."""
    img = slide.copy()
    for i in range(n):
        y = 110 + i * 45
        cv2.putText(img, f"handwritten line number {i + 1} ....", (30, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (10, 10, 10), 2)
    return img


def build_video(path):
    vw = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"mp4v"), FPS, (W, H))
    A = make_slide((235, 235, 235), 1)
    B = make_slide((255, 244, 214), 2)
    C = make_slide((214, 236, 255), 3)

    def hold(frame, seconds):
        for _ in range(int(seconds * FPS)):
            vw.write(frame)

    hold(A, 5)                                   # 1) static slide A
    for n in range(6):                           # 2) B written line by line
        hold(add_lines(B, n), 1.5)
    B_final = add_lines(B, 5)
    hold(B_final, 3)
    for i in range(int(1.0 * FPS)):              # 3) fade B -> C
        t = i / (1.0 * FPS)
        vw.write(cv2.addWeighted(B_final, 1 - t, C, t, 0))
    hold(C, 5)                                   # 4) static slide C
    hold(A, 4)                                   # 5) slide A repeated
    vw.release()
    return A, B_final, C


def ink(img_path):
    g = cv2.cvtColor(cv2.imread(img_path), cv2.COLOR_BGR2GRAY)
    return np.count_nonzero(cv2.Canny(g, 60, 160))


def main():
    tmp = tempfile.mkdtemp(prefix="slides_test_")
    video = os.path.join(tmp, "lecture.mp4")
    _, B_final, _ = build_video(video)

    slides = SlideExtractor(ExtractorConfig.from_sensitivity("medium")).extract(
        video, os.path.join(tmp, "out"))

    print(f"extracted {len(slides)} slides:")
    for s in slides:
        print(f"  #{s.index + 1} t={s.timestamp:6.1f}s ink={ink(s.path):6d} {s.path}")

    assert len(slides) == 3, f"expected 3 unique slides, got {len(slides)}"

    # Slide B (the incrementally-written one) must be complete: its ink
    # must match the final fully-written frame, not an early partial one.
    ref = os.path.join(tmp, "b_final_ref.png")
    cv2.imwrite(ref, B_final)
    ref_ink = ink(ref)
    b = max(slides, key=lambda s: ink(s.path))
    b_ink = ink(b.path)
    assert b_ink >= ref_ink * 0.9, (
        f"slide B captured incomplete: ink {b_ink} vs final {ref_ink}")

    pdf = build_pdf([s.path for s in slides], os.path.join(tmp, "slides.pdf"))
    assert os.path.getsize(pdf) > 10_000
    print(f"PDF built: {pdf} ({os.path.getsize(pdf)} bytes)")
    print("ALL TESTS PASSED ✔")


if __name__ == "__main__":
    main()
