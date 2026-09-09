from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.database import Base
from app.db.models import (
    CandidateStatus,
    ClipCandidate,
    ClipStatus,
    GeneratedClip,
    Transcript,
    Video,
    VideoStatus,
)
from app.utils.files import safe_filename


def test_database_models(tmp_path):
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}", future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, future=True)

    with SessionLocal() as db:
        video = Video(
            filename=safe_filename("talk.mp4"),
            original_path=str(tmp_path / "talk.mp4"),
            duration=120.0,
            status=VideoStatus.UPLOADED.value,
        )
        db.add(video)
        db.commit()
        db.refresh(video)

        transcript = Transcript(
            video_id=video.id,
            text="Hello world",
            segments_json='[{"start":0,"end":1,"text":"Hello world"}]',
        )
        candidate = ClipCandidate(
            video_id=video.id,
            start_time=10,
            end_time=40,
            title="Title",
            hook="Hook",
            reason="Reason",
            score=8.2,
            status=CandidateStatus.SELECTED.value,
        )
        db.add_all([transcript, candidate])
        db.commit()
        db.refresh(candidate)

        clip = GeneratedClip(
            candidate_id=candidate.id,
            output_path=str(tmp_path / "out.mp4"),
            duration=30.0,
            status=ClipStatus.COMPLETED.value,
        )
        db.add(clip)
        db.commit()

        loaded = db.get(Video, video.id)
        assert loaded is not None
        assert loaded.transcript is not None
        assert len(loaded.candidates) == 1
        assert loaded.candidates[0].generated_clip is not None
