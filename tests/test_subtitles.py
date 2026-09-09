from __future__ import annotations

from pathlib import Path

from app.services.subtitles.service import SubtitleService


def test_segments_for_window_and_srt(tmp_path):
    service = SubtitleService()
    segments = [
        {"start": 0.0, "end": 2.0, "text": "Hello there"},
        {"start": 12.0, "end": 15.5, "text": "Important point"},
        {"start": 40.0, "end": 42.0, "text": "After window"},
    ]
    windowed = service.segments_for_window(segments, start_time=10.0, end_time=20.0)
    assert len(windowed) == 1
    assert abs(windowed[0]["start"] - 2.0) < 0.01
    assert "Important" in windowed[0]["text"]

    srt_path = tmp_path / "test.srt"
    service.write_srt(windowed, srt_path)
    content = srt_path.read_text(encoding="utf-8")
    assert "Important point" in content
    assert "-->" in content


def test_write_ass(tmp_path):
    service = SubtitleService()
    path = tmp_path / "test.ass"
    service.write_ass(
        [{"start": 0.5, "end": 2.0, "text": "Readable subtitle"}],
        path,
        play_res_x=1080,
        play_res_y=1920,
    )
    text = path.read_text(encoding="utf-8")
    assert "Dialogue:" in text
    assert "Readable subtitle" in text
