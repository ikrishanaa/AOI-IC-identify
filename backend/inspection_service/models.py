from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Float, Text
from sqlalchemy.sql import func

from shared.db import Base


class InspectionJob(Base):
    """Batch inspection job tracking."""
    __tablename__ = "inspection_jobs"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(String(32), nullable=False, default="pending")  # pending, processing, completed, failed
    image_ref = Column(String(512), nullable=True)  # Path or object storage reference
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
