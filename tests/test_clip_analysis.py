from __future__ import annotations

import json

from app.core.config import Settings
from app.services.analysis.clip_analysis import ClipAnalysisService
from app.services.analysis.ollama_client import extract_json_object


def test_extract_json_object_plain():
    payload = extract_json_object('{"candidates": []}')
    assert payload == {"candidates": []}


def test_extract_json_object_fenced():
    raw = """```json
{"candidates": [{"start_time": 1, "end_time": 20, "title": "A", "hook": "H", "reason": "R", "score": 8}]}
```"""
    payload = extract_json_object(raw)
    assert "candidates" in payload


def test_parse_and_validate_filters_short_clips(tmp_path):
    settings = Settings(
        data_dir=tmp_path,
        min_clip_duration=10,
        max_clip_duration=90,
        ollama_model="test-model",
    )
    service = ClipAnalysisService(settings=settings)
    raw = json.dumps(
        {
            "candidates": [
                {
                    "start_time": 0,
                    "end_time": 5,
                    "title": "Too short",
                    "hook": "h",
                    "reason": "r",
                    "score": 9,
                },
                {
                    "start_time": 10,
                    "end_time": 40,
                    "title": "Good clip",
                    "hook": "hook",
                    "reason": "reason",
                    "score": 8.5,
                },
            ]
        }
    )
    valid = service.parse_and_validate(raw, video_duration=120)
    assert len(valid) == 1
    assert valid[0].title == "Good clip"


def test_timestamp_validation_against_duration(tmp_path):
    settings = Settings(data_dir=tmp_path, ollama_model="test-model")
    service = ClipAnalysisService(settings=settings)
    raw = json.dumps(
        {
            "candidates": [
                {
                    "start_time": 200,
                    "end_time": 230,
                    "title": "Past end",
                    "hook": "h",
                    "reason": "r",
                    "score": 8,
                }
            ]
        }
    )
    try:
        service.parse_and_validate(raw, video_duration=100)
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "no valid clip candidates" in str(exc).lower()
