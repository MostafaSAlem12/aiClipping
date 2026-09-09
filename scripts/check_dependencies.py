#!/usr/bin/env python
"""Check local prerequisites for the AI Video Engine MVP."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.core.config import get_settings
from app.services.analysis.ollama_client import OllamaClient, OllamaError
from app.utils.ffmpeg import resolve_ffmpeg, resolve_ffprobe, FFmpegError


def main() -> int:
    settings = get_settings()
    print(f"Project root: {ROOT}")
    print(f"Data dir: {settings.data_dir}")
    print()

    ok = True

    # FFmpeg
    try:
        ffmpeg = resolve_ffmpeg(settings)
        print(f"[OK] ffmpeg: {ffmpeg}")
    except FFmpegError as exc:
        ok = False
        print(f"[MISSING] ffmpeg: {exc}")

    try:
        ffprobe = resolve_ffprobe(settings)
        print(f"[OK] ffprobe: {ffprobe}")
    except FFmpegError as exc:
        ok = False
        print(f"[MISSING] ffprobe: {exc}")

    # Ollama
    client = OllamaClient(settings)
    models: list[str] = []
    try:
        models = client.list_models()
        if models:
            print(f"[OK] Ollama reachable at {settings.ollama_base_url}")
            print(f"     Installed models: {', '.join(models)}")
        else:
            ok = False
            print(f"[WARN] Ollama reachable at {settings.ollama_base_url}, but no models installed.")
            print("       Pull one, e.g.: ollama pull llama3.1:8b")
            print("       Then set OLLAMA_MODEL in .env to that exact name.")
    except OllamaError as exc:
        ok = False
        print(f"[MISSING] Ollama: {exc}")

    if settings.ollama_model:
        print(f"[OK] OLLAMA_MODEL={settings.ollama_model}")
        if models and settings.ollama_model not in models:
            # Allow tags like name:tag vs name
            aliases = {m.split(":")[0] for m in models}
            if settings.ollama_model not in aliases and not any(
                m.startswith(settings.ollama_model) for m in models
            ):
                ok = False
                print(
                    f"[WARN] Configured model '{settings.ollama_model}' "
                    f"was not found in `ollama list`."
                )
    else:
        ok = False
        print("[MISSING] OLLAMA_MODEL is empty. Set it in .env after pulling a model.")

    print(f"[INFO] WHISPER_MODEL={settings.whisper_model} device={settings.whisper_device}")
    print()
    if ok:
        print("All critical checks passed.")
        return 0
    print("Some checks failed. Fix the items above before running the full pipeline.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
