# AOI-IC-identify

Automated Optical Inspection and Identification for integrated circuits. This repository provides a multi-service system supporting batch (asynchronous) and live (real-time) inspection pipelines, a minimal Next.js frontend, and a docker-compose development stack (PostgreSQL + Redis + services).

## Contents
- Overview
- Architecture
- Services
- Quick start (Docker Compose)
- Local development (non-container)
- Frontend
- Environment variables
- API/WS endpoints
- Testing
- Repository layout
- Troubleshooting
- Contributing
- License

---

## Overview
This project orchestrates an AI/vision multi-signal pipeline to analyze component images/streams and produce inspection decisions. It exposes REST APIs (and WebSockets for live mode), persists core data to PostgreSQL, and uses Celery/Redis for batch processing.

## Architecture
Two operational modes share core verification capabilities:

- Batch (asynchronous via Celery and Redis)
  - Flow: API Gateway accepts request → persist job metadata in PostgreSQL → enqueue task to Redis (Celery) → Batch Processing workers run the AI/vision pipeline → persist results and audit trail → expose results via API.

- Live (real-time via WebSockets)
  - Flow: Devices stream to Stream Ingestion service via WebSockets → frames pass through the AI/vision pipeline in near real-time → Decision Engine returns results over the open WebSocket → snapshots persisted as needed → audit trail maintained.

### Microservices and responsibilities
- API Gateway: Public entrypoint exposing REST endpoints; routes to internal services; coordinates batch job creation and result retrieval.
- Inspection Management: Manages inspections, components, runs, and metadata; persists to PostgreSQL; participates in audit trail.
- Batch Processing (Celery): Workers pull tasks from Redis; run the AI/vision pipeline on queued batches; write results.
- Stream Ingestion & Processing: WebSocket endpoints for live streams; performs real-time processing and returns immediate outcomes; snapshots persisted when required.
- Component Verification: OCR, logo identification, visual signature embedding, and anomaly checks used by batch and live paths.
- Decision Engine: Fuses multi-signal outputs and produces pass/fail/notes/confidence; writes outcomes.

### AI/vision multi-signal pipeline
- Preprocessing → ROI detection → OCR (Signal 1) → Logo ID (Signal 2) → Visual Signature embeddings (Signal 3) → Surface Anomaly via autoencoder (Signal 4) → Decision Engine (fusion)

### Data persistence
- PostgreSQL for core domain tables
- Live-mode snapshot persistence as needed
- Immutable audit trail via shadow tables + triggers

---

## Quick start (Docker Compose)
Prerequisites: Docker and docker-compose.

```bash
# Build all images
docker-compose build

# Start services in the background
docker-compose up -d

# See service status
docker-compose ps
```

Service URLs (after compose up):
- API Gateway: http://localhost:8003/health
- Inspection Service: http://localhost:8001/health, http://localhost:8001/db/health
- Stream Ingestion: http://localhost:8002/health, ws://localhost:8002/ws/live/analysis
- Decision Engine: http://localhost:8004/health
- Verification Service: http://localhost:8005/health

To stop everything:
```bash
docker-compose down
```

---

## Local development (non-container)
Run services directly for iterative development. Start each in its own terminal.

```bash
# API Gateway (port 8000 by default here; configure as needed)
uvicorn backend/api_gateway/main:app --host 0.0.0.0 --port 8000 --reload

# Inspection Service (8001)
uvicorn backend/inspection_service/main:app --host 0.0.0.0 --port 8001 --reload

# Stream Ingestion Service (8002)
uvicorn backend/stream_ingestion_service/main:app --host 0.0.0.0 --port 8002 --reload

# Decision Engine (8004)
uvicorn backend/decision_engine/main:app --host 0.0.0.0 --port 8004 --reload

# Verification Service (8005)
uvicorn backend/verification_service/main:app --host 0.0.0.0 --port 8005 --reload

# Celery worker for batch processing
celery -A backend.batch_processing_service.celery_app worker --loglevel=info
```

Ensure PostgreSQL and Redis are available (via Docker or local installs) and `DATABASE_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` are set (see Environment variables).

---

## Frontend
Local development:
```bash
cd frontend
npm install
npm run dev  # open http://localhost:3000
```
Ensure `NEXT_PUBLIC_API_URL` points to the API Gateway (e.g., http://localhost:8003 when using docker-compose, or your local API Gateway URL when running services directly).

---

## Environment variables
Configure these in your environment or a `.env` consumed by your tooling/docker-compose as appropriate:

- `DATABASE_URL`
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`
- `NEXAR_API_KEY`
- `NEXT_PUBLIC_API_URL`

Example (placeholder values; replace as appropriate):
```dotenv
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/aoi
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
NEXAR_API_KEY=YOUR_NEXAR_API_KEY
NEXT_PUBLIC_API_URL=http://localhost:8003
```

---

## API and WebSocket endpoints
Health endpoints (useful for smoke checks):
- API Gateway: `GET /health`
- Inspection Service: `GET /health`, `GET /db/health`
- Stream Ingestion: `GET /health`, WS: `ws://localhost:8002/ws/live/analysis`
- Decision Engine: `GET /health`
- Verification Service: `GET /health`

Depending on your routing, API Gateway may proxy requests to internal services.

---

## Testing
Backend tests:
```bash
pytest backend/tests -q
# or single file
pytest backend/tests/test_health_endpoints.py -q
# or single test
pytest backend/tests/test_health_endpoints.py::test_api_gateway_health -q
```

---

## Repository layout
```
backend/
  api_gateway/
  inspection_service/
  stream_ingestion_service/
  decision_engine/
  verification_service/
  batch_processing_service/
frontend/
docker-compose.yml
```

---

## Troubleshooting
- Services unhealthy in docker-compose: check environment variables and view logs with `docker-compose logs -f <service>`.
- DB connectivity: verify `DATABASE_URL` and that PostgreSQL container is running and reachable from services.
- Redis/Celery: ensure broker/result URLs match your Redis instance and that the Celery worker is running.
- CORS/frontend API calls: confirm `NEXT_PUBLIC_API_URL` and API CORS configuration.

---

## Contributing
- Open an issue or PR describing your change.
- Add/adjust tests where applicable.
- Keep changes scoped and documented in commit messages.

---

## License
TBD. Add your project’s license (e.g., MIT, Apache-2.0) to `LICENSE`.
