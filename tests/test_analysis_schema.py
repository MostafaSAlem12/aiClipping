from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.analysis import LLMAnalysisResponse, LLMClipCandidate


def test_valid_candidate():
    c = LLMClipCandidate(
        start_time=10.0,
        end_time=35.5,
        title="Bold claim",
        hook="Nobody talks about this",
        reason="Strong opinion with payoff",
        score=8.5,
    )
    assert c.duration == 25.5


def test_rejects_inverted_timestamps():
    with pytest.raises(ValidationError):
        LLMClipCandidate(
            start_time=40.0,
            end_time=20.0,
            title="Bad",
            hook="Hook",
            reason="Reason",
            score=7.0,
        )


def test_rejects_empty_title():
    with pytest.raises(ValidationError):
        LLMClipCandidate(
            start_time=1.0,
            end_time=20.0,
            title="   ",
            hook="Hook",
            reason="Reason",
            score=7.0,
        )


def test_rejects_score_out_of_range():
    with pytest.raises(ValidationError):
        LLMClipCandidate(
            start_time=1.0,
            end_time=20.0,
            title="Title",
            hook="Hook",
            reason="Reason",
            score=11.0,
        )


def test_analysis_response_schema():
    payload = {
        "candidates": [
            {
                "start_time": 12.0,
                "end_time": 40.0,
                "title": "Insight",
                "hook": "Here's the twist",
                "reason": "Standalone valuable point",
                "score": 9.0,
            }
        ]
    }
    parsed = LLMAnalysisResponse.model_validate(payload)
    assert len(parsed.candidates) == 1
