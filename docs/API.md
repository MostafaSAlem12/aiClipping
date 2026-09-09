# API

Only endpoints that exist in code are listed as current.

Base URL (local default): `http://127.0.0.1:8000`

Interactive docs: `GET /docs`

---

## Dashboard (HTML)

### GET `/`
**Purpose:** Upload form + video list.  
**Request:** none  
**Response:** HTML  
**Errors:** none special

### POST `/upload`
**Purpose:** Upload a video from the dashboard.  
**Request:** `multipart/form-data` field `file`  
**Response:** `303` redirect to `/videos/{id}`  
**Errors:** redirect home on missing/unsupported type

### GET `/videos/{video_id}`
**Purpose:** Video detail — status, transcript, candidates, clips.  
**Request:** path `video_id`  
**Response:** HTML (auto-refresh while processing)  
**Errors:** 404 HTML if missing

### POST `/videos/{video_id}/process`
**Purpose:** Queue pipeline from dashboard.  
**Request:** path `video_id`  
**Response:** `303` redirect to detail page  
**Errors:** no-op if already running / missing

---

## Videos API

### POST `/api/videos/upload`
**Purpose:** Upload a video file.  
**Request:** `multipart/form-data` → `file`  
**Allowed extensions:** `.mp4`, `.mov`, `.mkv`, `.webm`, `.avi`, `.m4v`  
**Response:** `VideoSummary`

```json
{
  "id": 1,
  "filename": "talk.mp4",
  "duration": null,
  "width": null,
  "height": null,
  "status": "uploaded",
  "error_message": null,
  "created_at": "2026-09-04T12:00:00Z"
}
```

**Errors:**
- `400` missing filename / unsupported type

**Example:**

```powershell
curl -F "file=@C:\videos\talk.mp4" http://127.0.0.1:8000/api/videos/upload
```

### GET `/api/videos`
**Purpose:** List videos (newest first).  
**Response:** `VideoSummary[]`  
**Errors:** none special

### GET `/api/videos/{video_id}`
**Purpose:** Video detail including transcript/candidate/clip counts.  
**Response:** `VideoDetail`

```json
{
  "id": 1,
  "filename": "talk.mp4",
  "original_path": "F:/Work/ai-video-engine/data/uploads/talk.mp4",
  "duration": 120.5,
  "width": 1920,
  "height": 1080,
  "status": "completed",
  "error_message": null,
  "created_at": "2026-09-04T12:00:00Z",
  "has_transcript": true,
  "candidate_count": 6,
  "clip_count": 3
}
```

**Errors:** `404` video not found

### POST `/api/videos/{video_id}/process`
**Purpose:** Queue the background pipeline.  
**Response:** `ProcessResponse`

```json
{
  "video_id": 1,
  "status": "queued",
  "message": "Pipeline queued. Refresh this page to track progress."
}
```

**Errors:**
- `404` video not found
- `409` could not queue job
- Returns existing status message if already running / mid-pipeline

### GET `/api/videos/{video_id}/candidates`
**Purpose:** List clip candidates (score desc).  
**Response:** `ClipCandidateOut[]`  
**Errors:** `404` video not found

### GET `/api/videos/{video_id}/clips`
**Purpose:** List generated clips with title/score.  
**Response:** `GeneratedClipOut[]`  
**Errors:** `404` video not found

---

## Clips API

### GET `/api/clips/{clip_id}/download`
**Purpose:** Download finished MP4.  
**Response:** `video/mp4` file  
**Errors:**
- `404` clip not found
- `404` file missing on disk

**Example:**

```powershell
curl -OJ http://127.0.0.1:8000/api/clips/1/download
```

---

## PLANNED endpoints (not implemented)

- Candidate approve/reject
- Pipeline cancel / retry-stage
- Campaign CRUD
- Publishing jobs
- Analytics / earnings
- Auth
