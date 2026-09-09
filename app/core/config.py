from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Runtime configuration loaded from environment / .env."""

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "AI Video Engine"
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    debug: bool = True
    log_level: str = "INFO"

    data_dir: Path = Field(default=Path("data"))
    database_url: str = "sqlite:///./data/app.db"

    ffmpeg_path: str = ""
    ffprobe_path: str = ""

    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = ""
    ollama_timeout_seconds: int = 300

    whisper_model: str = "small"
    whisper_device: str = "cuda"
    whisper_compute_type: str = "float16"
    whisper_language: str = ""

    max_clips_per_video: int = 5
    min_clip_duration: float = 10.0
    max_clip_duration: float = 90.0
    preferred_min_duration: float = 20.0
    preferred_max_duration: float = 90.0
    min_candidate_score: float = 6.0

    output_width: int = 1080
    output_height: int = 1920
    subtitle_font_size: int = 48

    @field_validator("data_dir", mode="before")
    @classmethod
    def _resolve_data_dir(cls, value: str | Path) -> Path:
        path = Path(value)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        return path

    @property
    def uploads_dir(self) -> Path:
        return self.data_dir / "uploads"

    @property
    def transcripts_dir(self) -> Path:
        return self.data_dir / "transcripts"

    @property
    def clips_dir(self) -> Path:
        return self.data_dir / "clips"

    @property
    def temp_dir(self) -> Path:
        return self.data_dir / "temp"

    def ensure_directories(self) -> None:
        for path in (
            self.data_dir,
            self.uploads_dir,
            self.transcripts_dir,
            self.clips_dir,
            self.temp_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_directories()
    return settings
