from __future__ import annotations

import json
from pathlib import Path

from app.core.logging import get_logger
from app.utils.time import clamp, format_timestamp

logger = get_logger(__name__)


class SubtitleService:
    """Builds SRT/ASS subtitle files from transcript segment timestamps."""

    def segments_for_window(
        self,
        segments: list[dict],
        *,
        start_time: float,
        end_time: float,
    ) -> list[dict]:
        windowed: list[dict] = []
        for seg in segments:
            seg_start = float(seg["start"])
            seg_end = float(seg["end"])
            text = str(seg.get("text", "")).strip()
            if not text:
                continue
            if seg_end <= start_time or seg_start >= end_time:
                continue
            local_start = clamp(seg_start - start_time, 0.0, end_time - start_time)
            local_end = clamp(seg_end - start_time, 0.0, end_time - start_time)
            if local_end - local_start < 0.05:
                continue
            windowed.append(
                {
                    "start": local_start,
                    "end": local_end,
                    "text": text,
                }
            )
        return windowed

    def write_srt(self, segments: list[dict], path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        lines: list[str] = []
        for idx, seg in enumerate(segments, start=1):
            lines.append(str(idx))
            lines.append(
                f"{format_timestamp(seg['start'], srt=True)} --> "
                f"{format_timestamp(seg['end'], srt=True)}"
            )
            lines.append(self._wrap_text(seg["text"]))
            lines.append("")
        path.write_text("\n".join(lines), encoding="utf-8")
        logger.info("Wrote SRT with %d cues -> %s", len(segments), path)
        return path

    def write_ass(
        self,
        segments: list[dict],
        path: Path,
        *,
        play_res_x: int = 1080,
        play_res_y: int = 1920,
        font_size: int = 48,
    ) -> Path:
        """ASS with safe-area margins for vertical video."""
        path.parent.mkdir(parents=True, exist_ok=True)
        # MarginV keeps text above the bottom UI safe zone on mobile.
        header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {play_res_x}
PlayResY: {play_res_y}
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,{font_size},&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3,1,2,80,80,220,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        events: list[str] = []
        for seg in segments:
            start = format_timestamp(seg["start"], srt=False)[:-1]  # ASS uses centiseconds-ish; keep ms-ish
            end = format_timestamp(seg["end"], srt=False)[:-1]
            # Convert to ASS h:mm:ss.cs (centiseconds)
            start = self._to_ass_time(seg["start"])
            end = self._to_ass_time(seg["end"])
            text = self._wrap_text(seg["text"]).replace("\n", r"\N")
            events.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}")

        path.write_text(header + "\n".join(events) + "\n", encoding="utf-8")
        logger.info("Wrote ASS with %d cues -> %s", len(segments), path)
        return path

    def load_segments_json(self, segments_json: str) -> list[dict]:
        return json.loads(segments_json)

    @staticmethod
    def _wrap_text(text: str, width: int = 32) -> str:
        words = text.split()
        if not words:
            return text
        lines: list[str] = []
        current: list[str] = []
        for word in words:
            trial = (" ".join(current + [word])).strip()
            if current and len(trial) > width:
                lines.append(" ".join(current))
                current = [word]
            else:
                current.append(word)
        if current:
            lines.append(" ".join(current))
        return "\n".join(lines[:3])

    @staticmethod
    def _to_ass_time(seconds: float) -> str:
        if seconds < 0:
            seconds = 0.0
        total_cs = int(round(seconds * 100))
        hours, rem = divmod(total_cs, 360000)
        minutes, rem = divmod(rem, 6000)
        secs, cs = divmod(rem, 100)
        return f"{hours}:{minutes:02d}:{secs:02d}.{cs:02d}"
