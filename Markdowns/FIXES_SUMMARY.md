# Live Analysis Fixes Summary

## Issues Addressed

Based on the logs analysis, three major issues were identified and fixed:

1. **Overwhelming number of frames** - Too many frames processed, no visible analysis results
2. **Stopping camera aborts inspection** - Only stop option available, which terminates the session
3. **No inspection history** - No way to view past inspections

---

## 1. Frame Throttling (Issue: Overwhelming Frames)

### Problem
- Every frame from camera (30 FPS) was being analyzed
- Lines 369-468 in logs show continuous POST /verify requests
- Frontend couldn't keep up with results display

### Solution
**Backend Changes** (`backend/stream_ingestion_service/main.py`):
- Added `ANALYSIS_EVERY_N_FRAMES = 15` constant
- Process only every 15th frame (~2 FPS at 30 FPS camera)
- Reduced processing load by 93%

```python
# Frame throttling: only analyze every Nth frame
if frames_since_analysis < ANALYSIS_EVERY_N_FRAMES:
    await asyncio.sleep(0.01)
    continue
```

### Impact
- Manageable analysis rate: ~2 FPS instead of 30 FPS
- Frontend can display results in real-time
- Reduced server load significantly

---

## 2. Pause/Resume Functionality (Issue: Stop Aborts Inspection)

### Problem
- Line 469 in logs: POST /camera/stop
- Line 470: connection closed
- No way to pause and review results without ending session

### Solution
**Backend Changes** (`backend/stream_ingestion_service/main.py`):
- Added global `analysis_paused: bool = False` state
- Added `/camera/pause` endpoint
- Added `/camera/resume` endpoint
- Modified WebSocket to skip analysis when paused
- Updated `/camera/stats` to include pause state

**Frontend Changes** (`frontend/app/live/page.tsx`):
- Added Pause/Resume buttons (replacing single Stop button)
- Show Resume button when paused, Pause button when active
- Stop button remains but is now separate action
- Visual indicators: ⏸ Pause, ▶ Resume, ⏹ Stop

### Impact
- Users can pause analysis to review results
- Camera continues running (no reconnection needed)
- Inspection session persists until explicitly stopped

---

## 3. Inspection History (Issue: No History)

### Problem
- No database persistence for live inspections
- No UI to view past inspections
- Lost all data after stopping camera

### Solution

#### Database Models (`backend/inspection_service/models.py`)
Added two new tables:
- `LiveInspectionRun` - Tracks live inspection sessions
  - Camera source, status, timestamps
  - Summary stats: pass/fail/review counts
- `LiveFrameResult` - Individual frame analysis results
  - Frame ID, verdict, confidence, OCR/logo data

#### Backend Endpoints (`backend/inspection_service/main.py`)
**Live inspection management:**
- `POST /live/runs` - Create new live run session
- `POST /live/runs/{run_id}/frames` - Store frame result
- `POST /live/runs/{run_id}/complete` - Mark run completed
- `GET /live/runs` - List all live runs
- `GET /live/runs/{run_id}` - Get run details with frames

**Combined history:**
- `GET /history` - Get all inspections (batch + live)
  - Filterable by type: "batch", "live", or all
  - Sorted by date (most recent first)

#### Stream Ingestion Integration (`backend/stream_ingestion_service/main.py`)
- Camera start creates live run in database
- Each analyzed frame stored to database
- Camera stop marks run as completed
- Tracks global `current_run_id` for session

#### Frontend Pages
**History List** (`frontend/app/history/page.tsx`):
- Shows all batch and live inspections
- Filter tabs: All / Batch / Live
- Displays key metrics per inspection
- Click to view details

**Live Details** (`frontend/app/history/live/[id]/page.tsx`):
- Summary card: status, duration, frames analyzed
- Results overview: pass/fail/review counts
- Expandable frame results list
- Each frame shows verdict, confidence, OCR, logo

**Navigation** (`frontend/app/layout.tsx`):
- Added "History" link to main navigation

### Impact
- All live inspections persisted to database
- Full audit trail of analysis results
- Historical data accessible anytime
- Users can review past sessions

---

## Technical Details

### Frame Throttling Algorithm
```python
ANALYSIS_EVERY_N_FRAMES = 15
frames_since_analysis = 0

while camera.is_running():
    frame = camera.get_frame()
    frames_since_analysis += 1
    
    if frames_since_analysis < ANALYSIS_EVERY_N_FRAMES:
        continue
    
    frames_since_analysis = 0
    # Process frame...
```

### Pause State Management
```python
# Backend state
global analysis_paused: bool = False

# WebSocket processing
if analysis_paused:
    await asyncio.sleep(0.05)
    continue  # Skip analysis
```

### Database Persistence Flow
```
1. POST /camera/start
   └─> Create LiveInspectionRun → get run_id

2. WebSocket analysis loop
   └─> For each analyzed frame:
       └─> POST /live/runs/{run_id}/frames
           └─> Store frame result + update stats

3. POST /camera/stop
   └─> POST /live/runs/{run_id}/complete
       └─> Mark completed + final stats
```

---

## Testing Recommendations

1. **Frame Throttling**
   - Start camera with high FPS source
   - Verify analysis rate is ~2 FPS
   - Check logs for reduced /verify requests

2. **Pause/Resume**
   - Start live analysis
   - Click Pause - verify analysis stops but camera runs
   - Click Resume - verify analysis resumes
   - Click Stop - verify clean shutdown

3. **History**
   - Complete a live inspection session
   - Navigate to History page
   - Verify session appears in list
   - Click to view details
   - Verify frame results are stored

---

## Configuration Options

### Adjustable Parameters

**Frame Rate** (`backend/stream_ingestion_service/main.py:207`):
```python
ANALYSIS_EVERY_N_FRAMES = 15  # Adjust based on needs
# 15 frames = ~2 FPS at 30 FPS camera
# 30 frames = ~1 FPS at 30 FPS camera
# 10 frames = ~3 FPS at 30 FPS camera
```

**History Limit** (API query parameter):
```
GET /history?limit=100  # Default: 50
```

**Frame Storage** (optional optimization):
- Currently stores all analyzed frames
- Can add sampling to store only significant frames
- Can add retention policy for old data

---

## Database Migration

New tables require database migration. The tables will be auto-created on service startup due to:
```python
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
```

For production, use proper migrations (Alembic):
```bash
alembic revision --autogenerate -m "Add live inspection tables"
alembic upgrade head
```

---

## API Documentation

### New Endpoints

#### Live Inspection Management
- `POST /live/runs?camera_source=<url>` - Create run
- `POST /live/runs/{id}/frames` - Store frame result
- `POST /live/runs/{id}/complete?total_frames=<n>` - Complete run
- `GET /live/runs` - List runs
- `GET /live/runs/{id}?include_frames=true` - Get details

#### Pause/Resume
- `POST /camera/pause` - Pause analysis
- `POST /camera/resume` - Resume analysis

#### History
- `GET /history?inspection_type=<batch|live|all>` - Combined history

---

## Performance Impact

- **Frame processing**: 93% reduction (30 FPS → 2 FPS)
- **Database writes**: ~2 writes/second (manageable)
- **Memory usage**: Minimal increase (state tracking)
- **Network traffic**: 93% reduction to verification service

---

## Future Enhancements

1. **Configurable throttling** - UI control for frame rate
2. **Snapshot capture** - Save specific frames of interest
3. **Export history** - Download results as CSV/JSON
4. **Real-time charts** - Show pass/fail trends during live session
5. **Alert thresholds** - Notify on fail rate exceeding threshold
