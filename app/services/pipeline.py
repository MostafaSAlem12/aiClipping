from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.db.models import (
    CandidateStatus,
    ClipStatus,
    GeneratedClip,
    Transcript,
    Video,
    VideoStatus,
)
from app.services.analysis.clip_analysis import ClipAnalysisService
from app.services.analysis.clip_selection import ClipSelectionService
from app.services.clipping.service import VideoClipService
from app.services.ingestion.service import VideoIngestionService
from app.services.quality.service import QualityService
from app.services.rendering.service import RenderingService
from app.services.subtitles.service import SubtitleService
from app.services.transcription.service import TranscriptionService

logger = get_logger(__name__)


class PipelineService:
    """End-to-end video -> short clips pipeline."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.ingestion = VideoIngestionService(self.settings)
        self.transcription = TranscriptionService(self.settings)
        self.analysis = ClipAnalysisService(self.settings)
        self.selection = ClipSelectionService(self.settings)
        self.clipping = VideoClipService(self.settings)
        self.subtitles = SubtitleService()
        self.rendering = RenderingService(self.settings)
        self.quality = QualityService()

    def run(self, db: Session, video_id: int) -> Video:
        video = db.get(Video, video_id)
        if video is None:
            raise ValueError(f"Video {video_id} not found")

        logger.info("Starting pipeline for video %s (%s)", video.id, video.filename)
        video.error_message = None
        db.commit()

        try:
            video = self.ingestion.enrich_metadata(db, video)
            transcript = self.transcription.transcribe_video(db, video)
            candidates = self.analysis.analyze(db, video, transcript)
            selected = self.selection.select(db, video, candidates)

            if not selected:
                video.status = VideoStatus.FAILED.value
                video.error_message = "No candidates met the selection criteria."
                db.commit()
                return video

            video.status = VideoStatus.CLIPPING.value
            db.commit()
            self._render_selected(db, video, transcript, selected)

            video.status = VideoStatus.COMPLETED.value
            video.error_message = None
            db.commit()
            logger.info("Pipeline completed for video %s", video.id)
            return video
        except Exception as exc:
            logger.exception("Pipeline failed for video %s", video_id)
            video = db.get(Video, video_id)
            if video is not None:
                if video.status != VideoStatus.FAILED.value:
                    video.status = VideoStatus.FAILED.value
                if not video.error_message:
                    video.error_message = str(exc)
                db.commit()
            raise

    def _render_selected(
        self,
        db: Session,
        video: Video,
        transcript: Transcript,
        selected: list,
    ) -> None:
        video.status = VideoStatus.RENDERING.value
        db.commit()

        source = Path(video.original_path)
        segments = self.subtitles.load_segments_json(transcript.segments_json)
        clip_dir = self.settings.clips_dir / f"video_{video.id}"
        clip_dir.mkdir(parents=True, exist_ok=True)

        for candidate in selected:
            temp_cut = self.settings.temp_dir / f"cut_{video.id}_{candidate.id}.mp4"
            srt_path = clip_dir / f"candidate_{candidate.id}.srt"
            output_path = clip_dir / f"clip_{candidate.id}.mp4"

            generated = (
                db.query(GeneratedClip)
                .filter(GeneratedClip.candidate_id == candidate.id)
                .one_or_none()
            )
            if generated is None:
                generated = GeneratedClip(
                    candidate_id=candidate.id,
                    output_path=str(output_path),
                    status=ClipStatus.PROCESSING.value,
                )
                db.add(generated)
            else:
                generated.output_path = str(output_path)
                generated.status = ClipStatus.PROCESSING.value
                generated.error_message = None
            db.commit()

            try:
                self.clipping.extract_segment(
                    source_path=source,
                    output_path=temp_cut,
                    start_time=candidate.start_time,
                    end_time=candidate.end_time,
                )

                windowed = self.subtitles.segments_for_window(
                    segments,
                    start_time=candidate.start_time,
                    end_time=candidate.end_time,
                )
                self.subtitles.write_srt(windowed, srt_path)
                # Prefer ASS for styled burn-in when possible; SRT is fine for MVP.
                ass_path = clip_dir / f"candidate_{candidate.id}.ass"
                self.subtitles.write_ass(
                    windowed,
                    ass_path,
                    play_res_x=self.settings.output_width,
                    play_res_y=self.settings.output_height,
                    font_size=self.settings.subtitle_font_size,
                )

                self.rendering.render_vertical_with_subtitles(
                    source_path=temp_cut,
                    subtitle_path=ass_path,
                    output_path=output_path,
                    source_width=video.width,
                    source_height=video.height,
                )

                duration = candidate.end_time - candidate.start_time
                quality = self.quality.validate_clip(
                    output_path,
                    expected_min_duration=self.settings.min_clip_duration,
                    expected_max_duration=self.settings.max_clip_duration,
                    expected_width=self.settings.output_width,
                    expected_height=self.settings.output_height,
                )

                generated.duration = float(quality["duration"])
                if quality["ok"]:
                    generated.status = ClipStatus.COMPLETED.value
                    candidate.status = CandidateStatus.RENDERED.value
                else:
                    generated.status = ClipStatus.COMPLETED.value
                    generated.error_message = "; ".join(quality["issues"])
                    candidate.status = CandidateStatus.RENDERED.value
                db.commit()
            except Exception as exc:
                logger.exception(
                    "Failed rendering candidate %s for video %s",
                    candidate.id,
                    video.id,
                )
                generated.status = ClipStatus.FAILED.value
                generated.error_message = str(exc)
                candidate.status = CandidateStatus.FAILED.value
                db.commit()
            finally:
                if temp_cut.exists():
                    try:
                        temp_cut.unlink()
                    except OSError:
                        logger.warning("Could not delete temp cut %s", temp_cut)
