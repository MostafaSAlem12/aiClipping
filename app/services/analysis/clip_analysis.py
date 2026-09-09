from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.db.models import ClipCandidate, CandidateStatus, Transcript, Video, VideoStatus
from app.schemas.analysis import LLMAnalysisResponse, LLMClipCandidate
from app.services.analysis.ollama_client import OllamaClient, OllamaError, extract_json_object

logger = get_logger(__name__)

PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "clip_analysis.txt"


class ClipAnalysisService:
    """Sends transcript to Ollama and validates candidate JSON."""

    def __init__(
        self,
        settings: Settings | None = None,
        client: OllamaClient | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.client = client or OllamaClient(self.settings)
        self._prompt_template = PROMPT_PATH.read_text(encoding="utf-8")

    def analyze(self, db: Session, video: Video, transcript: Transcript) -> list[ClipCandidate]:
        logger.info("Analyzing transcript for video %s", video.id)
        video.status = VideoStatus.ANALYZING.value
        db.commit()

        prompt = self._build_prompt(transcript)
        try:
            raw = self.client.generate(prompt)
            candidates = self.parse_and_validate(raw, video_duration=video.duration)
        except (OllamaError, ValidationError, ValueError, json.JSONDecodeError) as exc:
            logger.exception("Analysis failed for video %s", video.id)
            video.status = VideoStatus.FAILED.value
            video.error_message = f"Analysis failed: {exc}"
            db.commit()
            raise

        # Replace previous candidates on reprocess.
        db.query(ClipCandidate).filter(ClipCandidate.video_id == video.id).delete()
        db.commit()

        rows: list[ClipCandidate] = []
        for item in candidates:
            row = ClipCandidate(
                video_id=video.id,
                start_time=item.start_time,
                end_time=item.end_time,
                title=item.title,
                hook=item.hook,
                reason=item.reason,
                score=item.score,
                status=CandidateStatus.PENDING.value,
            )
            db.add(row)
            rows.append(row)

        db.commit()
        for row in rows:
            db.refresh(row)

        logger.info("Stored %d raw candidates for video %s", len(rows), video.id)
        return rows

    def _build_prompt(self, transcript: Transcript) -> str:
        segments = json.loads(transcript.segments_json)
        lines = []
        for seg in segments:
            start = float(seg["start"])
            end = float(seg["end"])
            text = str(seg["text"]).strip()
            lines.append(f"[{start:.2f}-{end:.2f}] {text}")
        stamped = "\n".join(lines) if lines else transcript.text
        return self._prompt_template.replace("{{TRANSCRIPT}}", stamped)

    def parse_and_validate(
        self,
        raw: str,
        *,
        video_duration: float | None = None,
    ) -> list[LLMClipCandidate]:
        payload = extract_json_object(raw)
        parsed = LLMAnalysisResponse.model_validate(payload)

        valid: list[LLMClipCandidate] = []
        for candidate in parsed.candidates:
            duration = candidate.duration
            if duration < self.settings.min_clip_duration:
                logger.info(
                    "Dropping candidate (too short %.2fs): %s",
                    duration,
                    candidate.title,
                )
                continue
            if duration > self.settings.max_clip_duration:
                logger.info(
                    "Dropping candidate (too long %.2fs): %s",
                    duration,
                    candidate.title,
                )
                continue
            if video_duration is not None:
                if candidate.start_time >= video_duration:
                    logger.info("Dropping candidate past video end: %s", candidate.title)
                    continue
                if candidate.end_time > video_duration + 1.0:
                    # Clamp slight overruns; reject large ones.
                    if candidate.end_time > video_duration + 5.0:
                        logger.info(
                            "Dropping candidate beyond duration: %s",
                            candidate.title,
                        )
                        continue
                    candidate = candidate.model_copy(
                        update={"end_time": min(candidate.end_time, video_duration)}
                    )
            valid.append(candidate)

        if not valid:
            raise ValueError("LLM returned no valid clip candidates after validation")
        return valid
