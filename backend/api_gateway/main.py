from fastapi import FastAPI, Request, HTTPException, WebSocket
from fastapi.responses import JSONResponse, StreamingResponse
import httpx
import logging
from typing import Any

logger = logging.getLogger(__name__)
app = FastAPI(
    title="API Gateway",
    version="0.1.0",
    description="Unified entry point for AOI IC Identify system"
)

# Internal service URLs
SERVICES = {
    "inspection": "http://inspection_service:8000",
    "verification": "http://verification_service:8000",
    "decision": "http://decision_engine:8000",
    "stream": "http://stream_ingestion_service:8000",
}


@app.get("/health")
def health():
    return {"service": "api_gateway", "status": "ok"}


@app.get("/health/all")
async def health_all():
    """
    Check health of all backend services.
    """
    results = {}
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        for service_name, service_url in SERVICES.items():
            try:
                response = await client.get(f"{service_url}/health")
                results[service_name] = response.json()
            except Exception as e:
                results[service_name] = {"status": "error", "error": str(e)}
    
    return results


# ============================================================================
# Inspection Service Routes (Batch Processing)
# ============================================================================

@app.post("/api/inspections")
async def create_inspection(request: Request):
    """
    Proxy to inspection service to create a new batch inspection job.
    """
    return await proxy_post("inspection", "/inspections", request)


@app.get("/api/inspections/{job_id}")
async def get_inspection(job_id: int):
    """
    Proxy to inspection service to get job status and results.
    """
    return await proxy_get("inspection", f"/inspections/{job_id}")


@app.get("/api/inspections")
async def list_inspections(
    limit: int = 50,
    offset: int = 0,
    status: str | None = None
):
    """
    Proxy to inspection service to list jobs.
    """
    params = {"limit": limit, "offset": offset}
    if status:
        params["status"] = status
    return await proxy_get("inspection", "/inspections", params=params)


# ============================================================================
# Verification Service Routes
# ============================================================================

@app.post("/api/verify")
async def verify_component(request: Request):
    """
    Proxy to verification service for component verification.
    """
    return await proxy_post("verification", "/verify", request)


@app.post("/api/verify/ocr")
async def verify_ocr(request: Request):
    """Proxy to verification service for OCR only."""
    return await proxy_post("verification", "/verify/ocr", request)


@app.post("/api/verify/logo")
async def verify_logo(request: Request):
    """Proxy to verification service for logo detection only."""
    return await proxy_post("verification", "/verify/logo", request)


# ============================================================================
# Decision Engine Routes
# ============================================================================

@app.post("/api/decide")
async def decide(request: Request):
    """
    Proxy to decision engine for verdict computation.
    """
    return await proxy_post("decision", "/decide", request)


# ============================================================================
# Stream Ingestion Routes
# ============================================================================

@app.get("/api/live/feed")
async def live_feed():
    """
    Proxy to stream ingestion service for live video feed.
    """
    return await proxy_get("stream", "/live/feed")


@app.websocket("/api/ws/live/analysis")
async def ws_live_analysis(websocket: WebSocket):
    """
    WebSocket proxy to stream ingestion service.
    
    Note: For production, consider using a proper WebSocket proxy
    or load balancer. This is a simple pass-through for MVP.
    """
    await websocket.accept()
    logger.info("WebSocket connection to gateway established")
    
    # For simplicity, redirect client to connect directly to stream service
    # In production, implement proper WebSocket proxying
    await websocket.send_json({
        "type": "redirect",
        "message": "Connect directly to ws://localhost:8002/ws/live/analysis",
        "note": "WebSocket proxying not implemented in MVP gateway"
    })
    await websocket.close()


# ============================================================================
# Helper Functions for Proxying
# ============================================================================

async def proxy_get(service_name: str, path: str, params: dict | None = None) -> Any:
    """
    Proxy GET request to internal service.
    """
    service_url = SERVICES.get(service_name)
    if not service_url:
        raise HTTPException(status_code=500, detail=f"Unknown service: {service_name}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{service_url}{path}", params=params)
            return JSONResponse(
                content=response.json(),
                status_code=response.status_code
            )
    except httpx.HTTPStatusError as e:
        logger.error(f"Service {service_name} returned error: {e}")
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except Exception as e:
        logger.error(f"Error proxying to {service_name}: {e}")
        raise HTTPException(status_code=502, detail=f"Service unavailable: {service_name}")


async def proxy_post(service_name: str, path: str, request: Request) -> Any:
    """
    Proxy POST request to internal service.
    """
    service_url = SERVICES.get(service_name)
    if not service_url:
        raise HTTPException(status_code=500, detail=f"Unknown service: {service_name}")
    
    try:
        # Get request body
        body = await request.body()
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{service_url}{path}",
                content=body,
                headers={"Content-Type": request.headers.get("content-type", "application/json")}
            )
            return JSONResponse(
                content=response.json(),
                status_code=response.status_code
            )
    except httpx.HTTPStatusError as e:
        logger.error(f"Service {service_name} returned error: {e}")
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except Exception as e:
        logger.error(f"Error proxying to {service_name}: {e}")
        raise HTTPException(status_code=502, detail=f"Service unavailable: {service_name}")
