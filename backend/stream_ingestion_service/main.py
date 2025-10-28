from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import StreamingResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import asyncio
import logging
import time
import json
import cv2
import base64
from typing import Optional, Literal

from shared.models import LiveFrameAnalysis, SignalEvidence
from .camera import CameraStream

logger = logging.getLogger(__name__)
app = FastAPI(title="Stream Ingestion & Processing Service", version="0.2.0")

# CORS: allow frontend on 3000 to call camera endpoints
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service URLs
VERIFICATION_SERVICE_URL = "http://verification_service:8000"
DECISION_ENGINE_URL = "http://decision_engine:8000"
INSPECTION_SERVICE_URL = "http://inspection_service:8000"

# Global camera instance
camera: Optional[CameraStream] = None
analysis_paused: bool = False
current_run_id: Optional[int] = None

# Analysis configuration
AnalysisMode = Literal["conveyor", "single"]
analysis_mode: AnalysisMode = "conveyor"
store_snapshots: bool = True
delete_snapshot_after_analysis: bool = True
sampling_every_n_frames: int = 30  # Will be auto-set based on FPS on start
frames_analyzed_count: int = 0
last_ic_key: Optional[str] = None
awaiting_new_ic: bool = False
SNAPSHOT_DIR = "/tmp/stream_snapshots"


class CameraStartRequest(BaseModel):
    """Request to start camera."""
    camera_url: str


@app.get("/health")
def health():
    global camera
    return {
        "service": "stream_ingestion_service",
        "status": "ok",
        "camera_active": camera is not None and camera.is_running()
    }


@app.post("/camera/start")
async def start_camera(request: CameraStartRequest):
    """
    Start camera stream from provided URL.
    
    Supports:
    - RTSP: rtsp://192.168.1.100:8080/h264
    - HTTP MJPEG: http://192.168.1.100:8080/video
    - USB camera: 0, 1, 2...
    """
    global camera, current_run_id
    
    # Stop existing camera if running
    if camera and camera.is_running():
        logger.info("Stopping existing camera")
        camera.stop()
    
    # Start new camera
    logger.info(f"Starting camera: {request.camera_url}")
    camera = CameraStream(request.camera_url)
    
    if not camera.start():
        camera = None
        raise HTTPException(status_code=400, detail="Failed to start camera")
    
    # Auto-select sampling interval based on FPS
    try:
        cam_stats = camera.get_stats()
        fps = cam_stats.get("fps") or 30
        # Choose 60 for >=50 FPS, else 30; not less than 30
        n = 60 if fps and fps >= 50 else 30
        global sampling_every_n_frames
        sampling_every_n_frames = n
        logger.info(f"Auto sampling interval set to every {sampling_every_n_frames} frames (fps={fps})")
    except Exception as e:
        logger.warning(f"Failed to determine FPS for sampling: {e}")
        sampling_every_n_frames = 30
    
    # Reset counters
    global frames_analyzed_count, last_ic_key, awaiting_new_ic
    frames_analyzed_count = 0
    last_ic_key = None
    awaiting_new_ic = False
    
    # Create live inspection run in database
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{INSPECTION_SERVICE_URL}/live/runs",
                params={"camera_source": request.camera_url}
            )
            if response.status_code == 200:
                data = response.json()
                current_run_id = data.get("run_id")
                logger.info(f"Created live inspection run: {current_run_id}")
    except Exception as e:
        logger.error(f"Failed to create live inspection run: {e}")
        current_run_id = None
    
    return {
        "status": "started",
        "source": request.camera_url,
        "run_id": current_run_id,
        "stats": camera.get_stats()
    }


@app.post("/camera/stop")
async def stop_camera():
    """Stop active camera stream."""
    global camera, current_run_id
    
    if not camera:
        return {"status": "no_camera"}
    
    stats = camera.get_stats()
    total_frames = stats.get("frame_count", 0)
    
    camera.stop()
    camera = None
    
    # Complete live inspection run if exists
    if current_run_id:
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{INSPECTION_SERVICE_URL}/live/runs/{current_run_id}/complete",
                    params={"total_frames": total_frames}
                )
                logger.info(f"Completed live inspection run: {current_run_id}")
        except Exception as e:
            logger.error(f"Failed to complete live inspection run: {e}")
        current_run_id = None
    
    return {"status": "stopped"}


