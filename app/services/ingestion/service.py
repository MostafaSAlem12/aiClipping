from __future__ import annotations

import shutil
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.db.models import Video, VideoStatus
from app.utils.ffmpeg import FFmpegError, probe_video
from app.utils.files import safe_filename, unique_path

logger = get_logger(__name__)


class VideoIngestionService:
    """Stores uploads and extracts basic video metadata."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def save_upload(self, db: Session, *, filename: str, source: Path) -> Video:
        safe_name = safe_filename(filename)
        destination = unique_path(self.settings.uploads_dir, safe_name)
        shutil.copy2(source, destination)
        logger.info("Stored upload %s -> %s", filename, destination)

        video = Video(
            filename=safe_name,
            original_path=str(destination),
            status=VideoStatus.UPLOADED.value,
        )
        db.add(video)
        db.commit()
        db.refresh(video)
        return video

    def enrich_metadata(self, db: Session, video: Video) -> Video:
        logger.info("Extracting metadata for video %s", video.id)
        video.status = VideoStatus.INGESTING.value
        db.commit()

        path = Path(video.original_path)
        if not path.exists():
            raise FileNotFoundError(f"Video file missing: {path}")

        try:
            meta = probe_video(path, self.settings)
        except FFmpegError:
            video.status = VideoStatus.FAILED.value
            video.error_message = "FFmpeg/ffprobe is required to read video metadata."
            db.commit()
            raise

        video.duration = meta.duration
        video.width = meta.width
        video.height = meta.height
        db.commit()
        db.refresh(video)
        logger.info(
            "Video %s metadata: %.2fs %sx%s",
            video.id,
            meta.duration,
            meta.width,
            meta.height,
        )
        return video
