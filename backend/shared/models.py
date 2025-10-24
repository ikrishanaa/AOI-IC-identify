"""Shared Pydantic models for API contracts across services."""
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


# ============================================================================
# Verification Service Models
# ============================================================================

class OCRResult(BaseModel):
    """Result from OCR analysis."""
    text: str = Field(..., description="Extracted text from image")
    confidence: float = Field(..., ge=0.0, le=1.0, description="OCR confidence score")
    bounding_box: Optional[dict[str, int]] = Field(None, description="Text region coordinates")


class LogoResult(BaseModel):
    """Result from logo identification."""
    manufacturer: str = Field(..., description="Identified manufacturer name")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Logo identification confidence")
    bounding_box: Optional[dict[str, int]] = Field(None, description="Logo region coordinates")


class VisualSignatureResult(BaseModel):
    """Result from visual signature analysis."""
    similarity: float = Field(..., ge=0.0, le=1.0, description="Similarity to reference embeddings")
    reference_id: Optional[str] = Field(None, description="ID of matched reference component")
    embedding: Optional[list[float]] = Field(None, description="Feature embedding vector")


class AnomalyResult(BaseModel):
    """Result from surface anomaly detection."""
    score: float = Field(..., ge=0.0, le=1.0, description="Anomaly score (higher = more anomalous)")
    is_anomalous: bool = Field(..., description="Whether component is flagged as anomalous")
    reconstruction_error: Optional[float] = Field(None, description="Autoencoder reconstruction error")


class VerificationRequest(BaseModel):
    """Request for component verification."""
    image_data: str = Field(..., description="Base64 encoded image or image reference")
    verification_types: list[str] = Field(
        default=["ocr", "logo", "visual_signature", "anomaly"],
        description="Types of verification to perform"
    )


class VerificationResponse(BaseModel):
    """Combined verification results."""
    ocr: Optional[OCRResult] = None
    logo: Optional[LogoResult] = None
    visual_signature: Optional[VisualSignatureResult] = None
    anomaly: Optional[AnomalyResult] = None
    processing_time_ms: Optional[float] = None


# ============================================================================
# Decision Engine Models
# ============================================================================

class SignalEvidence(BaseModel):
    """Evidence from a single verification signal."""
    signal_type: str = Field(..., description="Type of signal (ocr, logo, visual, anomaly)")
    confidence: float = Field(..., ge=0.0, le=1.0)
    data: dict[str, Any] = Field(default_factory=dict)


class DecisionRequest(BaseModel):
    """Request for decision making."""
    signals: list[SignalEvidence] = Field(..., description="All verification signals")
    reference_data: Optional[dict[str, Any]] = Field(None, description="Expected component data")
    thresholds: Optional[dict[str, float]] = Field(None, description="Custom decision thresholds")


class DecisionResponse(BaseModel):
    """Decision engine verdict."""
    verdict: str = Field(..., description="Decision: pass, fail, or needs_review")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence in decision")
    score: float = Field(..., ge=0.0, le=1.0, description="Weighted aggregate score")
    notes: list[str] = Field(default_factory=list, description="Decision reasoning notes")
    signal_weights: Optional[dict[str, float]] = Field(None, description="Weights applied to signals")


# ============================================================================
# Inspection Service Models
# ============================================================================

class InspectionCreateRequest(BaseModel):
    """Request to create a new inspection job."""
    image_data: str = Field(..., description="Base64 encoded image")
    component_type: Optional[str] = Field(None, description="Expected component type/family")
    reference_id: Optional[str] = Field(None, description="Reference component ID for comparison")
    metadata: Optional[dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class InspectionStatusResponse(BaseModel):
    """Response for inspection job status."""
    job_id: int
    status: str = Field(..., description="Status: pending, processing, completed, failed")
    created_at: datetime
    completed_at: Optional[datetime] = None
    result: Optional[dict[str, Any]] = None
    error: Optional[str] = None


class InspectionResult(BaseModel):
    """Detailed inspection result."""
    job_id: int
    status: str
    verdict: Optional[str] = None
    confidence: Optional[float] = None
    score: Optional[float] = None
    
    # All verification signals
    ocr: Optional[OCRResult] = None
    logo: Optional[LogoResult] = None
    visual_signature: Optional[VisualSignatureResult] = None
    anomaly: Optional[AnomalyResult] = None
    
    # Decision details
    decision_notes: list[str] = Field(default_factory=list)
    
    created_at: datetime
    completed_at: Optional[datetime] = None


# ============================================================================
# Stream Ingestion Models
# ============================================================================

class LiveFrameAnalysis(BaseModel):
    """Real-time analysis result for a single frame."""
    frame_id: int
    timestamp: float
    verdict: Optional[str] = None
    confidence: Optional[float] = None
    
    # Quick results (not all signals may be available in real-time)
    ocr_text: Optional[str] = None
    logo_manufacturer: Optional[str] = None
    
    bounding_boxes: list[dict[str, Any]] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class CaptureRequest(BaseModel):
    """Request to capture and persist current frame."""
    save_to_db: bool = Field(default=True, description="Whether to persist to database")
    metadata: Optional[dict[str, Any]] = Field(default_factory=dict)


# ============================================================================
# Common Models
# ============================================================================

class HealthResponse(BaseModel):
    """Health check response."""
    service: str
    status: str
    version: Optional[str] = None
    timestamp: Optional[datetime] = None
