from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.db.models import Transcript, Video, VideoStatus
from app.services.transcription.base import TranscriptionBackend, TranscriptResult
from app.services.transcription.whisper_service import FasterWhisperBackend
from app.utils.ffmpeg import extract_audio

logger = get_logger(__name__)


class TranscriptionService:
    """Orchestrates audio extraction + speech-to-text."""

    def __init__(
        self,
        settings: Settings | None = None,
        backend: TranscriptionBackend | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.backend = backend or FasterWhisperBackend(self.settings)

    def transcribe_video(self, db: Session, video: Video) -> Transcript:
        logger.info("Transcribing video %s", video.id)
        video.status = VideoStatus.TRANSCRIBING.value
        video.error_message = None
        db.commit()

        video_path = Path(video.original_path)
        audio_path = self.settings.temp_dir / f"video_{video.id}_audio.wav"

        try:
            extract_audio(video_path, audio_path, self.settings)
            result = self.backend.transcribe(str(audio_path))
            transcript = self._persist(db, video, result)
        except Exception as exc:
            logger.exception("Transcription failed for video %s", video.id)
            video.status = VideoStatus.FAILED.value
            video.error_message = f"Transcription failed: {exc}"
            db.commit()
            raise
        finally:
            if audio_path.exists():
                try:
                    audio_path.unlink()
                except OSError:
                    logger.warning("Could not delete temp audio %s", audio_path)

        return transcript

    def _persist(self, db: Session, video: Video, result: TranscriptResult) -> Transcript:
        segments_payload = [
            {"start": s.start, "end": s.end, "text": s.text} for s in result.segments
        ]
        transcript_path = self.settings.transcripts_dir / f"video_{video.id}.json"
        transcript_path.write_text(
            json.dumps(
                {
                    "text": result.text,
                    "language": result.language,
                    "segments": segments_payload,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        existing = db.query(Transcript).filter(Transcript.video_id == video.id).one_or_none()
        if existing:
            existing.text = result.text
            existing.segments_json = json.dumps(segments_payload, ensure_ascii=False)
            transcript = existing
        else:
            transcript = Transcript(
                video_id=video.id,
                text=result.text,
                segments_json=json.dumps(segments_payload, ensure_ascii=False),
            )
            db.add(transcript)

        db.commit()
        db.refresh(transcript)
        logger.info(
            "Stored transcript for video %s (%d segments)",
            video.id,
            len(result.segments),
        )
        return transcript
