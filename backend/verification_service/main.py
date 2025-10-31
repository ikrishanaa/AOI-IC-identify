from fastapi import FastAPI, HTTPException
import random
import logging
import time
import hashlib
import base64

from shared.models import (
    VerificationRequest,
    VerificationResponse,
    OCRResult,
    LogoResult,
    VisualSignatureResult,
    AnomalyResult,
)

logger = logging.getLogger(__name__)
app = FastAPI(title="Component Verification Service", version="0.1.0")


# Mock data for demonstration (will be replaced with real AI models)
MOCK_MANUFACTURERS = ["Texas Instruments", "Intel", "STMicroelectronics", "NXP", "Analog Devices"]
MOCK_PART_NUMBERS = ["TI-LM358", "ATMEGA328P", "STM32F103", "LPC1768", "AD8232"]


@app.get("/health")
def health():
    return {"service": "verification_service", "status": "ok"}


@app.post("/verify", response_model=VerificationResponse)
def verify_component(request: VerificationRequest) -> VerificationResponse:
    """
    Perform multi-signal verification on component image.
    
    For MVP, this returns mock/deterministic results.
    In production, this would call:
    - Tesseract OCR
    - Logo detection CNN or cloud API
    - ResNet feature extraction + similarity
    - Autoencoder anomaly detection
    """
    start_time = time.time()
    
    verification_types = request.verification_types
    response = VerificationResponse()
    
    # OCR Signal
    if "ocr" in verification_types:
        response.ocr = perform_ocr_mock(request.image_data)
    
    # Logo Identification Signal
    if "logo" in verification_types:
        response.logo = perform_logo_detection_mock(request.image_data)
    
    # Visual Signature Signal
    if "visual_signature" in verification_types:
        response.visual_signature = perform_visual_signature_mock(request.image_data)
    
    # Anomaly Detection Signal
    if "anomaly" in verification_types:
        response.anomaly = perform_anomaly_detection_mock(request.image_data)
    
    processing_time = (time.time() - start_time) * 1000
    response.processing_time_ms = processing_time
    
    logger.info(f"Verification completed in {processing_time:.2f}ms")
    return response


def _content_bytes(image_data: str) -> bytes:
    """Extract raw bytes from possible data URL or plain base64 string; fallback to utf-8 bytes."""
    try:
        if image_data.startswith("data:") and "," in image_data:
            b64 = image_data.split(",", 1)[1]
            return base64.b64decode(b64, validate=False)
        # try base64 decode directly
        return base64.b64decode(image_data, validate=False)
    except Exception:
        return image_data.encode("utf-8", errors="ignore")


def _stable_index(payload: str, n: int) -> int:
    """Stable index in [0,n) based on SHA-256 of content bytes."""
    b = _content_bytes(payload)
    h = hashlib.sha256(b).digest()
    return int.from_bytes(h[:4], "big") % n if n > 0 else 0

def perform_ocr_mock(image_data: str) -> OCRResult:
    """
    Mock OCR using Tesseract.
    
    In production:
    - Decode base64 image
    - Preprocess (deskew, CLAHE, binarization)
    - Detect text ROI with EAST detector
    - Run Tesseract OCR on ROI
    """
    # Deterministic but content-sensitive mock
    idx = _stable_index(image_data, len(MOCK_PART_NUMBERS))
    text = MOCK_PART_NUMBERS[idx]
    
    # Simulate realistic confidence (0.75-0.95)
    confidence = 0.75 + (idx / max(1, len(MOCK_PART_NUMBERS)-1)) * 0.20
    
    return OCRResult(
        text=text,
        confidence=confidence,
        bounding_box={"x": 120, "y": 80, "width": 200, "height": 40}
    )


def perform_logo_detection_mock(image_data: str) -> LogoResult:
    """
    Mock logo identification.
    
    In production:
    - Detect logo ROI
    - Send to Google Cloud Vision API or AWS Rekognition
    - OR run custom CNN trained on manufacturer logos
    """
    idx = _stable_index(image_data, len(MOCK_MANUFACTURERS))
    manufacturer = MOCK_MANUFACTURERS[idx]
    
    # Simulate realistic confidence (0.70-0.95)
    confidence = 0.70 + (idx / max(1, len(MOCK_MANUFACTURERS)-1)) * 0.25
    
    return LogoResult(
        manufacturer=manufacturer,
        confidence=confidence,
        bounding_box={"x": 50, "y": 20, "width": 100, "height": 50}
    )


def perform_visual_signature_mock(image_data: str) -> VisualSignatureResult:
    """
    Mock visual signature embedding comparison.
    
    In production:
    - Extract features using pre-trained ResNet
    - Generate embedding vector
    - Compare with golden sample embeddings using cosine similarity
    """
    b = _content_bytes(image_data)
    # Simulate realistic similarity (0.65-0.90) based on content bytes
    h = hashlib.sha256(b).digest()
    similarity = 0.65 + (h[0] / 255.0) * 0.25
    
    # Mock embedding (128-dim vector) seeded for determinism per content
    seed = int.from_bytes(h[:4], "big")
    rnd = random.Random(seed)
    embedding = [rnd.random() for _ in range(128)]
    
    return VisualSignatureResult(
        similarity=similarity,
        reference_id="REF-001",
        embedding=embedding
    )


def perform_anomaly_detection_mock(image_data: str) -> AnomalyResult:
    """
    Mock surface anomaly detection using autoencoder.
    
    In production:
    - Train autoencoder on genuine component images
    - Calculate reconstruction error on input
    - High error = anomaly (tampered/fake)
    """
    # Simulate realistic anomaly scores (mostly low 0.05-0.20, occasionally high 0.30-0.60)
    b = _content_bytes(image_data)
    h = hashlib.sha256(b).digest()
    # Use first byte to decide anomaly roughly ~1/7 chance
    is_anomalous = (h[0] % 7) == 0
    if is_anomalous:
        score = 0.30 + (h[1] / 255.0) * 0.30  # 0.30-0.60
    else:
        score = 0.05 + (h[2] / 255.0) * 0.15  # 0.05-0.20
    
    return AnomalyResult(
        score=score,
        is_anomalous=is_anomalous,
        reconstruction_error=score * 10  # Scaled for display
    )


@app.post("/verify/ocr", response_model=OCRResult)
def verify_ocr_only(request: VerificationRequest) -> OCRResult:
    """Perform OCR only."""
    return perform_ocr_mock(request.image_data)


@app.post("/verify/logo", response_model=LogoResult)
def verify_logo_only(request: VerificationRequest) -> LogoResult:
    """Perform logo detection only."""
    return perform_logo_detection_mock(request.image_data)


@app.post("/verify/visual_signature", response_model=VisualSignatureResult)
def verify_visual_signature_only(request: VerificationRequest) -> VisualSignatureResult:
    """Perform visual signature analysis only."""
    return perform_visual_signature_mock(request.image_data)


@app.post("/verify/anomaly", response_model=AnomalyResult)
def verify_anomaly_only(request: VerificationRequest) -> AnomalyResult:
    """Perform anomaly detection only."""
    return perform_anomaly_detection_mock(request.image_data)
