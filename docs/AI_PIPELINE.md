# AI Pipeline

## Overview

```
Video
  ↓
Audio extract (FFmpeg)
  ↓
Transcription (faster-whisper)
  ↓
Transcript + timestamped segments
  ↓
LLM analysis (Ollama, JSON)
  ↓
Pydantic validation + duration checks
  ↓
Candidate moments
  ↓
Score adjustment + selection
  ↓
Clip cut (FFmpeg)
  ↓
Subtitles from segments (SRT/ASS)
  ↓
9:16 render + burn-in (FFmpeg)
  ↓
Quality validation
  ↓
Generated clip
```

Orchestrator: `app/services/pipeline.py`  
Background entry: `app/workers/jobs.py`

---

## Stage details

### 1. Ingestion
- **Input:** uploaded file
- **Processing:** copy to `data/uploads/`; ffprobe duration/width/height
- **Output:** `Video` metadata
- **Tool:** ffprobe
- **Failures:** missing file; FFmpeg/ffprobe unavailable → `failed`

### 2. Audio extraction
- **Input:** video path
- **Processing:** mono 16 kHz WAV to `data/temp/`
- **Output:** temporary WAV
- **Tool:** ffmpeg
- **Failures:** no audio / ffmpeg error → transcription stage fails

### 3. Transcription
- **Input:** WAV path
- **Processing:** `FasterWhisperBackend.transcribe` with VAD filter
- **Output:** full text + segments `{start,end,text}`; DB + JSON file
- **Model/tool:** faster-whisper (`WHISPER_MODEL`, default `small`)
- **Device:** `WHISPER_DEVICE` (default `cuda`); falls back to CPU `int8` if CUDA load fails
- **Failures:** model load / decode errors → video `failed`

### 4. LLM analysis
- **Input:** timestamped transcript lines `[start-end] text`
- **Processing:** prompt from `app/prompts/clip_analysis.txt`; Ollama `/api/generate` with `format: json`
- **Output:** raw JSON text
- **Model/tool:** Ollama model from `OLLAMA_MODEL` (**must be set**; no hard-coded default)
- **Failures:** unreachable Ollama, empty model, empty response → `failed`

### 5. Validation
- **Input:** raw LLM text
- **Processing:** extract JSON object; `LLMAnalysisResponse` / `LLMClipCandidate` Pydantic models; drop too-short/too-long / past-end windows
- **Output:** validated candidate list
- **Failures:** invalid JSON / no valid candidates → `failed`

### 6. Scoring & selection
- **Input:** validated candidates
- **Processing:**
  - start from LLM `score`
  - `+0.5` if duration in preferred window (default 20–90s)
  - `-0.5` if shorter than preferred min
  - `-0.3` if longer than preferred max
  - reject if adjusted score `< MIN_CANDIDATE_SCORE` (default 6.0)
  - reject if ≥40% overlap with already selected
  - keep top `MAX_CLIPS_PER_VIDEO` (default 5)
- **Output:** `selected` / `rejected` statuses
- **Failures:** zero selected → video `failed` with clear message

### 7. Clip extraction
- **Input:** selected windows
- **Processing:** re-encode accurate cut (`libx264` + `aac`), keep audio
- **Output:** temp cut MP4
- **Tool:** ffmpeg
- **Failures:** per-candidate `failed` (pipeline continues other candidates)

### 8. Subtitles
- **Input:** transcript segments + clip window
- **Processing:** re-base timestamps; write SRT + ASS (safe bottom margin for vertical)
- **Output:** subtitle files in clip folder
- **Tool:** `SubtitleService` (no ML)

### 9. Rendering
- **Input:** cut + ASS
- **Processing:** center-crop/scale to `OUTPUT_WIDTH`×`OUTPUT_HEIGHT` (default 1080×1920); burn subtitles
- **Output:** final MP4
- **Tool:** ffmpeg `crop/scale` + `subtitles` filter
- **Failures:** missing libass / path escaping issues on Windows → candidate `failed`

### 10. Quality validation
- **Input:** final MP4
- **Processing:** probe duration/dimensions/audio presence
- **Output:** issues list (stored on clip when present); does not invent engagement metrics
- **Tool:** ffprobe

---

## Current runtime configuration

| Setting | Current default / state |
|---|---|
| Ollama base URL | `http://127.0.0.1:11434` |
| Ollama model | **unset** until user configures `OLLAMA_MODEL` |
| Whisper model | `small` (`WHISPER_MODEL`) |
| Whisper device | `cuda` with CPU fallback |
| Prompt file | `app/prompts/clip_analysis.txt` (v0.1) |
| Min/max clip duration | 10s / 90s |
| Preferred duration | 20–90s |
| Max clips per video | 5 |

## Prompt versioning

| Version | Date | Notes |
|---|---|---|
| v0.1 | 2026-09-04 | Initial short-form moment finder; strict JSON schema; prioritizes opinions/insights/tension; avoids intros/greetings/context-heavy moments |

When the prompt changes meaningfully, add a row here and summarize the change in `CHANGELOG.md` / `PROGRESS.md`.

## Explicit non-goals of this pipeline
- No fake views / engagement generation
- No platform abuse automation
- No multi-agent frameworks in V0.1
