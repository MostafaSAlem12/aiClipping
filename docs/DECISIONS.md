# Architecture Decisions

## Decision: Python as the implementation language

**Date:** 2026-09-04  
**Status:** Accepted

**Context:** Need fast local MVP integrating ML transcription, LLM HTTP clients, and FFmpeg orchestration on Windows.

**Decision:** Use Python 3.11+.

**Why:** Strong ecosystem for Whisper, HTTP, FastAPI; fastest path to a working local pipeline.

**Alternatives considered:** Node.js (weaker local ML story), Go/Rust (faster runtime, slower ML integration for MVP).

**Consequences:** Easy service modularity; packaging/GPU wheels need care on Windows.

---

## Decision: FastAPI for the backend

**Date:** 2026-09-04  
**Status:** Accepted

**Context:** Need REST API + simple dashboard quickly, with clear OpenAPI docs.

**Decision:** FastAPI + Uvicorn + Jinja2 templates.

**Why:** Typed request/response models, async-friendly upload endpoints, low boilerplate.

**Alternatives considered:** Flask/Django, separate React SPA.

**Consequences:** Server-rendered MVP UI; React deferred until it provides clear benefit.

---

## Decision: SQLite for initial persistence

**Date:** 2026-09-04  
**Status:** Accepted

**Context:** Single-machine MVP; avoid ops overhead.

**Decision:** SQLAlchemy 2.x + SQLite file under `data/app.db`.

**Why:** Zero setup, enough for local video/candidate/clip records.

**Alternatives considered:** PostgreSQL immediately, JSON files only.

**Consequences:** Easy local start; migrate to PostgreSQL when multi-user/concurrency demands it (**PLANNED**).

---

## Decision: Ollama for local LLM inference

**Date:** 2026-09-04  
**Status:** Accepted

**Context:** Need local transcript analysis without cloud APIs.

**Decision:** Call Ollama HTTP `/api/generate` with `format: json`; model name via `OLLAMA_MODEL`.

**Why:** Simple local ops on Windows; model swappable without code changes.

**Alternatives considered:** Direct llama.cpp bindings, cloud LLM APIs, LangChain wrappers.

**Consequences:** Quality depends on locally pulled model; empty model list blocks analysis until configured.

---

## Decision: FFmpeg for all media operations

**Date:** 2026-09-04  
**Status:** Accepted

**Context:** Need cutting, scaling/cropping, subtitle burn-in without proprietary editors.

**Decision:** Invoke `ffmpeg` / `ffprobe` via subprocess helpers.

**Why:** Universal, scriptable, no license entanglement.

**Alternatives considered:** MoviePy-only, proprietary NLE automation.

**Consequences:** External binary required; Windows PATH/`FFMPEG_PATH` must be set.

---

## Decision: faster-whisper for transcription

**Date:** 2026-09-04  
**Status:** Accepted

**Context:** Need timestamped transcripts; GPU available (RTX 5060 Ti).

**Decision:** `faster-whisper` behind a `TranscriptionBackend` interface; model size via `WHISPER_MODEL`.

**Why:** Good CUDA performance; clean Python API; swappable later.

**Alternatives considered:** openai-whisper, cloud STT, Whisper.cpp only.

**Consequences:** First run downloads model weights; CUDA load failures fall back to CPU.

---

## Decision: Modular monolith (not microservices)

**Date:** 2026-09-04  
**Status:** Accepted

**Context:** Speed to MVP; later extractability desired.

**Decision:** One Python app with service packages and clear interfaces.

**Why:** Lowest operational complexity while preserving future service boundaries.

**Alternatives considered:** Immediate microservices, Kubernetes, multiple repos.

**Consequences:** Simple local run; must keep service boundaries clean to avoid a ball of mud.

---

## Decision: Do NOT use LangGraph / CrewAI / AutoGen / MCP in V0.1

**Date:** 2026-09-04  
**Status:** Accepted

**Context:** LLM usage is a single structured analysis call over a transcript.

**Decision:** Thin `OllamaClient` + prompt file + Pydantic validation.

**Why:** Avoid framework overhead and opaque agent graphs for one JSON extraction task.

**Alternatives considered:** LangChain/LangGraph agent pipelines, multi-agent crews.

**Consequences:** Less abstraction; easier debugging; can revisit if multi-agent workflows become necessary.

---

## Decision: Separate video engine from future Content Rewards system

**Date:** 2026-09-04  
**Status:** Accepted

**Context:** Long-term product includes campaigns, publishing, earnings; MVP must ship video-to-clips first.

**Decision:** Implement only core clip pipeline now; keep campaign/account/earnings models out of V0.1 schema.

**Why:** Prevents scope explosion; video quality is the foundation everything else depends on.

**Alternatives considered:** Build campaign tables/agents in parallel from day one.

**Consequences:** Cleaner MVP; Phase 3+ will add campaign intelligence as a separate concern.

---

## Decision: In-process job manager for async pipelines

**Date:** 2026-09-04  
**Status:** Accepted

**Context:** Transcription/render can take minutes; HTTP must not block indefinitely.

**Decision:** Single-worker `ThreadPoolExecutor` in `app/workers/jobs.py`.

**Why:** Enough for local single-user MVP without Redis/Celery.

**Alternatives considered:** Celery/RQ immediately, always-sync requests.

**Consequences:** Jobs die with process restart; concurrency limited to one pipeline; replace later (**PLANNED**).

---

## Decision: Deterministic center-crop for 9:16 in MVP

**Date:** 2026-09-04  
**Status:** Accepted

**Context:** Vertical shorts needed; face tracking adds complexity.

**Decision:** Center crop/scale via FFmpeg filter; isolate in `RenderingService._build_crop_filter`.

**Why:** Predictable, fast, good enough for many podcast layouts.

**Alternatives considered:** Face detection now, stretch-to-fill (rejected — distorts image).

**Consequences:** Off-center speakers may be cropped poorly until face-aware crop lands.
