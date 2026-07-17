"""The heart of the project: smart slide extraction.

The hard problem this solves: a lecturer writes on a slide gradually
(a word, a dot, a line at a time). Naive scene detection treats every
pen stroke as a "new page" and produces thousands of pages. Instead we
model the video as a sequence of *stability segments* and use the key
asymmetry between writing and page flips:

  - WRITING only ADDS ink: old edges stay where they were, a small area
    of new pixels appears. We stay in the same segment and keep the
    latest *stable* frame, so the slide is held in its most complete
    state.
  - A PAGE FLIP REMOVES content: a large share of the previous frame's
    edges disappears (or a large share of pixels changes color). That
    closes the segment and emits its final stable frame as a slide.
  - TRANSITIONS (fades, cuts, camera pans) never produce a stable pair
    of samples and their segments are too short, so they are dropped —
    the emitted frame is always a clean, fully-rendered slide, never a
    mid-fade blend.
  - A final perceptual-hash + color pass removes duplicate slides
    (e.g. the lecturer flips back to an earlier page), keeping whichever
    copy carries the most detail (most "ink").
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Tuple

import cv2
import imagehash
import numpy as np
from PIL import Image

ProgressFn = Callable[[float, str], None]


@dataclass
class ExtractorConfig:
    # Seconds between analyzed samples. 1.0 is a good balance between
    # accuracy and speed even for hour-long lectures.
    sample_interval: float = 1.0
    # Fraction of significantly-changed pixels (max over B,G,R channels)
    # that means "new slide". Writing a line changes <2-3% of pixels.
    change_ratio_threshold: float = 0.20
    # Fraction of the previous frame's edges that must vanish to count
    # as "content removed" => new slide. Writing removes ~0.
    removed_edges_threshold: float = 0.25
    # Per-pixel absolute color difference considered "changed".
    pixel_diff_threshold: int = 28
    # A pair of consecutive samples is "stable" when almost nothing
    # changed between them; only stable frames may be emitted as slides.
    stable_change_epsilon: float = 0.02
    stable_removed_epsilon: float = 0.10
    # A segment must span at least this many samples to become a slide
    # (filters out fades, camera pans and other transitions).
    min_stable_samples: int = 2
    # Hamming distance (perceptual hash, 64 bit) at or below which two
    # slides *may* be duplicates (confirmed by the color check below).
    dedup_hash_distance: int = 6
    # Mean per-pixel color distance below which two hash-similar slides
    # are confirmed duplicates.
    dedup_color_distance: float = 10.0
    # Width the frame is downscaled to for change analysis.
    analysis_width: int = 320
    # JPEG quality for saved slides (100 = maximum).
    jpeg_quality: int = 95

    @classmethod
    def from_sensitivity(cls, sensitivity: str = "medium") -> "ExtractorConfig":
        """high = capture more slides (smaller changes count as a new
        page), low = only very large changes count."""
        presets = {
            "low": dict(change_ratio_threshold=0.35,
                        removed_edges_threshold=0.40,
                        min_stable_samples=3),
            "medium": dict(change_ratio_threshold=0.20,
                           removed_edges_threshold=0.25,
                           min_stable_samples=2),
            "high": dict(change_ratio_threshold=0.10,
                         removed_edges_threshold=0.15,
                         min_stable_samples=1),
        }
        if sensitivity not in presets:
            raise ValueError(f"unknown sensitivity: {sensitivity!r}")
        return cls(**presets[sensitivity])


@dataclass
class Slide:
    index: int
    timestamp: float          # seconds into the video where slide was captured
    path: str                 # saved image file
    detail_score: float = 0.0 # edge density; higher = more content ("ink")
    phash: object = field(default=None, repr=False)


class SlideExtractor:
    def __init__(self, config: Optional[ExtractorConfig] = None):
        self.config = config or ExtractorConfig()

    # ------------------------------------------------------------------
    def extract(
        self,
        video_path: str,
        output_dir: str,
        progress: Optional[ProgressFn] = None,
    ) -> List[Slide]:
        cfg = self.config
        os.makedirs(output_dir, exist_ok=True)

        # OpenCV's bundled decoder can't handle every codec (notably the
        # AV1 that YouTube uses for long/low-bitrate videos). In that
        # case re-sample the video with the bundled ffmpeg — extracting
        # only 1 frame per analysis interval, which turns hours of
        # transcoding into minutes and is exactly what the analysis
        # needs anyway.
        resampled: Optional[str] = None
        if not self._decodable(video_path):
            resampled = self._ffmpeg_resample(video_path, output_dir,
                                              progress)
            video_path = resampled
        try:
            return self._extract_impl(video_path, output_dir, progress)
        finally:
            if resampled:
                try:
                    os.remove(resampled)
                except OSError:
                    pass

    @staticmethod
    def _decodable(video_path: str) -> bool:
        """True when OpenCV can actually DECODE frames (isOpened alone
        lies: grab() demuxes fine while retrieve() fails on unsupported
        codecs, which used to end analysis instantly with zero slides)."""
        cap = cv2.VideoCapture(video_path)
        try:
            if not cap.isOpened():
                return False
            ok, frame = cap.read()
            return bool(ok and frame is not None)
        finally:
            cap.release()

    _TIME_RE = re.compile(r"time=(\d+):(\d+):(\d+(?:\.\d+)?)")
    _DURATION_RE = re.compile(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)")

    def _ffmpeg_resample(self, video_path: str, output_dir: str,
                         progress: Optional[ProgressFn]) -> str:
        """Re-encode to H.264 at 1 frame per sample interval (original
        resolution, no audio) so any codec becomes analyzable."""
        try:
            import imageio_ffmpeg
            exe = imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            raise RuntimeError(
                "video codec unsupported by OpenCV and ffmpeg is not "
                "available for conversion")
        fps = 1.0 / self.config.sample_interval
        dest = os.path.join(output_dir, "_resampled.mp4")
        proc = subprocess.Popen(
            [exe, "-y", "-i", video_path, "-vf", f"fps={fps}",
             "-an", "-sn", "-c:v", "libx264", "-preset", "ultrafast",
             "-crf", "20", dest],
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True,
            errors="replace")
        duration = 0.0
        buf = ""
        while True:
            chunk = proc.stderr.read(256)
            if not chunk:
                break
            buf += chunk
            if not duration:
                m = self._DURATION_RE.search(buf)
                if m:
                    h, mnt, s = m.groups()
                    duration = int(h) * 3600 + int(mnt) * 60 + float(s)
            for m in self._TIME_RE.finditer(buf):
                h, mnt, s = m.groups()
                t = int(h) * 3600 + int(mnt) * 60 + float(s)
                if progress and duration:
                    progress(min(t / duration, 1.0),
                             "converting unsupported codec")
            buf = buf[-256:]
        proc.wait()
        if proc.returncode != 0 or not os.path.isfile(dest) \
                or os.path.getsize(dest) < 1000 \
                or not self._decodable(dest):
            raise RuntimeError(
                "تعذر فك ترميز الفيديو — الملف تالف أو بترميز غير مدعوم "
                "(could not decode this video even after conversion)")
        return dest

    # ------------------------------------------------------------------
    def _extract_impl(
        self,
        video_path: str,
        output_dir: str,
        progress: Optional[ProgressFn] = None,
    ) -> List[Slide]:
        cfg = self.config

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError(f"could not open video: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        step = max(1, int(round(fps * cfg.sample_interval)))

        prev_small: Optional[np.ndarray] = None
        prev_edges: Optional[np.ndarray] = None

        # Current stability segment state
        seg_len = 0
        seg_last: Optional[Tuple[np.ndarray, float]] = None    # newest frame
        seg_stable: Optional[Tuple[np.ndarray, float]] = None  # newest STABLE frame

        # Candidate slides are spooled to disk immediately: an hours-long
        # lecture can produce hundreds of full-resolution candidates,
        # which must not accumulate in RAM (small cloud containers get
        # OOM-killed otherwise).
        raw_dir = os.path.join(output_dir, ".raw")
        os.makedirs(raw_dir, exist_ok=True)
        raw_slides: List[Tuple[str, float]] = []   # (jpeg path, timestamp)

        def close_segment():
            # Prefer the last stable frame (clean, fully rendered); fall
            # back to the segment's last frame only if it never settled.
            if seg_len >= cfg.min_stable_samples:
                pick = seg_stable or seg_last
                if pick is not None:
                    frame, ts = pick
                    path = os.path.join(raw_dir,
                                        f"raw_{len(raw_slides):05d}.jpg")
                    cv2.imwrite(path, frame,
                                [cv2.IMWRITE_JPEG_QUALITY, cfg.jpeg_quality])
                    raw_slides.append((path, ts))

        frame_idx = 0
        while True:
            # Grab-skip is much faster than decoding every frame.
            ok = cap.grab()
            if not ok:
                break
            if frame_idx % step != 0:
                frame_idx += 1
                continue
            ok, frame = cap.retrieve()
            if not ok:
                break
            timestamp = frame_idx / fps
            frame_idx += 1

            small = self._prepare(frame)
            edges = self._edge_map(small)

            if prev_small is None:
                seg_len = 1
                seg_last = (frame, timestamp)
                seg_stable = None
            else:
                ratio = self._change_ratio(prev_small, small)
                removed = self._removed_fraction(prev_edges, edges)
                if (ratio > cfg.change_ratio_threshold
                        or removed > cfg.removed_edges_threshold):
                    # Content replaced: the previous slide is finished —
                    # emit it in its most complete stable state.
                    close_segment()
                    seg_len = 1
                    seg_stable = None
                else:
                    # Same slide, possibly with more writing on it.
                    seg_len += 1
                    if (ratio < cfg.stable_change_epsilon
                            and removed < cfg.stable_removed_epsilon):
                        seg_stable = (frame, timestamp)
                seg_last = (frame, timestamp)

            prev_small, prev_edges = small, edges

            if progress and total_frames > 0 and frame_idx % (step * 10) == 0:
                progress(min(frame_idx / total_frames, 1.0),
                         f"analyzing {timestamp:.0f}s")

        close_segment()
        cap.release()

        if progress:
            progress(1.0, "deduplicating")
        return self._dedup_and_save(raw_slides, output_dir)

    # ------------------------------------------------------------------
    def _prepare(self, frame: np.ndarray) -> np.ndarray:
        """Downscaled, blurred COLOR image: blur hides cursors, noise and
        compression artifacts; color catches slide changes that keep the
        same brightness (which grayscale misses)."""
        h, w = frame.shape[:2]
        scale = self.config.analysis_width / float(w)
        small = cv2.resize(frame,
                           (self.config.analysis_width, max(1, int(h * scale))))
        return cv2.GaussianBlur(small, (5, 5), 0)

    @staticmethod
    def _edge_map(small: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        return cv2.Canny(gray, 40, 120)

    def _change_ratio(self, a: np.ndarray, b: np.ndarray) -> float:
        diff = cv2.absdiff(a, b).max(axis=2)  # strongest channel per pixel
        changed = np.count_nonzero(diff > self.config.pixel_diff_threshold)
        return changed / diff.size

    @staticmethod
    def _removed_fraction(prev_edges: np.ndarray, edges: np.ndarray) -> float:
        """Share of the previous frame's edge pixels that no longer have
        any edge nearby — i.e. content that was ERASED. Writing scores
        ~0 here; flipping to a new page scores high."""
        prev_count = np.count_nonzero(prev_edges)
        if prev_count < 50:  # nearly blank frame: no reliable signal
            return 0.0
        curr_dilated = cv2.dilate(edges, np.ones((5, 5), np.uint8))
        removed = np.count_nonzero(prev_edges & (curr_dilated == 0))
        return removed / prev_count

    @staticmethod
    def _detail_score(frame: np.ndarray) -> float:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 60, 160)
        return float(np.count_nonzero(edges)) / edges.size

    @staticmethod
    def _color_signature(frame: np.ndarray) -> np.ndarray:
        return cv2.resize(frame, (16, 16)).astype(np.float32)

    # ------------------------------------------------------------------
    def _dedup_and_save(self, raw: List[Tuple[str, float]],
                        output_dir: str) -> List[Slide]:
        """Frames are read back from disk one at a time — memory stays
        flat no matter how many candidates an hours-long video yields."""
        cfg = self.config
        kept: List[Slide] = []
        for raw_path, ts in raw:
            frame = cv2.imread(raw_path)
            if frame is None:
                continue
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            ph = imagehash.phash(Image.fromarray(rgb))
            sig = self._color_signature(frame)
            score = self._detail_score(frame)

            duplicate_of = None
            for s in kept:
                if (ph - s.phash <= cfg.dedup_hash_distance
                        and np.abs(sig - s._sig).mean()
                        <= cfg.dedup_color_distance):
                    duplicate_of = s
                    break

            if duplicate_of is None:
                slide = Slide(index=len(kept), timestamp=ts, path="",
                              detail_score=score, phash=ph)
                slide._raw_path, slide._sig = raw_path, sig
                kept.append(slide)
            elif score > duplicate_of.detail_score:
                # Same slide seen again but with MORE content on it
                # (e.g. lecturer returned and added notes): keep the
                # richer version in the original position.
                duplicate_of.detail_score = score
                duplicate_of.timestamp = ts
                duplicate_of.phash = ph
                duplicate_of._raw_path, duplicate_of._sig = raw_path, sig

        for slide in kept:
            slide.path = os.path.join(output_dir,
                                      f"slide_{slide.index + 1:03d}.jpg")
            os.replace(slide._raw_path, slide.path)  # already q95 JPEG
            del slide._raw_path, slide._sig
        shutil.rmtree(os.path.join(output_dir, ".raw"), ignore_errors=True)
        return kept
