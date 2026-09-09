from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import ClipCandidate, GeneratedClip, Transcript, Video, VideoStatus
from app.services.ingestion.service import VideoIngestionService
from app.workers.jobs import job_manager

router = APIRouter(tags=["dashboard"])

TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

ALLOWED_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v"}


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    videos = db.query(Video).order_by(Video.created_at.desc()).all()
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {"videos": videos, "error": None},
    )


@router.get("/videos/{video_id}", response_class=HTMLResponse)
def video_detail(request: Request, video_id: int, db: Session = Depends(get_db)) -> HTMLResponse:
    video = db.get(Video, video_id)
    if video is None:
        videos = db.query(Video).order_by(Video.created_at.desc()).all()
        return templates.TemplateResponse(
            request,
            "dashboard.html",
            {"videos": videos, "error": f"Video {video_id} not found"},
            status_code=404,
        )

    transcript = (
        db.query(Transcript).filter(Transcript.video_id == video_id).one_or_none()
    )
    candidates = (
        db.query(ClipCandidate)
        .filter(ClipCandidate.video_id == video_id)
        .order_by(ClipCandidate.score.desc())
        .all()
    )
    clips = (
        db.query(GeneratedClip, ClipCandidate)
        .join(ClipCandidate, GeneratedClip.candidate_id == ClipCandidate.id)
        .filter(ClipCandidate.video_id == video_id)
        .order_by(ClipCandidate.score.desc())
        .all()
    )
    return templates.TemplateResponse(
        request,
        "video_detail.html",
        {
            "video": video,
            "transcript": transcript,
            "candidates": candidates,
            "clips": clips,
            "is_running": job_manager.is_running(video_id),
        },
    )


@router.post("/videos/{video_id}/process")
def dashboard_process(video_id: int, db: Session = Depends(get_db)) -> RedirectResponse:
    video = db.get(Video, video_id)
    if video is not None and not job_manager.is_running(video_id):
        if job_manager.submit_pipeline(video_id):
            video.status = VideoStatus.QUEUED.value
            video.error_message = None
            db.commit()
    return RedirectResponse(url=f"/videos/{video_id}", status_code=303)


@router.post("/upload")
async def dashboard_upload(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    if not file.filename:
        return RedirectResponse(url="/?error=missing_filename", status_code=303)

    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        return RedirectResponse(url="/?error=unsupported_type", status_code=303)

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp_path = Path(tmp.name)
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            tmp.write(chunk)

    try:
        service = VideoIngestionService()
        video = service.save_upload(db, filename=file.filename, source=tmp_path)
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass

    return RedirectResponse(url=f"/videos/{video.id}", status_code=303)
