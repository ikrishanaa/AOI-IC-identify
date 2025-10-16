# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

Repository status
- Implemented scaffolding exists for backend services (FastAPI + Celery), a minimal Next.js frontend, and a docker-compose dev stack (Postgres + Redis + services).

Commonly used commands
Container workflow (dev)
- docker-compose build
- docker-compose up -d
- docker-compose ps

Service URLs (after compose up)
- API Gateway: http://localhost:8003/health
- Inspection Service: http://localhost:8001/health, http://localhost:8001/db/health
- Stream Ingestion: http://localhost:8002/health, ws://localhost:8002/ws/live/analysis
- Decision Engine: http://localhost:8004/health
- Verification Service: http://localhost:8005/health

Frontend (local dev)
- cd frontend && npm install
- npm run dev  (open http://localhost:3000)

Run backend services locally (non-container)
- uvicorn backend/api_gateway/main:app --host 0.0.0.0 --port 8000 --reload
- uvicorn backend/inspection_service/main:app --host 0.0.0.0 --port 8001 --reload
- uvicorn backend/stream_ingestion_service/main:app --host 0.0.0.0 --port 8002 --reload
- uvicorn backend/decision_engine/main:app --host 0.0.0.0 --port 8004 --reload
- uvicorn backend/verification_service/main:app --host 0.0.0.0 --port 8005 --reload
- celery -A backend.batch_processing_service.celery_app worker --loglevel=info

Testing
- pytest backend/tests -q
- pytest backend/tests/test_health_endpoints.py -q
- pytest backend/tests/test_health_endpoints.py::test_api_gateway_health -q  (single test)

Environment variables
- DATABASE_URL
- CELERY_BROKER_URL
- CELERY_RESULT_BACKEND
- NEXAR_API_KEY
- NEXT_PUBLIC_API_URL

High-level architecture and structure
Operational modes
- Batch (asynchronous via Celery and Redis)
  - Flow: API Gateway accepts request → persist job metadata in PostgreSQL → enqueue task to Redis (Celery) → Batch Processing service executes AI/vision pipeline → persist results and audit trail → expose results via API.
- Live (real-time via WebSockets)
  - Flow: Devices stream to Stream Ingestion service via WebSockets → frames pass through AI/vision pipeline in near real-time → Decision Engine returns results over the open WebSocket → snapshot data persisted as needed → audit trail maintained.

Microservices and responsibilities
- API Gateway: Public entrypoint exposing REST endpoints; routes to internal services; coordinates batch job creation and result retrieval.
- Inspection Management: Manages inspections, components, runs, and metadata; persists to PostgreSQL; participates in audit trail.
- Batch Processing (Celery): Celery workers pull tasks from Redis; run the AI/vision pipeline on queued batches; write results.
- Stream Ingestion & Processing: WebSocket endpoints for live streams; performs real-time processing and returns immediate outcomes; snapshots persisted when required.
- Component Verification: Provides OCR, logo identification, visual signature embedding, and anomaly checks as callable routines used by batch and live paths.
- Decision Engine: Fuses multi-signal outputs and produces pass/fail/notes/confidence; writes outcomes.

AI/vision multi-signal pipeline
- Preprocessing → ROI detection → OCR (Signal 1) → Logo ID (Signal 2) → Visual Signature embeddings (Signal 3) → Surface Anomaly via autoencoder (Signal 4) → Decision Engine (fusion)

Data persistence strategy
- PostgreSQL for core domain tables.
- Live-mode snapshot persistence for real-time context.
- Immutable audit trail via shadow tables plus triggers.

Project layout (high-level)
- Top-level areas: backend and frontend, plus docker-compose.yml for dev orchestration.

Containerization footprint
- docker-compose defines postgres, redis, and services: api_gateway (8003), inspection_service (8001), stream_ingestion_service (8002), decision_engine (8004), verification_service (8005), and a batch_worker (Celery).
