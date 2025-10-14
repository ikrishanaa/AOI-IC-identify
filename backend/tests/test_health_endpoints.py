from fastapi.testclient import TestClient

from api_gateway.main import app as api_gateway_app
from inspection_service.main import app as inspection_service_app
from decision_engine.main import app as decision_engine_app
from verification_service.main import app as verification_service_app
from stream_ingestion_service.main import app as stream_ingestion_app


def test_api_gateway_health():
    client = TestClient(api_gateway_app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json().get("service") == "api_gateway"


def test_inspection_service_health():
    client = TestClient(inspection_service_app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json().get("service") == "inspection_service"


def test_decision_engine_health():
    client = TestClient(decision_engine_app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json().get("service") == "decision_engine"


def test_verification_service_health():
    client = TestClient(verification_service_app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json().get("service") == "verification_service"


def test_stream_ingestion_service_health():
    client = TestClient(stream_ingestion_app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json().get("service") == "stream_ingestion_service"