from __future__ import annotations

from types import SimpleNamespace

from app.core.config import Settings
from app.services.analysis.clip_selection import ClipSelectionService


def _candidate(**kwargs):
    defaults = {
        "id": 1,
        "start_time": 10.0,
        "end_time": 40.0,
        "score": 8.0,
        "status": "pending",
        "title": "t",
        "hook": "h",
        "reason": "r",
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_prefers_preferred_duration():
    settings = Settings(
        preferred_min_duration=20,
        preferred_max_duration=90,
        min_candidate_score=0,
        max_clips_per_video=5,
    )
    service = ClipSelectionService(settings)
    short = _candidate(id=1, start_time=0, end_time=12, score=8.0)
    good = _candidate(id=2, start_time=20, end_time=50, score=8.0)
    assert service.score_candidate(good) > service.score_candidate(short)


def test_overlap_detection():
    a = _candidate(id=1, start_time=0, end_time=30)
    b = _candidate(id=2, start_time=10, end_time=40)
    c = _candidate(id=3, start_time=100, end_time=130)
    assert ClipSelectionService._overlaps_existing(b, [a]) is True
    assert ClipSelectionService._overlaps_existing(c, [a]) is False
