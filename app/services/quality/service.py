from __future__ import annotations

from pathlib import Path

from app.core.logging import get_logger
from app.utils.ffmpeg import probe_video

logger = get_logger(__name__)


class QualityService:
    """Lightweight output checks for the MVP."""

    def validate_clip(
        self,
        path: Path,
        *,
        expected_min_duration: float,
        expected_max_duration: float,
        expected_width: int,
        expected_height: int,
    ) -> dict:
        if not path.exists():
            raise FileNotFoundError(f"Generated clip missing: {path}")

        meta = probe_video(path)
        issues: list[str] = []

        if meta.duration < expected_min_duration - 0.5:
            issues.append(
                f"duration too short: {meta.duration:.2f}s < {expected_min_duration}s"
            )
        if meta.duration > expected_max_duration + 1.0:
            issues.append(
                f"duration too long: {meta.duration:.2f}s > {expected_max_duration}s"
            )
        if meta.width != expected_width or meta.height != expected_height:
            issues.append(
                f"unexpected dimensions: {meta.width}x{meta.height} "
                f"(expected {expected_width}x{expected_height})"
            )
        if not meta.has_audio:
            issues.append("missing audio stream")

        ok = not issues
        result = {
            "ok": ok,
            "duration": meta.duration,
            "width": meta.width,
            "height": meta.height,
            "has_audio": meta.has_audio,
            "issues": issues,
        }
        if ok:
            logger.info("Quality check passed for %s", path)
        else:
            logger.warning("Quality check issues for %s: %s", path, issues)
        return result
