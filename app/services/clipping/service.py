from __future__ import annotations

from pathlib import Path

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.utils.ffmpeg import resolve_ffmpeg, run_command

logger = get_logger(__name__)


class VideoClipService:
    """Cuts time ranges from the source video (audio preserved)."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def extract_segment(
        self,
        *,
        source_path: Path,
        output_path: Path,
        start_time: float,
        end_time: float,
    ) -> Path:
        if end_time <= start_time:
            raise ValueError("end_time must be greater than start_time")

        duration = end_time - start_time
        output_path.parent.mkdir(parents=True, exist_ok=True)
        ffmpeg = resolve_ffmpeg(self.settings)

        logger.info(
            "Extracting clip %.2f-%.2f (%.2fs) -> %s",
            start_time,
            end_time,
            duration,
            output_path,
        )
        # Re-encode for accurate cuts (stream copy can miss keyframes).
        cmd = [
            ffmpeg,
            "-y",
            "-ss",
            f"{start_time:.3f}",
            "-i",
            str(source_path),
            "-t",
            f"{duration:.3f}",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "18",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            str(output_path),
        ]
        run_command(cmd, timeout=600)
        return output_path
