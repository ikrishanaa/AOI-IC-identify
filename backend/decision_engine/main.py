from fastapi import FastAPI, HTTPException
from typing import Dict, List
import logging

from shared.models import DecisionRequest, DecisionResponse, SignalEvidence

logger = logging.getLogger(__name__)
app = FastAPI(title="Decision Engine Service", version="0.1.0")


# Default signal weights (can be overridden per request)
DEFAULT_WEIGHTS = {
    "ocr": 0.30,
    "logo": 0.25,
    "visual_signature": 0.25,
    "anomaly": 0.20,
}

# Default decision thresholds
DEFAULT_THRESHOLDS = {
    "pass_threshold": 0.80,  # Above this = pass
    "fail_threshold": 0.50,  # Below this = fail
    "anomaly_threshold": 0.30,  # Above this = anomalous (inverted for scoring)
}


@app.get("/health")
def health():
    return {"service": "decision_engine", "status": "ok"}


@app.post("/decide", response_model=DecisionResponse)
def decide(request: DecisionRequest) -> DecisionResponse:
    """
    Apply weighted rule-based decision logic to verification signals.
    
    Logic:
    - Each signal contributes a weighted score
    - Anomaly signal is inverted (low anomaly = high score)
    - Final score determines verdict: pass, fail, or needs_review
    """
    if not request.signals:
        raise HTTPException(status_code=400, detail="No signals provided")
    
    # Use custom thresholds or defaults
    thresholds = request.thresholds or DEFAULT_THRESHOLDS
    
    # Calculate weighted score
    signals_by_type: Dict[str, SignalEvidence] = {
        sig.signal_type: sig for sig in request.signals
    }
    
    weighted_score = 0.0
    total_weight = 0.0
    notes: List[str] = []
    
    for signal_type, weight in DEFAULT_WEIGHTS.items():
        signal = signals_by_type.get(signal_type)
        if not signal:
            continue
        
        # Get signal confidence
        confidence = signal.confidence
        
        # Special handling for anomaly (invert the score)
        if signal_type == "anomaly":
            # High anomaly score = bad, so invert for weighted calculation
            anomaly_score = signal.data.get("score", 0.0)
            if anomaly_score > thresholds.get("anomaly_threshold", 0.30):
                notes.append(f"Anomaly detected (score: {anomaly_score:.2f})")
                confidence = 1.0 - anomaly_score  # Invert
            else:
                notes.append(f"No anomaly detected (score: {anomaly_score:.2f})")
        
        weighted_score += confidence * weight
        total_weight += weight
        
        # Add notes for each signal
        if signal_type == "ocr":
            text = signal.data.get("text", "")
            notes.append(f"OCR: '{text}' (conf: {signal.confidence:.2f})")
        elif signal_type == "logo":
            mfr = signal.data.get("manufacturer", "unknown")
            notes.append(f"Logo: {mfr} (conf: {signal.confidence:.2f})")
        elif signal_type == "visual_signature":
            sim = signal.data.get("similarity", 0.0)
            notes.append(f"Visual similarity: {sim:.2f}")
    
    # Normalize score by total weight
    if total_weight > 0:
        final_score = weighted_score / total_weight
    else:
        final_score = 0.0
    
    # Determine verdict based on thresholds
    pass_threshold = thresholds.get("pass_threshold", 0.80)
    fail_threshold = thresholds.get("fail_threshold", 0.50)
    
    if final_score >= pass_threshold:
        verdict = "pass"
        confidence = final_score
        notes.append(f"Score {final_score:.2f} >= {pass_threshold:.2f} → PASS")
    elif final_score < fail_threshold:
        verdict = "fail"
        confidence = 1.0 - final_score  # High confidence in failure
        notes.append(f"Score {final_score:.2f} < {fail_threshold:.2f} → FAIL")
    else:
        verdict = "needs_review"
        confidence = 0.5  # Medium confidence when in grey zone
        notes.append(f"Score {final_score:.2f} in review zone → NEEDS REVIEW")
    
    logger.info(
        f"Decision: verdict={verdict}, score={final_score:.2f}, signals={len(request.signals)}"
    )
    
    return DecisionResponse(
        verdict=verdict,
        confidence=confidence,
        score=final_score,
        notes=notes,
        signal_weights=DEFAULT_WEIGHTS,
    )
