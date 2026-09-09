from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TranscriptSegmentData:
    start: float
    end: float
    text: str


@dataclass
class TranscriptResult:
    text: str
    segments: list[TranscriptSegmentData]
    language: str | None = None


class TranscriptionBackend:
    """Replaceable transcription interface."""

    def transcribe(self, audio_or_video_path: str) -> TranscriptResult:
        raise NotImplementedError
