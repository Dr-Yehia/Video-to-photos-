"""In-process job manager: each conversion runs in a background thread and
reports progress that the web UI polls."""

from __future__ import annotations

import os
import shutil
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .downloader import download_video
from .extractor import ExtractorConfig, SlideExtractor
from .pdf_builder import build_pdf, build_zip


@dataclass
class Job:
    id: str
    url: str                        # source URL, or "" for uploaded files
    local_path: str = ""            # set instead of url for uploaded files
    sensitivity: str = "medium"
    max_height: int = 1080
    status: str = "queued"          # queued/downloading/extracting/done/error
    progress: float = 0.0
    message: str = ""
    title: str = ""
    error: str = ""
    slides: List[dict] = field(default_factory=list)
    workdir: str = ""
    created_at: float = field(default_factory=time.time)

    def public(self) -> dict:
        return {
            "id": self.id,
            "url": self.url,
            "status": self.status,
            "progress": round(self.progress, 3),
            "message": self.message,
            "title": self.title,
            "error": self.error,
            "slides": self.slides,
        }


class JobManager:
    def __init__(self, root: str = "output", max_jobs_kept: int = 20):
        self.root = root
        self.max_jobs_kept = max_jobs_kept
        self.jobs: Dict[str, Job] = {}
        self._lock = threading.Lock()
        os.makedirs(root, exist_ok=True)

    def create(self, url: str, sensitivity: str = "medium",
               max_height: int = 1080) -> Job:
        return self._start(Job(id=uuid.uuid4().hex[:12], url=url,
                               sensitivity=sensitivity,
                               max_height=max_height))

    def create_from_file(self, local_path: str, title: str,
                         sensitivity: str = "medium") -> Job:
        job = Job(id=uuid.uuid4().hex[:12], url="", local_path=local_path,
                  sensitivity=sensitivity, title=title)
        return self._start(job)

    def _start(self, job: Job) -> Job:
        job.workdir = os.path.join(self.root, job.id)
        os.makedirs(job.workdir, exist_ok=True)
        with self._lock:
            self.jobs[job.id] = job
            self._evict_old()
        threading.Thread(target=self._run, args=(job,), daemon=True).start()
        return job


    def get(self, job_id: str) -> Optional[Job]:
        return self.jobs.get(job_id)

    # ------------------------------------------------------------------
    def _run(self, job: Job):
        try:
            if job.local_path:
                video_path = job.local_path
                remove_video = job.local_path.startswith(self.root)
            else:
                job.status = "downloading"
                job.message = "downloading video"

                def dl_progress(p, msg):
                    job.progress = p * 0.4  # download = first 40%
                    job.message = msg

                info = download_video(job.url, job.workdir,
                                      max_height=job.max_height,
                                      progress=dl_progress)
                job.title = info["title"]
                video_path = info["path"]
                remove_video = True

            job.status = "extracting"
            job.message = "extracting slides"

            def ex_progress(p, msg):
                job.progress = 0.4 + p * 0.55  # extraction = next 55%
                job.message = msg

            extractor = SlideExtractor(
                ExtractorConfig.from_sensitivity(job.sensitivity))
            slides_dir = os.path.join(job.workdir, "slides")
            slides = extractor.extract(video_path, slides_dir,
                                       progress=ex_progress)
            if not slides:
                raise RuntimeError("no slides detected in this video")

            job.slides = [
                {"index": s.index, "timestamp": round(s.timestamp, 1),
                 "file": os.path.basename(s.path)}
                for s in slides
            ]

            job.message = "building PDF"
            paths = [os.path.join(slides_dir, s["file"]) for s in job.slides]
            build_pdf(paths, os.path.join(job.workdir, "slides.pdf"))
            build_zip(paths, os.path.join(job.workdir, "slides.zip"))

            # The downloaded/uploaded video can be large — remove it once
            # done (never touch files outside our output root).
            if remove_video:
                try:
                    os.remove(video_path)
                except OSError:
                    pass

            job.progress = 1.0
            job.status = "done"
            job.message = f"{len(job.slides)} slides extracted"
        except Exception as exc:  # surfaced to the UI
            job.status = "error"
            job.error = str(exc)
            job.message = "failed"

    def build_custom_pdf(self, job: Job, selected: List[int]) -> str:
        """PDF from a user-chosen subset of slides (order preserved)."""
        slides_dir = os.path.join(job.workdir, "slides")
        chosen = [s for s in job.slides if s["index"] in set(selected)]
        if not chosen:
            raise ValueError("no slides selected")
        paths = [os.path.join(slides_dir, s["file"]) for s in chosen]
        out = os.path.join(job.workdir, "slides_custom.pdf")
        return build_pdf(paths, out)

    def _evict_old(self):
        if len(self.jobs) <= self.max_jobs_kept:
            return
        for job_id in sorted(self.jobs, key=lambda j: self.jobs[j].created_at)[
                : len(self.jobs) - self.max_jobs_kept]:
            job = self.jobs.pop(job_id)
            shutil.rmtree(job.workdir, ignore_errors=True)
