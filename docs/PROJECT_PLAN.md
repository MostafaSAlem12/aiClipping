# Project Plan

## Phase 0 — Planning
**Status:** COMPLETED

**Objective:** Define MVP scope, stack constraints, and modular monolith boundaries.

**Tasks:**
- [x] Product vision and MVP user flow
- [x] Stack decisions (FastAPI, SQLite, Ollama, FFmpeg, faster-whisper)
- [x] Explicit non-goals for V0.1 (no LangChain/CrewAI/Redis/K8s/cloud)
- [x] Documentation system (`docs/` + `PROJECT_STATUS.md`)

**Dependencies:** None.

**Completion criteria:** Clear MVP scope and architecture decisions recorded.

---

## Phase 1 — Video Engine MVP
**Status:** COMPLETED (code + unit tests) / BLOCKED (real E2E on this machine)

**Objective:** Local Windows app that turns one uploaded long-form video into scored vertical short clips with subtitles.

**Tasks:**
- [x] Project structure
- [x] Configuration
- [x] FastAPI
- [x] SQLite
- [x] Upload
- [x] Video metadata
- [x] Whisper (faster-whisper service)
- [x] Ollama integration
- [x] Candidate detection
- [x] Candidate scoring / selection
- [x] Clip extraction
- [x] 9:16 rendering (center crop)
- [x] Subtitles
- [x] Dashboard
- [x] Unit tests
- [ ] First successful real-video E2E run on this workstation

**Dependencies:** FFmpeg, Ollama + pulled model, GPU/CPU Whisper runtime.

**Completion criteria:**
- Code paths for full pipeline exist and are unit-tested where practical.
- Dashboard + API can upload, process (async), list candidates/clips, download.
- Real E2E still pending local FFmpeg + model setup.

---

## Phase 2 — Quality Improvement
**Status:** PLANNED

**Objective:** Improve clip usefulness and vertical framing quality.

**Tasks:**
- [ ] Sentence-boundary snapping using transcript timestamps
- [ ] Better hook/title prompt iteration and evaluation set
- [ ] Optional face/speaker-aware crop
- [ ] Richer quality checks (black frames, silence, subtitle overflow)
- [ ] Manual approve/reject UI for candidates
- [ ] Integration test harness with fixture media (no GPU required where possible)

**Dependencies:** Phase 1 E2E working.

**Completion criteria:** Measurably fewer weak/mid-sentence clips; crop keeps speakers usable on sample podcasts.

---

## Phase 3 — Campaign Intelligence
**Status:** PLANNED

**Objective:** Connect clip selection to Content Rewards campaign goals.

**Tasks:**
- [ ] Campaign data model
- [ ] Campaign brief → clip scoring biases
- [ ] Target platform / format rules
- [ ] Campaign Agent interface (still local/modular; no cloud requirement yet)

**Dependencies:** Phase 2 baseline quality.

**Completion criteria:** Candidates can be scored against an explicit campaign brief.

---

## Phase 4 — Account Management
**Status:** PLANNED

**Objective:** Manage creator/social accounts used for publishing.

**Tasks:**
- [ ] Account entities and credentials vaulting approach
- [ ] Platform connection status
- [ ] Permission scopes documentation

**Dependencies:** Phase 3 campaign model.

**Completion criteria:** Accounts can be registered and selected per campaign without publishing yet.

---

## Phase 5 — Publishing Automation
**Status:** PLANNED

**Objective:** Publish approved clips to social platforms.

**Tasks:**
- [ ] Publish job model
- [ ] Platform adapters
- [ ] Scheduling
- [ ] Failure/retry handling

**Dependencies:** Phase 4 accounts; platform API access.

**Completion criteria:** Approved clip can be published to at least one platform with audit trail.

**Constraint:** No view manipulation or platform abuse features.

---

## Phase 6 — Analytics
**Status:** PLANNED

**Objective:** Ingest and display post performance.

**Tasks:**
- [ ] Metrics schema (views, watch time, CTR proxies if available)
- [ ] Sync jobs
- [ ] Dashboard charts

**Dependencies:** Phase 5 publishing.

**Completion criteria:** Per-clip performance visible in dashboard.

---

## Phase 7 — Earnings Optimization
**Status:** PLANNED

**Objective:** Track earnings and learn which clip patterns perform.

**Tasks:**
- [ ] Earnings ingestion
- [ ] Simple feedback into scoring weights
- [ ] Reporting

**Dependencies:** Phase 6 analytics + campaign payouts data.

**Completion criteria:** Historical earnings influence future candidate ranking in a transparent way.

---

## Phase 8 — SaaS Product
**Status:** PLANNED

**Objective:** Multi-user productization.

**Tasks:**
- [ ] AuthN/AuthZ
- [ ] Multi-tenant data isolation
- [ ] Billing
- [ ] Managed workers / queue
- [ ] PostgreSQL migration
- [ ] Hosted deployment

**Dependencies:** Stable local product through Phase 6–7 lessons.

**Completion criteria:** External users can sign up, process videos, and manage campaigns safely.
