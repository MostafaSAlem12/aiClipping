from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.db.models import ClipCandidate, CandidateStatus, Video, VideoStatus

logger = get_logger(__name__)


class ClipSelectionService:
    """Selects the strongest validated candidates for rendering."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def select(self, db: Session, video: Video, candidates: list[ClipCandidate]) -> list[ClipCandidate]:
        logger.info("Selecting clips for video %s from %d candidates", video.id, len(candidates))
        video.status = VideoStatus.SELECTING.value
        db.commit()

        scored = []
        for candidate in candidates:
            adjusted = self.score_candidate(candidate)
            scored.append((adjusted, candidate))

        scored.sort(key=lambda item: item[0], reverse=True)

        selected: list[ClipCandidate] = []
        for adjusted_score, candidate in scored:
            if adjusted_score < self.settings.min_candidate_score:
                candidate.status = CandidateStatus.REJECTED.value
                continue
            if self._overlaps_existing(candidate, selected):
                candidate.status = CandidateStatus.REJECTED.value
                continue
            if len(selected) >= self.settings.max_clips_per_video:
                candidate.status = CandidateStatus.REJECTED.value
                continue
            candidate.status = CandidateStatus.SELECTED.value
            selected.append(candidate)

        # Mark remaining as rejected.
        selected_ids = {c.id for c in selected}
        for candidate in candidates:
            if candidate.id not in selected_ids and candidate.status != CandidateStatus.REJECTED.value:
                candidate.status = CandidateStatus.REJECTED.value

        db.commit()
        logger.info("Selected %d clips for video %s", len(selected), video.id)
        return selected

    def score_candidate(self, candidate: ClipCandidate) -> float:
        """Adjust LLM score with soft duration preferences."""
        duration = candidate.end_time - candidate.start_time
        score = float(candidate.score)

        if (
            self.settings.preferred_min_duration
            <= duration
            <= self.settings.preferred_max_duration
        ):
            score += 0.5
        elif duration < self.settings.preferred_min_duration:
            score -= 0.5
        elif duration > self.settings.preferred_max_duration:
            score -= 0.3

        return score

    @staticmethod
    def _overlaps_existing(
        candidate: ClipCandidate,
        selected: list[ClipCandidate],
        *,
        max_overlap_ratio: float = 0.4,
    ) -> bool:
        c_dur = max(candidate.end_time - candidate.start_time, 0.001)
        for other in selected:
            overlap_start = max(candidate.start_time, other.start_time)
            overlap_end = min(candidate.end_time, other.end_time)
            overlap = max(0.0, overlap_end - overlap_start)
            if overlap / c_dur >= max_overlap_ratio:
                return True
        return False
