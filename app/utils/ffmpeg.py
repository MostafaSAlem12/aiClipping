from __future__ import annotations

import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from app.core.config import Settings, get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class FFmpegError(RuntimeError):
    """Raised when FFmpeg/ffprobe fails or is unavailable."""


@dataclass(frozen=True)
class VideoMetadata:
    duration: float
    width: int
    height: int
    has_audio: bool
    codec_name: str | None = None


def resolve_ffmpeg(settings: Settings | None = None) -> str:
    settings = settings or get_settings()
    if settings.ffmpeg_path:
        path = Path(settings.ffmpeg_path)
        if not path.exists():
            raise FFmpegError(f"FFMPEG_PATH does not exist: {path}")
        return str(path)
    found = shutil.which("ffmpeg")
    if not found:
        raise FFmpegError(
            "ffmpeg not found. Install FFmpeg and add it to PATH, "
            "or set FFMPEG_PATH in your .env file."
        )
    return found


def resolve_ffprobe(settings: Settings | None = None) -> str:
    settings = settings or get_settings()
    if settings.ffprobe_path:
        path = Path(settings.ffprobe_path)
        if not path.exists():
            raise FFmpegError(f"FFPROBE_PATH does not exist: {path}")
        return str(path)
    found = shutil.which("ffprobe")
    if not found:
        # Common case: only FFMPEG_PATH is set — derive ffprobe sibling.
        if settings.ffmpeg_path:
            sibling = Path(settings.ffmpeg_path).with_name("ffprobe.exe")
            if sibling.exists():
                return str(sibling)
            sibling = Path(settings.ffmpeg_path).with_name("ffprobe")
            if sibling.exists():
                return str(sibling)
        raise FFmpegError(
            "ffprobe not found. Install FFmpeg and add it to PATH, "
            "or set FFPROBE_PATH in your .env file."
        )
    return found


def run_command(cmd: list[str], *, timeout: int | None = None) -> subprocess.CompletedProcess[str]:
    logger.debug("Running command: %s", " ".join(cmd))
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        raise FFmpegError(f"Executable not found: {cmd[0]}") from exc
    except subprocess.TimeoutExpired as exc:
        raise FFmpegError(f"Command timed out: {' '.join(cmd)}") from exc

    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        raise FFmpegError(
            f"Command failed ({result.returncode}): {' '.join(cmd)}\n{stderr}"
        )
    return result


def probe_video(path: Path | str, settings: Settings | None = None) -> VideoMetadata:
    ffprobe = resolve_ffprobe(settings)
    cmd = [
        ffprobe,
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(path),
    ]
    result = run_command(cmd, timeout=60)
    payload = json.loads(result.stdout)

    video_stream = next(
        (s for s in payload.get("streams", []) if s.get("codec_type") == "video"),
        None,
    )
    audio_stream = next(
        (s for s in payload.get("streams", []) if s.get("codec_type") == "audio"),
        None,
    )
    if not video_stream:
        raise FFmpegError(f"No video stream found in {path}")

    duration = float(payload.get("format", {}).get("duration") or video_stream.get("duration") or 0)
    width = int(video_stream.get("width") or 0)
    height = int(video_stream.get("height") or 0)
    if width <= 0 or height <= 0:
        raise FFmpegError(f"Invalid video dimensions for {path}")

    return VideoMetadata(
        duration=duration,
        width=width,
        height=height,
        has_audio=audio_stream is not None,
        codec_name=video_stream.get("codec_name"),
    )


def extract_audio(video_path: Path, audio_path: Path, settings: Settings | None = None) -> Path:
    ffmpeg = resolve_ffmpeg(settings)
    audio_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        ffmpeg,
        "-y",
        "-i",
        str(video_path),
        "-vn",
        "-acodec",
        "pcm_s16le",
        "-ar",
        "16000",
        "-ac",
        "1",
        str(audio_path),
    ]
    run_command(cmd, timeout=600)
    return audio_path


def build_center_crop_filter(src_w: int, src_h: int, out_w: int, out_h: int) -> str:
    """Deterministic center-crop scale filter for 9:16 output.

    Designed so face/speaker-aware cropping can replace this later without
    changing the rendering service contract.
    """
    target_aspect = out_w / out_h
    src_aspect = src_w / src_h

    if src_aspect > target_aspect:
        # Wider than target: crop width, keep full height.
        crop_h = src_h
        crop_w = int(round(src_h * target_aspect))
    else:
        # Taller/narrower: crop height, keep full width.
        crop_w = src_w
        crop_h = int(round(src_w / target_aspect))

    crop_w = max(2, crop_w - (crop_w % 2))
    crop_h = max(2, crop_h - (crop_h % 2))
    x = max(0, (src_w - crop_w) // 2)
    y = max(0, (src_h - crop_h) // 2)

    return (
        f"crop={crop_w}:{crop_h}:{x}:{y},"
        f"scale={out_w}:{out_h}:flags=lanczos,"
        f"setsar=1"
    )


_TIME_RE = re.compile(
    r"(?:(?P<h>\d+):)?(?P<m>\d+):(?P<s>\d+(?:\.\d+)?)$|^(?P<secs>\d+(?:\.\d+)?)$"
)


def parse_timestamp(value: str | float | int) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    text = value.strip()
    match = _TIME_RE.match(text)
    if not match:
        raise ValueError(f"Unrecognized timestamp: {value!r}")
    if match.group("secs") is not None:
        return float(match.group("secs"))
    hours = float(match.group("h") or 0)
    minutes = float(match.group("m") or 0)
    seconds = float(match.group("s") or 0)
    return hours * 3600 + minutes * 60 + seconds
