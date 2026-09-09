from __future__ import annotations

import re
import uuid
from pathlib import Path


_UNSAFE = re.compile(r"[^A-Za-z0-9._-]+")


def safe_filename(name: str, *, fallback: str = "video") -> str:
    stem = Path(name).name
    cleaned = _UNSAFE.sub("_", stem).strip("._")
    return cleaned or fallback


def unique_path(directory: Path, filename: str) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    candidate = directory / filename
    if not candidate.exists():
        return candidate
    stem = candidate.stem
    suffix = candidate.suffix
    return directory / f"{stem}_{uuid.uuid4().hex[:8]}{suffix}"


def ensure_parent(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    return path
