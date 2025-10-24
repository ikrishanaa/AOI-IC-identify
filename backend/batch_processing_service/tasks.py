import logging
from typing import Any
from datetime import datetime
import httpx

from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .celery_app import app
from shared.config import get_settings
from shared.models import (
    VerificationRequest,
    DecisionRequest,
    SignalEvidence,
)
from inspection_service.models import InspectionJob, InspectionResult


logger = logging.getLogger(__name__)

# Service URLs (in containerized env, use service names)
settings = get_settings()
VERIFICATION_SERVICE_URL = "http://verification_service:8000"
DECISION_ENGINE_URL = "http://decision_engine:8000"

# DB session for workers
engine = create_engine(settings.database_url, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@app.task
def add(x: int, y: int) -> int:
    return x + y


@app.task
def process_inspection_image(job_id: int) -> dict[str, Any]:
    """
    Execute full multi-signal verification pipeline for a batch inspection job.

    Steps:
    1. Fetch job from database
    2. Call Verification Service to get all signals
    3. Call Decision Engine to fuse signals into verdict
    4. Persist results to database
    5. Update job status

    Args:
        job_id: Database ID of the inspection job
    Returns:
        Dict with complete inspection results
    """
    logger.info(f"Processing inspection job {job_id}")
    
    db = SessionLocal()
    try:
        # 1. Fetch job
        job = db.get(InspectionJob, job_id)
        if not job:
            logger.error(f"Job {job_id} not found")
            return {"error": "Job not found"}
        
        # Update status to processing
        job.status = "processing"
        db.commit()
        
        # 2. Call Verification Service
        logger.info(f"Calling verification service for job {job_id}")
        verification_response = call_verification_service(job.image_ref or "")
        
        if not verification_response:
            job.status = "failed"
            job.error_message = "Verification service failed"
            db.commit()
            return {"error": "Verification failed"}
        
        # 3. Prepare signals for Decision Engine
        signals = []
        
        if verification_response.get("ocr"):
            signals.append(
                SignalEvidence(
                    signal_type="ocr",
                    confidence=verification_response["ocr"]["confidence"],
                    data=verification_response["ocr"]
                )
            )
        
        if verification_response.get("logo"):
            signals.append(
                SignalEvidence(
                    signal_type="logo",
                    confidence=verification_response["logo"]["confidence"],
                    data=verification_response["logo"]
                )
            )
        
        if verification_response.get("visual_signature"):
            signals.append(
                SignalEvidence(
                    signal_type="visual_signature",
                    confidence=verification_response["visual_signature"]["similarity"],
                    data=verification_response["visual_signature"]
                )
            )
        
        if verification_response.get("anomaly"):
            signals.append(
                SignalEvidence(
                    signal_type="anomaly",
                    confidence=1.0 - verification_response["anomaly"]["score"],  # Invert for signal
                    data=verification_response["anomaly"]
                )
            )
        
        # 4. Call Decision Engine
        logger.info(f"Calling decision engine for job {job_id} with {len(signals)} signals")
        decision_response = call_decision_engine(signals)
        
        if not decision_response:
            job.status = "failed"
            job.error_message = "Decision engine failed"
            db.commit()
            return {"error": "Decision failed"}
        
        # 5. Persist results
        result = InspectionResult(
            job_id=job_id,
            verdict=decision_response["verdict"],
            confidence=decision_response["confidence"],
            score=decision_response["score"],
            ocr_result=verification_response.get("ocr"),
            logo_result=verification_response.get("logo"),
            visual_signature_result=verification_response.get("visual_signature"),
            anomaly_result=verification_response.get("anomaly"),
            decision_notes=decision_response.get("notes", []),
        )
        db.add(result)
        
        # Update job status
        job.status = "completed"
        job.completed_at = datetime.utcnow()
        db.commit()
        
        logger.info(
            f"Job {job_id} completed: verdict={decision_response['verdict']}, "
            f"score={decision_response['score']:.2f}"
        )
        
        return {
            "job_id": job_id,
            "verdict": decision_response["verdict"],
            "confidence": decision_response["confidence"],
            "score": decision_response["score"],
        }
        
    except Exception as e:
        logger.exception(f"Error processing job {job_id}: {e}")
        if job:
            job.status = "failed"
            job.error_message = str(e)
            db.commit()
        return {"error": str(e)}
    finally:
        db.close()


def call_verification_service(image_ref: str) -> dict[str, Any] | None:
    """Call verification service to get all signals."""
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{VERIFICATION_SERVICE_URL}/verify",
                json={
                    "image_data": image_ref,
                    "verification_types": ["ocr", "logo", "visual_signature", "anomaly"]
                }
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Verification service error: {e}")
        return None


def call_decision_engine(signals: list[SignalEvidence]) -> dict[str, Any] | None:
    """Call decision engine to fuse signals into verdict."""
    try:
        with httpx.Client(timeout=10.0) as client:
            # Convert Pydantic models to dict for JSON serialization
            signals_data = [s.model_dump() for s in signals]
            response = client.post(
                f"{DECISION_ENGINE_URL}/decide",
                json={"signals": signals_data}
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Decision engine error: {e}")
        return None
