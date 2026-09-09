# AI Video Engine

Local MVP for turning long-form video into scored, subtitled, vertical short-form clips.

Pipeline: **upload → ingest → transcribe → LLM analyze → select → cut → 9:16 render + burn-in subtitles**.

This is a modular monolith (FastAPI + SQLite) designed to run on Windows 11 with a local NVIDIA GPU, Ollama, and FFmpeg. No cloud services, queues, or agent frameworks in v1.

## Project documentation

| File | Purpose |
|---|---|
| [`PROJECT_STATUS.md`](PROJECT_STATUS.md) | Single-page current status |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | System architecture |
| [`docs/PROJECT_PLAN.md`](docs/PROJECT_PLAN.md) | Roadmap / phases |
| [`docs/PROGRESS.md`](docs/PROGRESS.md) | Development log |
| [`docs/TODO.md`](docs/TODO.md) | Prioritized tasks |
| [`docs/DECISIONS.md`](docs/DECISIONS.md) | Architecture decision records |
| [`docs/API.md`](docs/API.md) | Implemented HTTP API |
| [`docs/DATA_MODEL.md`](docs/DATA_MODEL.md) | Database entities |
| [`docs/AI_PIPELINE.md`](docs/AI_PIPELINE.md) | Pipeline stages |
| [`docs/SETUP.md`](docs/SETUP.md) | Windows setup guide |
| [`docs/CHANGELOG.md`](docs/CHANGELOG.md) | Release history |

Documentation is updated with significant changes. Code + tests remain the source of truth for what is implemented.

## Prerequisites

| Software | Purpose | Notes |
|---|---|---|
| **Python 3.11+** | App runtime | Tested with 3.13 |
| **FFmpeg + ffprobe** | Metadata, cutting, 9:16 render, subtitle burn-in | Must be on `PATH` or set `FFMPEG_PATH` / `FFPROBE_PATH` |
| **Ollama** | Local LLM for clip discovery | Default API: `http://127.0.0.1:11434` |
| **NVIDIA GPU + drivers** | Faster Whisper on CUDA | CPU fallback is automatic if CUDA load fails |
| **CUDA-capable PyTorch wheels** | Used transitively by `faster-whisper` | Install CUDA torch if GPU transcription is required |

### FFmpeg (Windows)

