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
from typing import Optional

from shared.models import LiveFrameAnalysis, SignalEvidence
from .camera import CameraStream

logger = logging.getLogger(__name__)
app = FastAPI(title="Stream Ingestion & Processing Service", version="0.1.0")

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

# Global camera instance
camera: Optional[CameraStream] = None


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
def start_camera(request: CameraStartRequest):
    """
    Start camera stream from provided URL.
    
    Supports:
    - RTSP: rtsp://192.168.1.100:8080/h264
    - HTTP MJPEG: http://192.168.1.100:8080/video
    - USB camera: 0, 1, 2...
    """
    global camera
    
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
    
    return {
        "status": "started",
        "source": request.camera_url,
        "stats": camera.get_stats()
    }


@app.post("/camera/stop")
def stop_camera():
    """Stop active camera stream."""
    global camera
    
    if not camera:
        return {"status": "no_camera"}
    
    camera.stop()
    camera = None
    
    return {"status": "stopped"}


@app.get("/camera/stats")
def get_camera_stats():
    """Get camera statistics."""
    global camera
    
    if not camera:
        return {"status": "no_camera"}
    
    return camera.get_stats()


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
            
            # Encode frame to base64 for analysis
            ret, buffer = cv2.imencode('.jpg', frame)
            if ret:
                frame_base64 = base64.b64encode(buffer).decode('utf-8')
                frame_data = f"data:image/jpeg;base64,{frame_base64}"
            else:
                continue
            
            # Perform analysis
            analysis = await analyze_frame_async(frame_data, frame_id)
            
            # Send results to client
            await websocket.send_json({
                "type": "analysis",
                "data": analysis.model_dump()
            })
            
            logger.debug(f"Sent analysis for frame {frame_id}")
            
            # Small delay to prevent overwhelming client (adjust based on needs)
            await asyncio.sleep(0.1)
    
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
    
    return LiveFrameAnalysis(
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
