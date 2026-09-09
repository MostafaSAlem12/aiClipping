# Changelog

## [0.1.0] — 2026-09-04

### Added
- Modular FastAPI monolith for local video → short-clip pipeline
- SQLite models: `Video`, `Transcript`, `ClipCandidate`, `GeneratedClip`
- Upload + process APIs and Jinja2 dashboard
- faster-whisper transcription backend (CUDA with CPU fallback)
- Ollama JSON clip analysis with Pydantic validation
- Candidate selection (duration preference + overlap filter)
- FFmpeg cut, 9:16 center-crop render, SRT/ASS subtitle burn-in
- Lightweight quality checks
- In-process single-worker job manager
- Unit tests (20) and `scripts/check_dependencies.py`
- Documentation: `PROJECT_STATUS.md` and `docs/*`

### Changed
- N/A (initial release)

### Fixed
- N/A (initial release)

### Removed
- N/A (initial release)
