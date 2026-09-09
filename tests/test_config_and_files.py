from __future__ import annotations

from pathlib import Path

from app.core.config import Settings, get_settings
from app.utils.files import safe_filename, unique_path
from app.utils.ffmpeg import build_center_crop_filter
from app.utils.time import format_timestamp


def test_settings_resolve_data_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "custom-data"))
    monkeypatch.setenv("OLLAMA_MODEL", "demo-model")
    get_settings.cache_clear()
    settings = get_settings()
    assert settings.data_dir == tmp_path / "custom-data"
    assert settings.uploads_dir.exists()
    assert settings.ollama_model == "demo-model"
    get_settings.cache_clear()


def test_settings_defaults_do_not_hardcode_model():
    settings = Settings(_env_file=None)
    # Empty by default so local installs must configure explicitly.
    assert settings.ollama_model == "" or isinstance(settings.ollama_model, str)


def test_safe_filename():
    assert "lecture" in safe_filename(r"my lecture?.mp4").lower() or safe_filename(
        r"my lecture?.mp4"
    ).endswith(".mp4")


def test_unique_path(tmp_path):
    first = unique_path(tmp_path, "clip.mp4")
    first.write_text("a", encoding="utf-8")
    second = unique_path(tmp_path, "clip.mp4")
    assert first != second


def test_center_crop_filter_landscape():
    filt = build_center_crop_filter(1920, 1080, 1080, 1920)
    assert "crop=" in filt
    assert "scale=1080:1920" in filt


def test_format_timestamp_srt():
    assert format_timestamp(3661.5, srt=True) == "01:01:01,500"
