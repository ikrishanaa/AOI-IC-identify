# MILESTONES.md

This plan breaks down the AOI IC Marking blueprint into high-level milestones with scope, dependencies, and success criteria. The goal is to deliver an MVP first (batch image analysis with OCR + Logo ID + simple rules), then evolve to the long-term architecture.

Milestone 0: Repo bootstrap and governance
- Scope: Establish repository structure (backend/, frontend/), common docs, env templates. Decide Python/Node versions, test/lint runners.
- Dependencies: None
- Done when: The repo contains standard folders, .env.example, and common docs (WARP.md, MILESTONES.md, PROGRESS.md).

Milestone 1: Backend platform foundation (FastAPI microservices)
- Scope: Shared config and logging; service skeletons with /health; packaging (requirements.txt); basic tests. Services: api_gateway, inspection_service, decision_engine, verification_service, stream_ingestion_service (stub).
- Dependencies: M0
- Done when: All services run locally via uvicorn; /health returns 200; pytest of health checks passes.

Milestone 2: Task queue foundation (Celery + Redis)
- Scope: Celery app, worker container, and basic tasks (ping/add). Wire inspection_service to publish a placeholder task.
- Dependencies: M1
- Done when: A task can be queued and consumed by a local worker; logs prove execution.

Milestone 3: Database schema and persistence (PostgreSQL)
- Scope: Choose SQLAlchemy/SQLModel; define minimal tables (inspection_jobs, inspection_results); connection management; migrations (Alembic) optional for MVP.
- Dependencies: M1
- Done when: Service can connect to DB and create/read a simple entity; migration scaffold exists (optional for MVP).

Milestone 4: Batch pipeline MVP (two signals)
- Scope: Define process_inspection_image task skeleton; integrate OCR and Logo ID placeholders; route: POST /inspections to create a job and enqueue; GET /inspections/{id} for status and result (mocked).
- Dependencies: M2, M3
- Done when: End-to-end "image in, mocked verdict out" works over async queue with persisted metadata.

Milestone 5: Decision Engine v0 (rule-based)
- Scope: Expose /decide accepting signals; implement simple weighted rules with thresholds; return pass/fail and confidence.
- Dependencies: M1
- Done when: Unit tests cover decision rules; API returns reproducible verdicts for sample payloads.

Milestone 6: Component Verification v0
- Scope: Expose /verify endpoints for OCR and logo checks using stubbed/local logic; add Nexar API client placeholder with environment variable and simple cache interface.
- Dependencies: M1
- Done when: Endpoint responds with deterministic stub data; integration points documented for future real calls.

Milestone 7: Live stream skeleton (WebSocket + MJPEG)
- Scope: WebSocket endpoint /ws/live/analysis (sends synthetic frames/JSON); HTTP /live/feed (stub StreamingResponse). No OpenCV dependency yet.
- Dependencies: M1
- Done when: Frontend can connect to WS and receive mock analysis; feed endpoint responds 501 or simple stream.

Milestone 8: Frontend MVP (Next.js)
- Scope: Scaffold app; pages: dashboard (list jobs mocked), new inspection (upload form stub), job status (poll stub), live view (connects WS). Minimal styling.
- Dependencies: M1, M4, M7
- Done when: Dev server runs; can navigate pages; WS connects and displays mock messages.

Milestone 9: Containerized dev environment (Docker Compose)
- Scope: Dockerfile for backend; docker-compose with postgres, redis, services; environment wiring; volumes for live reload.
- Dependencies: M1, M2, M3
- Done when: `docker compose up -d` boots infra and services and health checks succeed.

Milestone 10: Testing and CI
- Scope: Pytest for services and queue flows; minimal e2e smoke; optional GitHub Actions workflow.
- Dependencies: M1-M4
- Done when: `pytest` passes locally; CI runs tests on push.

Milestone 11: Data audit trail (shadow tables + triggers)
- Scope: Design audit trail for persisted entities; implement DB triggers; document audit read patterns.
- Dependencies: M3
- Done when: Mutations create immutable audit records; tests verify invariants.

Milestone 12: Observability and hardening
- Scope: Structured logging, basic metrics, health/readiness separation; config secrets via env; rate limits at gateway (future).
- Dependencies: M1, M9
- Done when: Logs and metrics visible locally; readiness probes distinguish startup from liveness.

Notes
- Focus on MVP flow first (Milestones 1–4, 9, 10). Live mode (7) can proceed in parallel once foundations are stable.
- Replace stubbed logic with real OCR/Logo/Nexar only after MVP is functional.