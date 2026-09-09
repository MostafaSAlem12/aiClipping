# TODO

Prioritized work list. Keep this actionable; move finished items to checked state.

## 🔴 Critical
- [ ] Install FFmpeg + ffprobe (PATH or `FFMPEG_PATH` / `FFPROBE_PATH`)
- [ ] Pull an Ollama model (`ollama pull …`) and set `OLLAMA_MODEL` in `.env`
- [ ] Run `python scripts/check_dependencies.py` until critical checks pass
- [ ] Complete one real long-form video end-to-end and verify downloads

## 🟠 High
- [ ] Capture notes from first real E2E run (bad clips, crop issues, subtitle issues)
- [ ] Sentence-boundary snapping for candidate start/end times
- [ ] Manual candidate approve/reject before render (optional toggle)
- [ ] Add a small fixture-based integration test that mocks Whisper/Ollama

## 🟡 Medium
- [ ] Prompt evaluation set (golden transcript → expected moment ranges)
- [ ] Improve quality checks (silence / black-frame heuristics)
- [ ] Persist pipeline stage timings for debugging
- [ ] Document recommended Whisper size vs VRAM tradeoffs after local benchmarks

## 🟢 Low
- [ ] Dashboard polish (progress bar, clearer error panels)
- [ ] Clip preview player in dashboard
- [ ] Export candidates as JSON from UI

## 🔵 Future
- [ ] Face/speaker-aware 9:16 crop
- [ ] Durable job queue
- [ ] PostgreSQL migration
- [ ] Campaign intelligence / Content Rewards
- [ ] Account management + publishing adapters
- [ ] Analytics + earnings feedback loop
- [ ] Auth / multi-tenant SaaS

## Completed
- [x] V0.1.0 MVP code structure and pipeline services
- [x] FastAPI REST endpoints for videos/clips
- [x] HTML dashboard upload/process/status/download
- [x] Unit test suite (20 tests)
- [x] Initial documentation system (`docs/` + `PROJECT_STATUS.md`)
