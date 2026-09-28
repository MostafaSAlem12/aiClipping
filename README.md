# AI Video Engine

A local Python/FastAPI pipeline for turning long-form video into structured, scored, captioned vertical short-form clips.

The project combines:

- Python / FastAPI
- faster-whisper transcription
- Local LLM inference through Ollama
- Pydantic validation
- FFmpeg / ffprobe
- SQLite / SQLAlchemy
- Automated tests
- Deterministic media quality checks

The system is designed as a modular monolith with clear service boundaries so individual processing stages can be replaced or moved to external workers later.

---

## Verified Result

The project has been verified on Windows 11 with:

- Python 3.13
- NVIDIA RTX 5060 Ti 16GB
- faster-whisper
- Ollama
- FFmpeg / ffprobe

### Automated verification

Run:

```powershell
.\.venv\Scripts\Activate.ps1
pytest -q
