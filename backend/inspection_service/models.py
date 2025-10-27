from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Float, Text
from sqlalchemy.sql import func

from shared.db import Base


class InspectionJob(Base):
    """Batch inspection job tracking."""
    __tablename__ = "inspection_jobs"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(String(32), nullable=False, default="pending")  # pending, processing, completed, failed
    image_ref = Column(Text, nullable=True)  # Path or object storage reference (can be large base64)
    component_type = Column(String(128), nullable=True)
    reference_id = Column(String(128), nullable=True)
    job_metadata = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)


class InspectionResult(Base):
    """Detailed inspection results with all verification signals."""
    __tablename__ = "inspection_results"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("inspection_jobs.id"), nullable=False, unique=True)
    
    # Final decision
    verdict = Column(String(32), nullable=True)  # pass, fail, needs_review
    confidence = Column(Float, nullable=True)
    score = Column(Float, nullable=True)
    
    # Verification signals (stored as JSON)
    ocr_result = Column(JSON, nullable=True)
    logo_result = Column(JSON, nullable=True)
    visual_signature_result = Column(JSON, nullable=True)
    anomaly_result = Column(JSON, nullable=True)
    
    # Decision notes
    decision_notes = Column(JSON, nullable=True)  # Array of strings
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ReferenceComponent(Base):
    """Reference/golden sample components for comparison."""
    __tablename__ = "reference_components"

    id = Column(Integer, primary_key=True, index=True)
    component_id = Column(String(128), nullable=False, unique=True, index=True)
    manufacturer = Column(String(128), nullable=True)
    part_number = Column(String(128), nullable=True)
    component_type = Column(String(128), nullable=True)
    
    # Golden sample data
    reference_text = Column(String(512), nullable=True)
    reference_logo = Column(String(128), nullable=True)
    visual_embedding = Column(JSON, nullable=True)  # Feature vector
    
    component_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class LiveInspectionRun(Base):
    """Live inspection session tracking."""
    __tablename__ = "live_inspection_runs"

    id = Column(Integer, primary_key=True, index=True)
    camera_source = Column(String(256), nullable=True)
    status = Column(String(32), nullable=False, default="active")  # active, completed, aborted
    component_type = Column(String(128), nullable=True)
    reference_id = Column(String(128), nullable=True)
    run_metadata = Column(JSON, nullable=True)
    
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)
    
    # Summary statistics
    total_frames = Column(Integer, default=0)
    frames_analyzed = Column(Integer, default=0)
    pass_count = Column(Integer, default=0)
    fail_count = Column(Integer, default=0)
    review_count = Column(Integer, default=0)


class LiveFrameResult(Base):
    """Individual frame analysis results from live inspection."""
    __tablename__ = "live_frame_results"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("live_inspection_runs.id"), nullable=False, index=True)
    frame_id = Column(Integer, nullable=False)
    
    # Frame analysis
    verdict = Column(String(32), nullable=True)  # pass, fail, needs_review
    confidence = Column(Float, nullable=True)
    
    # Verification signals
    ocr_text = Column(String(512), nullable=True)
    logo_manufacturer = Column(String(128), nullable=True)
    analysis_data = Column(JSON, nullable=True)  # Full analysis details
    
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
