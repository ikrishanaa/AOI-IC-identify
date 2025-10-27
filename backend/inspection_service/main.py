from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from celery import Celery
import logging
from typing import Optional

from shared.db import Base, engine, check_connection, get_db
from shared.config import get_settings
from shared.models import InspectionCreateRequest, InspectionStatusResponse
from .models import InspectionJob, InspectionResult, LiveInspectionRun, LiveFrameResult

logger = logging.getLogger(__name__)
app = FastAPI(title="Inspection Management Service", version="0.1.0")

# Celery client for task publishing
settings = get_settings()
celery_app = Celery(
    "inspection_client",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)


@app.on_event("startup")
def on_startup():
    # Create tables if they don't exist (dev convenience)
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"service": "inspection_service", "status": "ok"}


@app.get("/db/health")
def db_health():
    try:
        ok = check_connection()
        return {"service": "inspection_service", "db": "ok" if ok else "unreachable"}
    except SQLAlchemyError as e:
        return {"service": "inspection_service", "db": "error", "detail": str(e)}


# ============================================================================
# Batch Inspection Endpoints
# ============================================================================

@app.post("/inspections", response_model=InspectionStatusResponse)
def create_inspection(request: InspectionCreateRequest, db: Session = Depends(get_db)):
    """
    Create a new batch inspection job and enqueue for processing.
    
    Workflow:
    1. Persist job metadata to database
    2. Enqueue Celery task for async processing
    3. Return job_id immediately (non-blocking)
    """
    # Create job record
    job = InspectionJob(
        status="pending",
        image_ref=request.image_data,  # In production, save to object storage first
        component_type=request.component_type,
        reference_id=request.reference_id,
        job_metadata=request.metadata or {},
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # Enqueue task
    try:
        celery_app.send_task(
            "batch_processing_service.tasks.process_inspection_image",
            args=[job.id],
        )
        logger.info(f"Enqueued inspection job {job.id} for processing")
    except Exception as e:
        logger.error(f"Failed to enqueue job {job.id}: {e}")
        job.status = "failed"
        job.error_message = f"Failed to enqueue: {str(e)}"
        db.commit()
        raise HTTPException(status_code=500, detail="Failed to enqueue job")
    
    return InspectionStatusResponse(
        job_id=job.id,
        status=job.status,
        created_at=job.created_at,
        completed_at=job.completed_at,
        result=None,
        error=job.error_message,
    )


@app.get("/inspections/{job_id}", response_model=InspectionStatusResponse)
def get_inspection_status(job_id: int, db: Session = Depends(get_db)):
    """
    Get status and results of an inspection job.
    
    Returns:
    - Job metadata (status, timestamps)
    - Full results if completed (all signals + decision)
    - Error message if failed
    """
    job = db.get(InspectionJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Fetch result if exists
    result_data = None
    if job.status == "completed":
        result = db.query(InspectionResult).filter(InspectionResult.job_id == job_id).first()
        if result:
            result_data = {
                "verdict": result.verdict,
                "confidence": result.confidence,
                "score": result.score,
                "ocr": result.ocr_result,
                "logo": result.logo_result,
                "visual_signature": result.visual_signature_result,
                "anomaly": result.anomaly_result,
                "decision_notes": result.decision_notes,
            }
    
    return InspectionStatusResponse(
        job_id=job.id,
        status=job.status,
        created_at=job.created_at,
        completed_at=job.completed_at,
        result=result_data,
        error=job.error_message,
    )


@app.get("/inspections")
def list_inspections(
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List inspection jobs with optional filtering.
    """
    query = db.query(InspectionJob)
    
    if status:
        query = query.filter(InspectionJob.status == status)
    
    query = query.order_by(InspectionJob.created_at.desc())
    total = query.count()
    jobs = query.offset(offset).limit(limit).all()
    
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "jobs": [
            {
                "id": job.id,
                "status": job.status,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            }
            for job in jobs
        ]
    }


# ============================================================================
# Live Inspection Endpoints
# ============================================================================

@app.post("/live/runs")
def create_live_run(
    camera_source: str,
    component_type: Optional[str] = None,
    reference_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Create a new live inspection run session.
    """
    run = LiveInspectionRun(
        camera_source=camera_source,
        status="active",
        component_type=component_type,
        reference_id=reference_id,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    
    return {
        "run_id": run.id,
        "status": run.status,
        "started_at": run.started_at.isoformat() if run.started_at else None,
    }


@app.post("/live/runs/{run_id}/frames")
def add_frame_result(
    run_id: int,
    frame_id: int,
    verdict: Optional[str] = None,
    confidence: Optional[float] = None,
    ocr_text: Optional[str] = None,
    logo_manufacturer: Optional[str] = None,
    analysis_data: Optional[dict] = None,
    db: Session = Depends(get_db)
):
    """
    Store analysis result for a single frame in live inspection.
    """
    # Verify run exists
    run = db.get(LiveInspectionRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    # Store frame result
    frame_result = LiveFrameResult(
        run_id=run_id,
        frame_id=frame_id,
        verdict=verdict,
        confidence=confidence,
        ocr_text=ocr_text,
        logo_manufacturer=logo_manufacturer,
        analysis_data=analysis_data or {},
    )
    db.add(frame_result)
    
    # Update run statistics
    run.frames_analyzed += 1
    if verdict == "pass":
        run.pass_count += 1
    elif verdict == "fail":
        run.fail_count += 1
    elif verdict == "needs_review":
        run.review_count += 1
    
    db.commit()
    
    return {"status": "stored", "frame_id": frame_id}


@app.post("/live/runs/{run_id}/complete")
def complete_live_run(
    run_id: int,
    total_frames: int,
    db: Session = Depends(get_db)
):
    """
    Mark a live inspection run as completed.
    """
    run = db.get(LiveInspectionRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    run.status = "completed"
    run.ended_at = func.now()
    run.total_frames = total_frames
    
    db.commit()
    
    return {
        "run_id": run.id,
        "status": run.status,
        "summary": {
            "total_frames": run.total_frames,
            "analyzed": run.frames_analyzed,
            "pass": run.pass_count,
            "fail": run.fail_count,
            "review": run.review_count,
        }
    }


@app.get("/live/runs")
def list_live_runs(
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List all live inspection runs with optional filtering.
    """
    query = db.query(LiveInspectionRun)
    
    if status:
        query = query.filter(LiveInspectionRun.status == status)
    
    query = query.order_by(LiveInspectionRun.started_at.desc())
    total = query.count()
    runs = query.offset(offset).limit(limit).all()
    
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "runs": [
            {
                "id": run.id,
                "camera_source": run.camera_source,
                "status": run.status,
                "started_at": run.started_at.isoformat() if run.started_at else None,
                "ended_at": run.ended_at.isoformat() if run.ended_at else None,
                "frames_analyzed": run.frames_analyzed,
                "pass_count": run.pass_count,
                "fail_count": run.fail_count,
                "review_count": run.review_count,
            }
            for run in runs
        ]
    }


@app.get("/live/runs/{run_id}")
def get_live_run(
    run_id: int,
    include_frames: bool = False,
    db: Session = Depends(get_db)
):
    """
    Get details of a specific live inspection run.
    """
    run = db.get(LiveInspectionRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    result = {
        "id": run.id,
        "camera_source": run.camera_source,
        "status": run.status,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "ended_at": run.ended_at.isoformat() if run.ended_at else None,
        "total_frames": run.total_frames,
        "frames_analyzed": run.frames_analyzed,
        "pass_count": run.pass_count,
        "fail_count": run.fail_count,
        "review_count": run.review_count,
    }
    
    if include_frames:
        frames = db.query(LiveFrameResult).filter(
            LiveFrameResult.run_id == run_id
        ).order_by(LiveFrameResult.frame_id).all()
        
        result["frames"] = [
            {
                "frame_id": frame.frame_id,
                "verdict": frame.verdict,
                "confidence": frame.confidence,
                "ocr_text": frame.ocr_text,
                "logo_manufacturer": frame.logo_manufacturer,
                "timestamp": frame.timestamp.isoformat() if frame.timestamp else None,
            }
            for frame in frames
        ]
    
    return result


# ============================================================================
# History Endpoints (Combined Batch + Live)
# ============================================================================

@app.get("/history")
def get_inspection_history(
    limit: int = 50,
    offset: int = 0,
    inspection_type: Optional[str] = None,  # "batch", "live", or None for all
    db: Session = Depends(get_db)
):
    """
    Get combined history of batch and live inspections.
    """
    history = []
    
    # Fetch batch inspections
    if not inspection_type or inspection_type == "batch":
        batch_jobs = db.query(InspectionJob).order_by(
            InspectionJob.created_at.desc()
        ).limit(limit).all()
        
        for job in batch_jobs:
            history.append({
                "type": "batch",
                "id": job.id,
                "status": job.status,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "component_type": job.component_type,
            })
    
    # Fetch live inspections
    if not inspection_type or inspection_type == "live":
        live_runs = db.query(LiveInspectionRun).order_by(
            LiveInspectionRun.started_at.desc()
        ).limit(limit).all()
        
        for run in live_runs:
            history.append({
                "type": "live",
                "id": run.id,
                "status": run.status,
                "started_at": run.started_at.isoformat() if run.started_at else None,
                "ended_at": run.ended_at.isoformat() if run.ended_at else None,
                "camera_source": run.camera_source,
                "frames_analyzed": run.frames_analyzed,
                "pass_count": run.pass_count,
                "fail_count": run.fail_count,
            })
    
    # Sort by date (most recent first)
    history.sort(key=lambda x: x.get("created_at") or x.get("started_at") or "", reverse=True)
    
    return {
        "total": len(history),
        "limit": limit,
        "offset": offset,
        "history": history[offset:offset + limit]
    }


# ============================================================================
# Debug Endpoints (kept for backward compatibility)
# ============================================================================

@app.post("/debug/jobs")
def create_job(db: Session = Depends(get_db)):
    job = InspectionJob(status="pending")
    db.add(job)
    db.commit()
    db.refresh(job)
    return {"id": job.id, "status": job.status}


@app.get("/debug/jobs/{job_id}")
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.get(InspectionJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"id": job.id, "status": job.status, "created_at": str(job.created_at)}
