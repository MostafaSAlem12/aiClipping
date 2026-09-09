from __future__ import annotations

from pathlib import Path

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.utils.ffmpeg import (
    build_center_crop_filter,
    probe_video,
    resolve_ffmpeg,
    run_command,
)

logger = get_logger(__name__)


class RenderingService:
    """Renders vertical 9:16 clips with burned-in subtitles.

    Cropping strategy is intentionally pluggable: MVP uses deterministic
    center crop. Face/speaker-aware crop can replace `_build_crop_filter`
    later without changing callers.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def render_vertical_with_subtitles(
        self,
        *,
        source_path: Path,
        subtitle_path: Path,
        output_path: Path,
        source_width: int | None = None,
        source_height: int | None = None,
    ) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        ffmpeg = resolve_ffmpeg(self.settings)

        if source_width is None or source_height is None:
            meta = probe_video(source_path, self.settings)
            source_width = meta.width
            source_height = meta.height

        crop_filter = self._build_crop_filter(source_width, source_height)
        # Escape path for FFmpeg subtitles filter on Windows.
        sub_escaped = self._escape_subtitles_path(subtitle_path)
        vf = f"{crop_filter},subtitles='{sub_escaped}'"

        logger.info("Rendering 9:16 clip -> %s", output_path)
        cmd = [
            ffmpeg,
            "-y",
            "-i",
            str(source_path),
            "-vf",
            vf,
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
        run_command(cmd, timeout=900)
        return output_path

    def _build_crop_filter(self, src_w: int, src_h: int) -> str:
        """Hook point for future face-aware cropping."""
        return build_center_crop_filter(
            src_w,
            src_h,
            self.settings.output_width,
            self.settings.output_height,
        )

    @staticmethod
    def _escape_subtitles_path(path: Path) -> str:
        # FFmpeg subtitles filter on Windows needs forward slashes and escaped colons/drive.
        text = path.resolve().as_posix()
        text = text.replace(":", r"\:")
        text = text.replace("'", r"\'")
        return text
