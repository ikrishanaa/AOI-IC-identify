from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from celery import Celery
import logging
from typing import Optional

from shared.db import Base, engine, check_connection, get_db
from shared.config import get_settings
from shared.models import InspectionCreateRequest, InspectionStatusResponse
from .models import InspectionJob, InspectionResult

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
