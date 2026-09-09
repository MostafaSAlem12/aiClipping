from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import ClipCandidate, GeneratedClip

router = APIRouter(prefix="/api/clips", tags=["clips"])


@router.get("/{clip_id}/download")
def download_clip(clip_id: int, db: Session = Depends(get_db)) -> FileResponse:
    clip = db.get(GeneratedClip, clip_id)
    if clip is None:
        raise HTTPException(status_code=404, detail="Clip not found")

    path = Path(clip.output_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Clip file missing on disk")

    candidate = db.get(ClipCandidate, clip.candidate_id)
    download_name = f"clip_{clip_id}.mp4"
    if candidate is not None:
        safe_title = "".join(
            ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in candidate.title
        )[:60]
        download_name = f"{safe_title or 'clip'}_{clip_id}.mp4"

    return FileResponse(
        path=path,
        media_type="video/mp4",
        filename=download_name,
    )