1. Download a full build (essentials or full) from [https://www.gyan.dev/ffmpeg/builds/](https://www.gyan.dev/ffmpeg/builds/) or [https://github.com/BtbN/FFmpeg-Builds/releases](https://github.com/BtbN/FFmpeg-Builds/releases).
2. Extract somewhere permanent, e.g. `C:\ffmpeg`.
3. Add `C:\ffmpeg\bin` to your user `PATH`, **or** set in `.env`:

```env
FFMPEG_PATH=C:\ffmpeg\bin\ffmpeg.exe
FFPROBE_PATH=C:\ffmpeg\bin\ffprobe.exe
```

4. Verify in a new terminal:

```powershell
ffmpeg -version
ffprobe -version
```

### Ollama model configuration (important)

This machine currently has Ollama installed and reachable, but **no models pulled** (`ollama list` is empty).

Do **not** hard-code a model name in code. Configure it via environment variables:

1. Start Ollama (Windows app / tray).
2. Pull a model appropriate for your GPU/RAM, for example:

```powershell
ollama pull llama3.1:8b
# or
ollama pull qwen2.5:14b
```

3. Confirm the exact name:

```powershell
ollama list
```

4. Copy `.env.example` → `.env` and set:

```env
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=llama3.1:8b
```

Use the **exact** name shown by `ollama list`. The app sends `format: json` requests to `/api/generate`.

Recommended starting points on an RTX 5060 Ti 16GB:
- `llama3.1:8b` — fast, good JSON compliance
- `qwen2.5:14b` — stronger analysis, still fits 16GB VRAM comfortably for LLM-only use (Whisper and LLM should not be loaded at the same time in this MVP; they run sequentially)

## Python setup

```powershell
cd F:\Work\ai-video-engine
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env
```

Edit `.env` and set at least `OLLAMA_MODEL`.

Optional GPU check script:

```powershell
python scripts\check_dependencies.py
```

## Start the server

```powershell
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Open:
- Dashboard: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- API docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## How to upload and process a video

### Dashboard

1. Open the dashboard.
2. Upload an `.mp4` / `.mov` / `.mkv` / `.webm` file.
3. On the video page, click **Run pipeline**.
4. The page auto-refreshes while processing.
5. Review candidates (title/hook/reason/score) and download finished clips.

### API

```powershell
curl -F "file=@C:\path\to\video.mp4" http://127.0.0.1:8000/api/videos/upload
curl -X POST http://127.0.0.1:8000/api/videos/1/process
curl http://127.0.0.1:8000/api/videos/1
curl http://127.0.0.1:8000/api/videos/1/candidates
curl http://127.0.0.1:8000/api/videos/1/clips
curl -OJ http://127.0.0.1:8000/api/clips/1/download
```

## Environment variables

| Variable | Meaning | Example |
|---|---|---|
| `OLLAMA_BASE_URL` | Ollama HTTP API | `http://127.0.0.1:11434` |
| `OLLAMA_MODEL` | Model name from `ollama list` | `llama3.1:8b` |
| `WHISPER_MODEL` | faster-whisper size | `small` / `medium` |
| `WHISPER_DEVICE` | `cuda` or `cpu` | `cuda` |
| `WHISPER_COMPUTE_TYPE` | Whisper compute | `float16` (GPU) / `int8` (CPU) |
| `DATA_DIR` | Local project data root | `data` |
| `DATABASE_URL` | SQLAlchemy URL | `sqlite:///./data/app.db` |
| `FFMPEG_PATH` | Optional absolute ffmpeg path | `C:\ffmpeg\bin\ffmpeg.exe` |
| `FFPROBE_PATH` | Optional absolute ffprobe path | `C:\ffmpeg\bin\ffprobe.exe` |
| `MAX_CLIPS_PER_VIDEO` | Cap rendered clips | `5` |
| `MIN_CLIP_DURATION` | Reject shorter candidates | `10` |
| `MAX_CLIP_DURATION` | Reject longer candidates | `90` |

## How the pipeline works

```
VideoUpload
  → VideoIngestionService      (store file + ffprobe metadata)
  → TranscriptionService       (extract audio + faster-whisper)
  → ClipAnalysisService        (Ollama JSON → Pydantic validation)
  → ClipSelectionService       (score adjust + overlap filter + top-N)
  → VideoClipService           (FFmpeg cut with original audio)
  → SubtitleService            (SRT/ASS from transcript timestamps)
  → RenderingService           (center-crop 9:16 + burn subtitles)
  → QualityService             (duration/dimension/audio checks)
  → GeneratedClip
```

Long-running work runs in a **single-worker in-process thread pool** so HTTP requests are not blocked. Replace `app/workers/jobs.py` later with a real queue without changing service interfaces.

## Tests

```powershell
.\.venv\Scripts\Activate.ps1
pytest -q
```

Unit tests cover configuration, LLM JSON validation, candidate selection, duration/timestamp rules, subtitles, file helpers, and DB models. They intentionally do **not** require GPU transcription or FFmpeg rendering.

## Project layout

```
ai-video-engine/
  app/
    main.py
    api/routes/
    core/
    db/
    schemas/
    services/
      ingestion/ transcription/ analysis/
      clipping/ subtitles/ rendering/ quality/
    prompts/
    workers/
    utils/
    templates/ static/
  data/
  tests/
  scripts/
  .env.example
  requirements.txt
  README.md
```

## Known limitations (MVP)

- No face/speaker tracking yet — vertical framing uses deterministic center crop.
- In-process job runner only (one pipeline at a time); no Redis/Celery.
- LLM quality depends entirely on the locally configured Ollama model.
- Subtitle burn-in needs an FFmpeg build with `libass` (standard full builds include it).
- No campaign / publishing / earnings / feedback-learning features yet.
- Re-running the pipeline replaces previous candidates for that video.
- Whisper model download happens on first transcription.

## Recommended next development step

1. Install FFmpeg and pull an Ollama model.
2. Run `python scripts/check_dependencies.py`.
3. Process one real podcast/talk video end-to-end.
4. Then improve clip quality: sentence-boundary snapping + optional face-aware crop, before any social publishing work.
