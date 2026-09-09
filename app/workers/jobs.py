from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor

from app.core.logging import get_logger
from app.db.database import SessionLocal
from app.db.models import Video, VideoStatus
from app.services.pipeline import PipelineService

logger = get_logger(__name__)


class JobManager:
    """Simple in-process background job runner for the MVP.

    Replace with a proper queue (RQ/Celery/etc.) later without changing routes.
    """

    def __init__(self, max_workers: int = 1) -> None:
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="pipeline")
        self._futures: dict[int, Future] = {}

    def is_running(self, video_id: int) -> bool:
        future = self._futures.get(video_id)
        return future is not None and not future.done()

    def submit_pipeline(self, video_id: int) -> bool:
        if self.is_running(video_id):
            return False

        future = self._executor.submit(self._run_pipeline, video_id)
        self._futures[video_id] = future
        return True

    def _run_pipeline(self, video_id: int) -> None:
        db = SessionLocal()
        try:
            video = db.get(Video, video_id)
            if video is None:
                logger.error("Job started for missing video %s", video_id)
                return
            video.status = VideoStatus.QUEUED.value
            db.commit()

            pipeline = PipelineService()
            pipeline.run(db, video_id)
        except Exception:
            logger.exception("Background pipeline job failed for video %s", video_id)
        finally:
            db.close()


job_manager = JobManager(max_workers=1)
