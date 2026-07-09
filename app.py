"""Video → Slides web app.

Run with:  python app.py   (or: uvicorn app:app --host 0.0.0.0 --port 8000)
"""

from __future__ import annotations

import os

import shutil
import uuid

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from slide_extractor import probe_video
from slide_extractor.jobs import JobManager

app = FastAPI(title="Video to Slides", version="1.0.0")
manager = JobManager(root=os.environ.get("OUTPUT_DIR", "output"))

BASE = os.path.dirname(os.path.abspath(__file__))


class CreateJobRequest(BaseModel):
    url: str = Field(..., min_length=8, description="YouTube (or any) video URL")
    sensitivity: str = Field("medium", pattern="^(low|medium|high)$")
    max_height: int = Field(1080, ge=144, le=2160)


class CustomPdfRequest(BaseModel):
    selected: list[int]


class ProbeRequest(BaseModel):
    url: str = Field(..., min_length=8)


@app.post("/api/probe")
def probe(req: ProbeRequest):
    """Read title, duration and the REAL available qualities of a video
    without downloading it."""
    try:
        return probe_video(req.url)
    except Exception as exc:
        raise HTTPException(502, str(exc))


@app.post("/api/jobs")
def create_job(req: CreateJobRequest):
    job = manager.create(req.url, req.sensitivity, req.max_height)
    return job.public()


@app.post("/api/jobs/upload")
async def create_upload_job(file: UploadFile = File(...),
                            sensitivity: str = Form("medium")):
    if sensitivity not in ("low", "medium", "high"):
        raise HTTPException(400, "bad sensitivity")
    uploads = os.path.join(manager.root, "uploads")
    os.makedirs(uploads, exist_ok=True)
    ext = os.path.splitext(file.filename or "video.mp4")[1] or ".mp4"
    path = os.path.join(uploads, uuid.uuid4().hex[:12] + ext)
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    title = os.path.splitext(os.path.basename(file.filename or "video"))[0]
    job = manager.create_from_file(path, title=title, sensitivity=sensitivity)
    return job.public()


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str):
    job = manager.get(job_id)
    if not job:
        raise HTTPException(404, "job not found")
    return job.public()


@app.get("/api/jobs/{job_id}/slides/{filename}")
def get_slide(job_id: str, filename: str):
    job = manager.get(job_id)
    if not job:
        raise HTTPException(404, "job not found")
    if filename != os.path.basename(filename):
        raise HTTPException(400, "bad filename")
    path = os.path.join(job.workdir, "slides", filename)
    if not os.path.isfile(path):
        raise HTTPException(404, "slide not found")
    return FileResponse(path, media_type="image/jpeg")


def _download(job_id: str, name: str, media: str, download_name: str):
    job = manager.get(job_id)
    if not job:
        raise HTTPException(404, "job not found")
    path = os.path.join(job.workdir, name)
    if not os.path.isfile(path):
        raise HTTPException(404, "not ready")
    safe_title = "".join(
        c for c in (job.title or "slides") if c.isalnum() or c in " -_"
    ).strip() or "slides"
    return FileResponse(path, media_type=media,
                        filename=f"{safe_title}{download_name}")


@app.get("/api/jobs/{job_id}/pdf")
def get_pdf(job_id: str):
    return _download(job_id, "slides.pdf", "application/pdf", ".pdf")


@app.get("/api/jobs/{job_id}/zip")
def get_zip(job_id: str):
    return _download(job_id, "slides.zip", "application/zip", "_slides.zip")


@app.post("/api/jobs/{job_id}/pdf")
def custom_pdf(job_id: str, req: CustomPdfRequest):
    job = manager.get(job_id)
    if not job:
        raise HTTPException(404, "job not found")
    if job.status != "done":
        raise HTTPException(409, "job not finished")
    try:
        manager.build_custom_pdf(job, req.selected)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"url": f"/api/jobs/{job_id}/pdf/custom"}


@app.get("/api/jobs/{job_id}/pdf/custom")
def get_custom_pdf(job_id: str):
    return _download(job_id, "slides_custom.pdf", "application/pdf",
                     "_selected.pdf")


app.mount("/", StaticFiles(directory=os.path.join(BASE, "static"), html=True),
          name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
