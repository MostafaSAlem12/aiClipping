# Architecture

## System Overview

```
User (browser / API client)
  ↓
FastAPI (app/main.py)
  ├── HTML Dashboard (Jinja2)
  └── REST API (/api/...)
        ↓
  JobManager (in-process thread pool)
        ↓
  PipelineService
        ├── VideoIngestionService
        ├── TranscriptionService → FasterWhisperBackend
        ├── ClipAnalysisService → OllamaClient
        ├── ClipSelectionService
        ├── VideoClipService (FFmpeg cut)
        ├── SubtitleService (SRT/ASS)
        ├── RenderingService (9:16 + burn-in)
        └── QualityService
        ↓
  SQLite + local files under data/
        ↓
  Generated clips (downloadable)
```

## Components

### FastAPI application (`app/main.py`)
- **Responsibility:** HTTP entrypoint, static files, route mounting, startup (logging, dirs, DB init).
- **Inputs:** HTTP requests.
- **Outputs:** HTML pages, JSON responses, file downloads.
- **Dependencies:** FastAPI, Jinja2, SQLAlchemy.

### JobManager (`app/workers/jobs.py`)
- **Responsibility:** Queue long-running pipelines without blocking HTTP forever.
- **Inputs:** `video_id`.
- **Outputs:** Background execution of `PipelineService.run`.
- **Dependencies:** `ThreadPoolExecutor` (max_workers=1).
- **Note:** MVP only. A real queue is **PLANNED**, not implemented.

### PipelineService (`app/services/pipeline.py`)
- **Responsibility:** Orchestrate stages and update video status / errors.
- **Inputs:** DB session + video id.
- **Outputs:** Persisted transcript, candidates, generated clips; final video status.
- **Dependencies:** All stage services below.

### VideoIngestionService
- **Responsibility:** Store uploads under `data/uploads/`, probe duration/dimensions.
- **Inputs:** Uploaded file path + filename.
- **Outputs:** `Video` row; metadata fields.
- **Dependencies:** FFmpeg/ffprobe.

### TranscriptionService + FasterWhisperBackend
- **Responsibility:** Extract audio, transcribe with timestamps.
- **Inputs:** Video path.
- **Outputs:** `Transcript` row + JSON file under `data/transcripts/`.
- **Dependencies:** FFmpeg (audio extract), faster-whisper, optional CUDA.

### ClipAnalysisService + OllamaClient
- **Responsibility:** Prompt LLM with timestamped transcript; validate JSON candidates.
- **Inputs:** Transcript segments.
- **Outputs:** `ClipCandidate` rows (pending).
- **Dependencies:** Ollama HTTP API; prompt file `app/prompts/clip_analysis.txt`.

### ClipSelectionService
- **Responsibility:** Adjust scores, reject overlaps / weak scores, pick top-N.
- **Inputs:** Candidate list + settings thresholds.
- **Outputs:** Candidates marked `selected` or `rejected`.

### VideoClipService
- **Responsibility:** Cut source segment with original audio.
- **Inputs:** Source video + start/end.
- **Outputs:** Temporary cut MP4.
- **Dependencies:** FFmpeg.

### SubtitleService
- **Responsibility:** Window transcript segments to clip range; write SRT/ASS.
- **Inputs:** Segment JSON + clip window.
- **Outputs:** Subtitle files beside clips.

### RenderingService
- **Responsibility:** Deterministic center-crop to 9:16 and burn subtitles.
- **Inputs:** Cut video + ASS/SRT path.
- **Outputs:** Final MP4 under `data/clips/video_{id}/`.
- **Dependencies:** FFmpeg with subtitle filter / libass.
- **Extension point:** `_build_crop_filter` can later become face-aware (**PLANNED**).

### QualityService
- **Responsibility:** Lightweight checks (duration, dimensions, audio presence).
- **Inputs:** Output clip path + expectations.
- **Outputs:** Pass/fail issue list stored on clip when present.

## Data Flow

1. User uploads video → stored on disk + `videos` row (`uploaded`).
2. User triggers process → `JobManager` sets `queued`.
3. Ingest probes metadata (`ingesting`).
4. Audio extracted → Whisper transcription (`transcribing`) → `transcripts`.
5. Ollama returns candidate JSON (`analyzing`) → Pydantic validation → `clip_candidates`.
6. Selection marks best clips (`selecting`).
7. Each selected candidate is cut, subtitled, rendered (`clipping` / `rendering`).
8. `generated_clips` rows created; video becomes `completed` or `failed`.

## Directory Structure

```
ai-video-engine/
  PROJECT_STATUS.md
  README.md
  docs/                 ← project documentation (this folder)
  app/
    main.py
    api/routes/
    core/
    db/
    schemas/
    services/
    prompts/
    workers/
    utils/
    templates/
    static/
  data/
    uploads/
    transcripts/
    clips/
    temp/
  tests/
  scripts/
```

## External Dependencies

| Dependency | Role | Status on current machine |
|---|---|---|
| Ollama | Local LLM for clip discovery | Installed; **no models pulled** |
| FFmpeg / ffprobe | Metadata, cut, render, burn-in | **Missing from PATH** |
| faster-whisper | Speech-to-text | Python package installed |
| NVIDIA CUDA | Preferred Whisper device | GPU present (RTX 5060 Ti); CUDA path used when available |

## Future Architecture

**PLANNED only — not implemented:**

- Durable job queue (Redis / Celery / RQ)
- PostgreSQL
- Campaign Agent / Content Rewards integration
- Account Manager
- Social Publishing
- Analytics / earnings tracking
- SaaS API, authentication, billing
- Face/speaker-aware cropping
- Microservices extraction of pipeline stages
