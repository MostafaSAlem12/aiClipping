from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import ClipCandidate, GeneratedClip, Transcript, Video, VideoStatus
from app.schemas.clip import ClipCandidateOut, GeneratedClipOut
from app.schemas.video import ProcessResponse, VideoDetail, VideoSummary
from app.services.ingestion.service import VideoIngestionService
from app.workers.jobs import job_manager

router = APIRouter(prefix="/api/videos", tags=["videos"])

ALLOWED_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v"}


@router.post("/upload", response_model=VideoSummary)
async def upload_video(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> Video:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{suffix}'. Allowed: {sorted(ALLOWED_EXTENSIONS)}",
        )

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

    return video


@router.get("", response_model=list[VideoSummary])
def list_videos(db: Session = Depends(get_db)) -> list[Video]:
    return db.query(Video).order_by(Video.created_at.desc()).all()


@router.get("/{video_id}", response_model=VideoDetail)
def get_video(video_id: int, db: Session = Depends(get_db)) -> VideoDetail:
    video = db.get(Video, video_id)
    if video is None:
        raise HTTPException(status_code=404, detail="Video not found")

    has_transcript = (
        db.query(Transcript).filter(Transcript.video_id == video_id).count() > 0
    )
    candidate_count = (
        db.query(ClipCandidate).filter(ClipCandidate.video_id == video_id).count()
    )
    clip_count = (
        db.query(GeneratedClip)
        .join(ClipCandidate, GeneratedClip.candidate_id == ClipCandidate.id)
        .filter(ClipCandidate.video_id == video_id)
        .count()
    )
    return VideoDetail(
        id=video.id,
        filename=video.filename,
        original_path=video.original_path,
        duration=video.duration,
        width=video.width,
        height=video.height,
        status=video.status,
        error_message=video.error_message,
        created_at=video.created_at,
        has_transcript=has_transcript,
        candidate_count=candidate_count,
        clip_count=clip_count,
    )


@router.post("/{video_id}/process", response_model=ProcessResponse)
def process_video(video_id: int, db: Session = Depends(get_db)) -> ProcessResponse:
    video = db.get(Video, video_id)
    if video is None:
        raise HTTPException(status_code=404, detail="Video not found")

    if job_manager.is_running(video_id):
        return ProcessResponse(
            video_id=video_id,
            status=video.status,
            message="Pipeline already running for this video.",
        )

    terminal_busy = {
        VideoStatus.QUEUED.value,
        VideoStatus.INGESTING.value,
        VideoStatus.TRANSCRIBING.value,
        VideoStatus.ANALYZING.value,
        VideoStatus.SELECTING.value,
        VideoStatus.CLIPPING.value,
        VideoStatus.RENDERING.value,
    }
    if video.status in terminal_busy:
        return ProcessResponse(
            video_id=video_id,
            status=video.status,
            message="Video is already being processed.",
        )

    submitted = job_manager.submit_pipeline(video_id)
    if not submitted:
        raise HTTPException(status_code=409, detail="Could not queue pipeline job")

    video.status = VideoStatus.QUEUED.value
    video.error_message = None
    db.commit()

    return ProcessResponse(
        video_id=video_id,
        status=VideoStatus.QUEUED.value,
        message="Pipeline queued. Refresh this page to track progress.",
    )


@router.get("/{video_id}/candidates", response_model=list[ClipCandidateOut])
def list_candidates(video_id: int, db: Session = Depends(get_db)) -> list[ClipCandidate]:
    video = db.get(Video, video_id)
    if video is None:
        raise HTTPException(status_code=404, detail="Video not found")
    return (
        db.query(ClipCandidate)
        .filter(ClipCandidate.video_id == video_id)
        .order_by(ClipCandidate.score.desc())
        .all()
    )


@router.get("/{video_id}/clips", response_model=list[GeneratedClipOut])
def list_clips(video_id: int, db: Session = Depends(get_db)) -> list[GeneratedClipOut]:
    video = db.get(Video, video_id)
    if video is None:
        raise HTTPException(status_code=404, detail="Video not found")

    rows = (
        db.query(GeneratedClip, ClipCandidate)
        .join(ClipCandidate, GeneratedClip.candidate_id == ClipCandidate.id)
        .filter(ClipCandidate.video_id == video_id)
        .order_by(ClipCandidate.score.desc())
        .all()
    )
    return [
        GeneratedClipOut(
            id=clip.id,
            candidate_id=clip.candidate_id,
            output_path=clip.output_path,
            duration=clip.duration,
            status=clip.status,
            error_message=clip.error_message,
            created_at=clip.created_at,
            title=candidate.title,
            score=candidate.score,
        )
        for clip, candidate in rows
    ]
