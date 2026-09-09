from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ClipCandidateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    video_id: int
    start_time: float
    end_time: float
    title: str
    hook: str
    reason: str
    score: float
    status: str
    created_at: datetime

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time


class GeneratedClipOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    candidate_id: int
    output_path: str
    duration: float | None = None
    status: str
    error_message: str | None = None
    created_at: datetime
    title: str | None = None
    score: float | None = None
