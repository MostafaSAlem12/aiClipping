from __future__ import annotations


def format_timestamp(seconds: float, *, srt: bool = True) -> str:
    """Format seconds as SRT (comma) or ASS (dot) timestamp."""
    if seconds < 0:
        seconds = 0.0
    total_ms = int(round(seconds * 1000))
    hours, rem = divmod(total_ms, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    secs, millis = divmod(rem, 1000)
    sep = "," if srt else "."
    return f"{hours:02d}:{minutes:02d}:{secs:02d}{sep}{millis:03d}"


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))
