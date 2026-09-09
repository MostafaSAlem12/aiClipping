from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class VideoSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    duration: float | None = None
    width: int | None = None
    height: int | None = None
    status: str
    error_message: str | None = None
    created_at: datetime


class VideoDetail(VideoSummary):
    original_path: str
    has_transcript: bool = False
    candidate_count: int = 0
    clip_count: int = 0


class ProcessResponse(BaseModel):
    video_id: int
    status: str
    message: str


class TranscriptSegment(BaseModel):
    start: float = Field(..., ge=0)
    end: float = Field(..., ge=0)
    text: str

    def model_post_init(self, __context: object) -> None:  # noqa: N805
        if self.end < self.start:
            raise ValueError("segment end must be >= start")


class TranscriptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    video_id: int
    text: str
    created_at: datetime