@app.post("/camera/pause")
def pause_analysis():
    """Pause analysis without stopping camera."""
    global analysis_paused
    analysis_paused = True
    return {"status": "paused"}


@app.post("/camera/resume")
def resume_analysis():
    """Resume analysis."""
    global analysis_paused
    analysis_paused = False
    return {"status": "resumed"}


@app.get("/analysis/config")
def get_analysis_config():
    """Get current analysis configuration."""
    global analysis_mode, store_snapshots, delete_snapshot_after_analysis, sampling_every_n_frames
    return {
        "analysis_mode": analysis_mode,
        "store_snapshots": store_snapshots,
        "delete_after": delete_snapshot_after_analysis,
        "sampling_every_n_frames": sampling_every_n_frames,
    }


class AnalysisConfigRequest(BaseModel):
    analysis_mode: AnalysisMode
    store_snapshots: Optional[bool] = None
    delete_after: Optional[bool] = None
    sampling_every_n_frames: Optional[int] = None  # Optional manual override (30 or 60)


@app.post("/analysis/config")
def set_analysis_config(cfg: AnalysisConfigRequest):
    """Update analysis configuration."""
    global analysis_mode, store_snapshots, delete_snapshot_after_analysis, sampling_every_n_frames
    analysis_mode = cfg.analysis_mode
    if cfg.store_snapshots is not None:
        store_snapshots = cfg.store_snapshots
    if cfg.delete_after is not None:
        delete_snapshot_after_analysis = cfg.delete_after
    if cfg.sampling_every_n_frames is not None:
        # Respect constraints: only 30 or 60, min 30
        n = cfg.sampling_every_n_frames
        if n not in (30, 60):
            n = 30 if n and n < 60 else 60
        sampling_every_n_frames = max(30, n)
    return get_analysis_config()


@app.get("/camera/stats")
def get_camera_stats():
    """Get camera statistics."""
    global camera, analysis_paused, frames_analyzed_count, analysis_mode, sampling_every_n_frames
    
    if not camera:
        return {"status": "no_camera"}
    
    stats = camera.get_stats()
    stats["analysis_paused"] = analysis_paused
    stats["frames_analyzed"] = frames_analyzed_count
    stats["analysis_mode"] = analysis_mode
    stats["sampling_every_n_frames"] = sampling_every_n_frames
    return stats


