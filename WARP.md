# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

Repository status
- This repository currently contains architectural blueprints only. There is no implemented code, no README.md, no tests, and no existing WARP.md at the time of writing.

Commonly used commands
Container workflow
- docker compose build
- docker compose up -d

Run backend services locally (non-container)
- uvicorn inspection_service.main:app --host 0.0.0.0 --port 8000 --reload
- uvicorn stream_ingestion_service.main:app --host 0.0.0.0 --port 8000 --reload
- celery -A batch_processing_service.celery_app worker --loglevel=info

Testing (as proposed by the blueprint)
- pytest backend/tests -q
- pytest backend/tests/test_batch_processing_service.py -q
- pytest path/to/test_file.py::TestClass::test_func -q

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

Proposed project layout
- Top-level areas: backend and frontend, with shared modules leveraged by multiple services.

Containerization footprint
- docker-compose defines services for: db (PostgreSQL), redis, inspection_service, batch_worker (Celery), stream_ingestion_service, and frontend.

Repository notes
- There is currently no README.md or rule files present in this repository. This WARP.md reflects blueprint guidance only.