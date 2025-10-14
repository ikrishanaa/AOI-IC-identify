import logging
from typing import Any

from .celery_app import app


logger = logging.getLogger(__name__)


@app.task
def add(x: int, y: int) -> int:
    return x + y


@app.task
def process_inspection_image(image_ref: str) -> dict[str, Any]:
    """Stubbed processing task; replace with real pipeline later.

    Args:
        image_ref: Path or object storage reference to the image
    Returns:
        Dict with mocked signals and verdict placeholder
    """
    logger.info("Processing image (stub): %s", image_ref)
    result = {
        "ocr": {"text": "ABC123", "confidence": 0.9},
        "logo": {"manufacturer": "ExampleCorp", "confidence": 0.85},
        "visual_signature": {"similarity": 0.8},
        "surface_anomaly": {"score": 0.1},
        "verdict": {"decision": "undetermined", "confidence": 0.0},
    }
    return result