@app.get("/live/feed")
def live_feed():
    """
    Stream live video feed as MJPEG.
    
    Returns multipart/x-mixed-replace stream for display in <img> tag.
    """
    global camera
    
    if not camera or not camera.is_running():
        return PlainTextResponse(
            "Camera not started. Use POST /camera/start first.",
            status_code=503
        )
    
    def generate():
        """Generate MJPEG stream."""
        while camera and camera.is_running():
            frame = camera.get_frame(timeout=1.0)
            
            if frame is None:
                continue
            
            # Encode as JPEG (quality 85)
            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            
            if not ret:
                continue
            
            # Send frame in multipart format
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + 
                   buffer.tobytes() + b'\r\n')
    
    return StreamingResponse(
        generate(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


@app.websocket("/ws/live/analysis")
async def ws_live_analysis(websocket: WebSocket):
    """
    WebSocket endpoint for real-time frame-by-frame analysis using camera.
    
    Workflow:
    1. Accept WebSocket connection
    2. Check if camera is active
    3. For each camera frame:
       - Encode frame to base64
       - Call verification service
       - Call decision engine  
       - Push results to client
    4. Handle capture events from client
    """
    global camera
    await websocket.accept()
    logger.info("WebSocket connection established")
    
    # Check if camera is active
    if not camera or not camera.is_running():
        await websocket.send_json({
            "type": "error",
            "message": "Camera not started. Start camera first via /camera/start"
        })
        await websocket.close()
        return
    
    try:
        # Send initial message
        await websocket.send_json({
            "type": "connected",
            "message": "Live analysis stream connected",
            "service": "stream_ingestion_service",
            "camera_source": camera.source
        })
        
        frame_id = 0
        frames_since_analysis = 0
        OCR_DETECT_EVERY_N_FRAMES = 10  # For 'single' mode new-IC detection
        
        while camera and camera.is_running():
            # Check for incoming messages (capture requests, etc.)
            try:
                message = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=0.01
                )
                client_msg = json.loads(message)
                
                if client_msg.get("type") == "capture":
                    logger.info(f"Capture requested at frame {frame_id}")
                    await websocket.send_json({
                        "type": "capture_ack",
                        "frame_id": frame_id,
                        "message": "Frame captured and saved"
                    })
            except asyncio.TimeoutError:
                pass
            
            # Get frame from camera
            frame = camera.get_frame(timeout=1.0)
            
            if frame is None:
                await asyncio.sleep(0.1)
                continue
            
            frame_id += 1
            frames_since_analysis += 1
            
            # Skip analysis if paused
            if analysis_paused:
                await asyncio.sleep(0.05)
                continue
            
            # Encode frame to JPEG bytes
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                continue
            frame_bytes = buffer.tobytes()
            frame_base64 = base64.b64encode(frame_bytes).decode('utf-8')
            frame_data = f"data:image/jpeg;base64,{frame_base64}"
            
            # Analysis behavior by mode
            if analysis_mode == "conveyor":
                # Analyze every Nth frame based on FPS (30 or 60), never less frequent than 30
                if frames_since_analysis < sampling_every_n_frames:
                    await asyncio.sleep(0.005)
                    continue
                frames_since_analysis = 0
                
                # Optionally snapshot to disk
                snapshot_path = None
                if store_snapshots:
                    try:
                        import os
                        os.makedirs(SNAPSHOT_DIR, exist_ok=True)
                        snapshot_path = f"{SNAPSHOT_DIR}/run_{current_run_id or 'na'}_f{frame_id}.jpg"
                        with open(snapshot_path, 'wb') as f:
                            f.write(frame_bytes)
                    except Exception as e:
                        logger.warning(f"Failed to save snapshot: {e}")
                
                # Perform analysis
                analysis = await analyze_frame_async(frame_data, frame_id)
                
                # Delete snapshot after analysis if configured
                if snapshot_path and delete_snapshot_after_analysis:
                    try:
                        import os
                        os.remove(snapshot_path)
                    except Exception:
                        pass
                
                # Persist result
                await persist_and_emit_analysis(websocket, analysis, frame_id)
                
            else:  # single (1-by-1)
                if not awaiting_new_ic:
                    # Analyze current frame and then wait for next IC
                    analysis = await analyze_frame_async(frame_data, frame_id)
                    # Set current ic key from OCR
                    set_ic_key_from_analysis(analysis)
                    awaiting_new_ic = True
                    await persist_and_emit_analysis(websocket, analysis, frame_id)
                    continue
                
                # Waiting for new IC: do lightweight OCR check every few frames
                if frames_since_analysis % OCR_DETECT_EVERY_N_FRAMES != 0:
                    await asyncio.sleep(0.005)
                    continue
                
                new_key = await quick_ocr_key(frame_data)
                if new_key and new_key != (last_ic_key or ""):
                    # New IC detected, analyze this frame
                    analysis = await analyze_frame_async(frame_data, frame_id)
                    set_ic_key_from_analysis(analysis)
                    awaiting_new_ic = True  # Will remain true until next new IC
                    await persist_and_emit_analysis(websocket, analysis, frame_id)
                else:
                    # Keep waiting
                    await asyncio.sleep(0.01)
    
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected by client")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
            pass
        logger.info("WebSocket connection closed")


def normalize_ic_key(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    return ''.join(ch for ch in text.upper() if ch.isalnum()) or None


def set_ic_key_from_analysis(analysis: LiveFrameAnalysis):
    global last_ic_key
    last_ic_key = normalize_ic_key(analysis.ocr_text)


async def quick_ocr_key(frame_data: str) -> Optional[str]:
    """Run OCR-only verification to detect IC text quickly."""
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.post(
                f"{VERIFICATION_SERVICE_URL}/verify",
                json={
                    "image_data": frame_data,
                    "verification_types": ["ocr"]
                }
            )
            data = resp.json()
            return normalize_ic_key(data.get("ocr", {}).get("text"))
    except Exception as e:
        logger.debug(f"quick_ocr_key error: {e}
")
        return None


async def persist_and_emit_analysis(websocket: WebSocket, analysis: LiveFrameAnalysis, frame_id: int):
    """Persist analysis to DB (if configured) and emit to client."""
    # Persist
    if current_run_id and analysis.verdict:
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                await client.post(
                    f"{INSPECTION_SERVICE_URL}/live/runs/{current_run_id}/frames",
                    params={
                        "frame_id": frame_id,
                        "verdict": analysis.verdict,
                        "confidence": analysis.confidence,
                        "ocr_text": analysis.ocr_text,
                        "logo_manufacturer": analysis.logo_manufacturer,
                    },
                    json={"analysis_data": analysis.model_dump()}
                )
        except Exception as e:
            logger.warning(f"Failed to store frame result: {e}")
    
    # Emit
    await websocket.send_json({
        "type": "analysis",
        "data": analysis.model_dump()
    })


async def analyze_frame_async(frame_data: str, frame_id: int) -> LiveFrameAnalysis:
    """
    Perform real-time analysis on a single frame.
    
    In production:
    - Preprocess frame (resize, enhance)
    - Extract ROIs
    - Run OCR and logo detection (fast models)
    - Optionally skip visual signature/anomaly for speed
    - Return immediate verdict
    """
    start_time = time.time()
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Call verification service (subset for speed)
            verify_response = await client.post(
                f"{VERIFICATION_SERVICE_URL}/verify",
                json={
                    "image_data": frame_data,
                    "verification_types": ["ocr", "logo"]  # Skip slow signals for real-time
                }
            )
            verify_data = verify_response.json()
            
            # Prepare signals
            signals = []
            if verify_data.get("ocr"):
                signals.append({
                    "signal_type": "ocr",
                    "confidence": verify_data["ocr"]["confidence"],
                    "data": verify_data["ocr"]
                })
            if verify_data.get("logo"):
                signals.append({
                    "signal_type": "logo",
                    "confidence": verify_data["logo"]["confidence"],
                    "data": verify_data["logo"]
                })
            
            # Call decision engine if we have signals
            verdict = None
            confidence = None
            notes = []
            
            if signals:
                decision_response = await client.post(
                    f"{DECISION_ENGINE_URL}/decide",
                    json={"signals": signals}
                )
                decision_data = decision_response.json()
                verdict = decision_data.get("verdict")
                confidence = decision_data.get("confidence")
                notes = decision_data.get("notes", [])
    
    except Exception as e:
        logger.error(f"Error analyzing frame {frame_id}: {e}")
        verdict = "error"
        confidence = 0.0
        notes = [f"Analysis error: {str(e)}"]
        verify_data = {}
    
    processing_time = time.time() - start_time
    
    global frames_analyzed_count
    result = LiveFrameAnalysis(
        frame_id=frame_id,
        timestamp=time.time(),
        verdict=verdict,
        confidence=confidence,
        ocr_text=verify_data.get("ocr", {}).get("text"),
        logo_manufacturer=verify_data.get("logo", {}).get("manufacturer"),
        bounding_boxes=[
            verify_data.get("ocr", {}).get("bounding_box", {}),
            verify_data.get("logo", {}).get("bounding_box", {}),
        ],
        notes=notes + [f"Processing time: {processing_time*1000:.1f}ms"],
    )
    # Count only full analyses (i.e., when we called analyze_frame_async)
    frames_analyzed_count += 1
    return result
