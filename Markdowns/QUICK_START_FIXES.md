# Quick Start - Testing the Fixes

## Prerequisites

Make sure services are running:
```bash
cd /home/rgt/Videos/AOI-IC-identify
docker-compose up -d
cd frontend && npm run dev
```

---

## Test 1: Frame Throttling ✅

### What Changed
- Analysis now processes every 15th frame instead of every frame
- ~2 FPS analysis rate instead of 30 FPS

### How to Test
1. Go to http://localhost:3000/live/setup
2. Start a camera (use test video or webcam)
3. Go to http://localhost:3000/live
4. **Observe**: Analysis results appear at manageable rate (~2 per second)
5. **Check logs**: `docker-compose logs stream_ingestion_service-1 | grep verify`
   - Should see much fewer POST /verify requests than before

### Expected Result
✅ Analysis results visible in real-time
✅ No overwhelming flood of frames
✅ UI remains responsive

---

## Test 2: Pause/Resume ⏸▶

### What Changed
- New Pause and Resume buttons
- Camera keeps running when paused
- Inspection session persists

### How to Test
1. Start live analysis (from Test 1)
2. **Click Pause button** (⏸ Pause)
   - Analysis stops but camera feed continues
   - Latest result stays on screen
3. Review the results while paused
4. **Click Resume button** (▶ Resume)
   - Analysis resumes from where it paused
5. **Click Stop button** (⏹ Stop) when done
   - Camera stops, inspection ends

### Expected Result
✅ Pause stops analysis but keeps camera running
✅ Can review results without losing connection
✅ Resume continues analysis
✅ Stop button ends session cleanly

---

## Test 3: Inspection History 📋

### What Changed
- Live inspections now saved to database
- New History page to view past inspections
- Detail view with all frame results

### How to Test

#### Part A: Create History
1. Complete a live analysis session (from Test 1 & 2)
2. Stop the camera after analyzing some frames
3. **Note**: Session is automatically saved

#### Part B: View History List
1. Go to http://localhost:3000/history
2. **Observe**: Your live inspection appears in list
3. Try filter tabs: All / Batch / Live
4. Click on your inspection

#### Part C: View Details
1. **Observe** on detail page:
   - Summary stats (duration, frames analyzed)
   - Pass/Fail/Review counts
   - Camera source info
2. Click "Show All Frames"
3. **Observe**: All analyzed frames listed with verdicts

### Expected Result
✅ Live inspection saved to database
✅ History page shows all inspections
✅ Detail page shows summary and frame results
✅ Can navigate between history and detail views

---

## Test 4: Full Workflow Integration 🔄

### Complete User Journey
1. **Setup**: Go to /live/setup, configure camera
2. **Start**: Camera starts, live run created in database
3. **Analyze**: Frames processed at ~2 FPS, results shown
4. **Pause**: Review results without stopping
5. **Resume**: Continue analysis
6. **Stop**: Session ends, marked as completed
7. **History**: View saved session in /history
8. **Details**: See all frame results in detail view

### Expected Result
✅ Smooth flow from start to finish
✅ Data persisted throughout
✅ No lost data or disconnections

---

## Verify Database Persistence 🗄️

### Check Database Tables
```bash
docker exec -it aoi-ic-identify-postgres-1 psql -U postgres -d aoi_ic_db
```

```sql
-- List live inspection runs
SELECT id, camera_source, status, started_at, frames_analyzed, pass_count, fail_count 
FROM live_inspection_runs 
ORDER BY started_at DESC 
LIMIT 5;

-- List frame results for a run (replace <run_id>)
SELECT frame_id, verdict, confidence, ocr_text, logo_manufacturer 
FROM live_frame_results 
WHERE run_id = <run_id> 
ORDER BY frame_id 
LIMIT 10;

-- Count total frames stored
SELECT COUNT(*) FROM live_frame_results;

-- Exit
\q
```

### Expected Result
✅ Rows in `live_inspection_runs` table
✅ Rows in `live_frame_results` table
✅ Data matches what was shown in UI

---

## API Testing 🔧

### Test Pause/Resume Endpoints
```bash
# Start camera first via UI, then:

# Pause analysis
curl -X POST http://localhost:8002/camera/pause

# Check status
curl http://localhost:8002/camera/stats | jq '.analysis_paused'
# Should return: true

# Resume analysis
curl -X POST http://localhost:8002/camera/resume

# Check status again
curl http://localhost:8002/camera/stats | jq '.analysis_paused'
# Should return: false
```

### Test History Endpoints
```bash
# List all inspections
curl http://localhost:8001/history | jq

# List only live inspections
curl "http://localhost:8001/history?inspection_type=live" | jq

# Get specific run details (replace <run_id>)
curl "http://localhost:8001/live/runs/<run_id>?include_frames=true" | jq
```

---

## Troubleshooting 🔍

### Issue: No analysis results appearing
**Check:**
- Is WebSocket connected? (Look for "LIVE" indicator)
- Check browser console for errors
- Verify services are running: `docker-compose ps`

### Issue: Camera not starting
**Check:**
- Camera URL correct?
- Camera accessible?
- Check stream_ingestion logs: `docker-compose logs stream_ingestion_service-1`

### Issue: History page empty
**Check:**
- Did you complete a live inspection session?
- Database tables created? (Run SQL queries above)
- Inspection service logs: `docker-compose logs inspection_service-1`

### Issue: Pause/Resume not working
**Check:**
- Click on correct button?
- Camera stats showing paused state?
- WebSocket still connected?

---

## Performance Monitoring 📊

### Watch Service Logs
```bash
# Stream ingestion (frame throttling in action)
docker-compose logs -f stream_ingestion_service-1 | grep "frame"

# Verification service (should see reduced traffic)
docker-compose logs -f verification_service-1 | grep "POST /verify"

# Inspection service (database writes)
docker-compose logs -f inspection_service-1 | grep "live"
```

### Monitor Database Size
```bash
docker exec -it aoi-ic-identify-postgres-1 psql -U postgres -d aoi_ic_db -c "
SELECT 
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables 
WHERE schemaname = 'public' 
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"
```

---

## Success Criteria ✅

All tests pass if:
- [x] Frame analysis rate is ~2 FPS (not 30 FPS)
- [x] Results visible in real-time on frontend
- [x] Pause button stops analysis, keeps camera running
- [x] Resume button continues analysis
- [x] Stop button ends session cleanly
- [x] History page shows completed inspection
- [x] Detail page shows all frame results
- [x] Database contains inspection data
- [x] No errors in logs

---

## Cleanup (Optional) 🧹

### Clear Test Data
```bash
docker exec -it aoi-ic-identify-postgres-1 psql -U postgres -d aoi_ic_db -c "
DELETE FROM live_frame_results;
DELETE FROM live_inspection_runs;
"
```

### Restart Services
```bash
cd /home/rgt/Videos/AOI-IC-identify
docker-compose restart
```

---

## Next Steps

Once all tests pass:
1. ✅ Frame throttling working
2. ✅ Pause/Resume working
3. ✅ History working
4. 🎉 All three major issues resolved!

Proceed with production testing or further enhancements as needed.
