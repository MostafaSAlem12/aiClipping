# Project Status

## Current Version
V0.1.0

## Current Phase
Phase 1 — Video Engine MVP (code complete; end-to-end blocked on local deps)

## Overall Progress
~35% — core video-to-clips MVP implemented and unit-tested; local FFmpeg + Ollama model still required before a real end-to-end run; later product phases not started.

## Current Objective
Get the local Windows environment fully runnable (FFmpeg + Ollama model), then process one real long-form video end-to-end and harden clip quality.

## Completed
- [x] Project structure (modular monolith)
- [x] Configuration via environment variables (`.env` / `.env.example`)
- [x] FastAPI app + Uvicorn entrypoint
- [x] SQLite + SQLAlchemy models (`Video`, `Transcript`, `ClipCandidate`, `GeneratedClip`)
- [x] Upload API + dashboard upload
- [x] Video metadata via ffprobe (code path; requires FFmpeg installed)
- [x] Transcription service with faster-whisper (replaceable backend)
- [x] Ollama client + JSON analysis prompt + Pydantic validation
- [x] Candidate scoring / selection (duration preference + overlap filter)
- [x] Clip extraction, 9:16 center-crop rendering, subtitle burn-in (code path)
- [x] Simple HTML dashboard + clip download
- [x] Unit tests (20 passed)
- [x] Project documentation under `docs/` + root `PROJECT_STATUS.md`

## In Progress
- [ ] Local environment readiness (FFmpeg install, Ollama model pull, first real pipeline run)

## Next
- [ ] Install FFmpeg / ffprobe and set PATH or `FFMPEG_PATH` / `FFPROBE_PATH`
- [ ] Pull an Ollama model and set `OLLAMA_MODEL`
- [ ] Run `python scripts/check_dependencies.py`
- [ ] Process one real video end-to-end
- [ ] Phase 2 quality improvements (sentence-boundary snapping, better crop)

## Blocked
- [ ] Full pipeline E2E on this machine — **FFmpeg not found on PATH**
- [ ] LLM analysis — **no Ollama models installed** (`ollama list` empty; `OLLAMA_MODEL` unset)

## Current Architecture
Modular monolith: FastAPI HTTP layer → in-process `JobManager` → `PipelineService` orchestrating ingestion, transcription, Ollama analysis, selection, clipping, subtitles, rendering, and light quality checks. Data stored in SQLite + local `data/` directories.

## Current Tech Stack
- Python 3.13 (target 3.11+)
- FastAPI, Uvicorn, Pydantic, SQLAlchemy, SQLite
- Jinja2 server-rendered HTML dashboard
- Ollama (local HTTP API)
- faster-whisper (CUDA preferred, CPU fallback)
- FFmpeg / ffprobe (required external binaries)
- pytest

## Current Known Issues
- FFmpeg / ffprobe not installed on the development machine
- No Ollama model pulled; `OLLAMA_MODEL` empty by design until configured
- Vertical framing is deterministic center-crop only (no face/speaker tracking)
- Single-worker in-process jobs only (no durable queue)
- End-to-end GPU transcription + FFmpeg render not covered by unit tests (by design)
- Re-running the pipeline replaces previous candidates for that video

## Last Updated
2026-09-04
