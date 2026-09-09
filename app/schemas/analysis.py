from __future__ import annotations

from pydantic import BaseModel, Field, field_validator, model_validator


class LLMClipCandidate(BaseModel):
    """Single candidate returned by the LLM — never trust raw JSON."""

    start_time: float = Field(..., ge=0)
    end_time: float = Field(..., ge=0)
    title: str = Field(..., min_length=1, max_length=256)
    hook: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1)
    score: float = Field(..., ge=0, le=10)

    @field_validator("title", "hook", "reason")
    @classmethod
    def _strip_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("field cannot be empty")
        return cleaned

    @model_validator(mode="after")
    def _validate_window(self) -> LLMClipCandidate:
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be greater than start_time")
        return self

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time


class LLMAnalysisResponse(BaseModel):
    candidates: list[LLMClipCandidate] = Field(default_factory=list)
