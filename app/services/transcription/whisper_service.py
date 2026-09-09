from __future__ import annotations

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.services.transcription.base import (
    TranscriptionBackend,
    TranscriptResult,
    TranscriptSegmentData,
)

logger = get_logger(__name__)


class FasterWhisperBackend(TranscriptionBackend):
    """GPU-capable transcription via faster-whisper."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._model = None

    def _load_model(self):
        if self._model is not None:
            return self._model

        from faster_whisper import WhisperModel

        device = self.settings.whisper_device
        compute_type = self.settings.whisper_compute_type
        model_size = self.settings.whisper_model

        logger.info(
            "Loading faster-whisper model=%s device=%s compute_type=%s",
            model_size,
            device,
            compute_type,
        )
        try:
            self._model = WhisperModel(
                model_size,
                device=device,
                compute_type=compute_type,
            )
        except Exception as cuda_exc:
            if device == "cpu":
                raise
            logger.warning(
                "CUDA whisper load failed (%s); falling back to CPU int8",
                cuda_exc,
            )
            self._model = WhisperModel(
                model_size,
                device="cpu",
                compute_type="int8",
            )
        return self._model

    def transcribe(self, audio_or_video_path: str) -> TranscriptResult:
        model = self._load_model()
        language = self.settings.whisper_language or None

        segments_iter, info = model.transcribe(
            audio_or_video_path,
            language=language,
            beam_size=5,
            vad_filter=True,
        )

        segments: list[TranscriptSegmentData] = []
        texts: list[str] = []
        for segment in segments_iter:
            text = segment.text.strip()
            if not text:
                continue
            segments.append(
                TranscriptSegmentData(
                    start=float(segment.start),
                    end=float(segment.end),
                    text=text,
                )
            )
            texts.append(text)

        full_text = " ".join(texts).strip()
        detected = getattr(info, "language", None)
        logger.info(
            "Transcription complete: %d segments, language=%s",
            len(segments),
            detected,
        )
        return TranscriptResult(text=full_text, segments=segments, language=detected)
