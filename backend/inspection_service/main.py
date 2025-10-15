from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from shared.db import Base, engine, check_connection, get_db
from .models import InspectionJob

app = FastAPI(title="Inspection Management Service", version="0.1.0")


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
