# Progress Log

## 2026-09-04

### Completed
- Scaffolded modular monolith under `app/` with FastAPI, SQLite, Jinja2 dashboard.
- Implemented upload → ingest → transcribe → Ollama analyze → select → cut → 9:16 render → subtitle burn-in → quality check pipeline.
- Added replaceable transcription backend (`FasterWhisperBackend`).
- Added Pydantic validation for LLM candidate JSON.
- Added in-process `JobManager` for non-blocking pipeline runs.
- Added unit tests for config, schemas, selection, subtitles, files, DB models.
- Created documentation set: `PROJECT_STATUS.md` + `docs/*`.

### Changed
- Repository went from empty → V0.1.0 MVP codebase.
- `OLLAMA_MODEL` left empty by design; must be set after `ollama pull`.

### Tests
- `pytest -q` → **20 passed**.
- Smoke: `GET /` → 200; `GET /api/videos` → 200; app import OK.
- Not run: GPU transcription E2E, FFmpeg render E2E (dependencies missing).

### Problems
- FFmpeg / ffprobe not installed on PATH.
- Ollama reachable but model list empty.
- Full real-video pipeline therefore blocked on this machine.

### Decisions
- Modular monolith over microservices for V0.1.
- No LangChain / CrewAI / Redis / Celery in MVP.
- Center-crop 9:16 with explicit extension point for face-aware crop later.
- Documentation under `docs/` is mandatory and must track real status.

### Next Session
- Install FFmpeg and pull an Ollama model.
- Run `scripts/check_dependencies.py`.
- Process one real video end-to-end.
- Start Phase 2 quality improvements only after E2E succeeds.
