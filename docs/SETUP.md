# Setup (Windows 11)

Never put secrets in this file. API keys are not used in V0.1.

## 1. Prerequisites

| Requirement | Notes |
|---|---|
| Python 3.11+ | Developed/tested with Python 3.13.3 |
| Git (optional) | For version control |
| NVIDIA driver | RTX 5060 Ti present on the reference machine |
| Ollama | Windows app; API on `http://127.0.0.1:11434` |
| FFmpeg + ffprobe | **Required** for metadata/cut/render |

## 2. Python virtual environment

```powershell
cd F:\Work\ai-video-engine
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 3. Environment variables

```powershell
copy .env.example .env
notepad .env
```

Important variables:

| Variable | Purpose |
|---|---|
| `OLLAMA_BASE_URL` | Ollama HTTP API |
| `OLLAMA_MODEL` | Exact name from `ollama list` (required for analysis) |
| `WHISPER_MODEL` | e.g. `small`, `medium` |
| `WHISPER_DEVICE` | `cuda` or `cpu` |
| `DATA_DIR` | Local data root (default `data`) |
| `DATABASE_URL` | Default SQLite file URL |
| `FFMPEG_PATH` / `FFPROBE_PATH` | Optional absolute paths if not on PATH |

SQLite DB file is created automatically on startup under `data/app.db` (given default URL).

## 4. FFmpeg installation

1. Download a full Windows build (Gyán.dev or BtbN builds).
2. Extract to a stable folder, e.g. `C:\ffmpeg`.
3. Add `C:\ffmpeg\bin` to user PATH **or** set:

```env
FFMPEG_PATH=C:\ffmpeg\bin\ffmpeg.exe
FFPROBE_PATH=C:\ffmpeg\bin\ffprobe.exe
```

4. Open a **new** PowerShell and verify:

```powershell
ffmpeg -version
ffprobe -version
```

## 5. Ollama installation & model setup

1. Install Ollama for Windows and ensure the tray app is running.
2. Pull a model (examples):

```powershell
ollama pull llama3.1:8b
# or
ollama pull qwen2.5:14b
```

3. Confirm:

```powershell
ollama list
```

4. Set `OLLAMA_MODEL` in `.env` to the **exact** listed name.

Reference machine note (2026-09-04): Ollama was reachable but **no models were installed**.

## 6. Dependency check

```powershell
.\.venv\Scripts\Activate.ps1
python scripts\check_dependencies.py
```

Fix any `[MISSING]` / `[WARN]` items before expecting a full pipeline run.

## 7. Run the server

```powershell
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

- Dashboard: http://127.0.0.1:8000/
- OpenAPI: http://127.0.0.1:8000/docs

## 8. Run tests

```powershell
.\.venv\Scripts\Activate.ps1
pytest -q
```

Unit tests do not require FFmpeg, GPU, or an Ollama model.

## 9. First video run

1. Open dashboard → upload an MP4/MOV/MKV/WEBM.
2. Click **Run pipeline**.
3. Wait for statuses: queued → … → completed.
4. Download clips from the detail page or `/api/clips/{id}/download`.

## 10. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `ffmpeg not found` | Binary missing / PATH | Install FFmpeg or set `FFMPEG_PATH` |
| `OLLAMA_MODEL is not set` | Empty `.env` value | Pull model + set exact name |
| Ollama connection errors | App not running | Start Ollama tray app |
| Whisper CUDA load fails | Wheel/driver mismatch | App falls back to CPU; or install CUDA-capable stack |
| Subtitle burn-in fails | FFmpeg without libass | Use a full FFmpeg build |
| Pipeline stuck / no progress | Job died / missing deps | Check server logs; video `error_message` |

## 11. GPU notes

- Preferred Whisper path: `WHISPER_DEVICE=cuda`, `WHISPER_COMPUTE_TYPE=float16`.
- Whisper and Ollama run **sequentially** in this MVP (not concurrently), which helps 16GB VRAM machines.
- If GPU transcription is unreliable, set `WHISPER_DEVICE=cpu` and `WHISPER_COMPUTE_TYPE=int8`.
