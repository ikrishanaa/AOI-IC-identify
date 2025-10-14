# PROGRESS.md

A running progress tracker for the AOI IC Marking project. Update this as milestones move forward.

Status legend: NOT STARTED | IN PROGRESS | DONE

Summary
- Current focus: Foundations (backend services, queue, compose) and scaffolding the frontend.

Milestone status
- M0 Repo bootstrap and governance: DONE
- M1 Backend platform foundation (FastAPI microservices): DONE
- M2 Task queue foundation (Celery + Redis): DONE (stub tasks wired)
- M3 Database schema and persistence (PostgreSQL): NOT STARTED
- M4 Batch pipeline MVP (two signals): NOT STARTED
- M5 Decision Engine v0 (rule-based): NOT STARTED
- M6 Component Verification v0: NOT STARTED
- M7 Live stream skeleton (WebSocket + MJPEG): DONE (WS and feed stub)
- M8 Frontend MVP (Next.js): DONE (minimal scaffold)
- M9 Containerized dev environment (Docker Compose): DONE
- M10 Testing and CI: IN PROGRESS (service health tests added)
- M11 Data audit trail (shadow tables + triggers): NOT STARTED
- M12 Observability and hardening: NOT STARTED

Next actions
- M3: Introduce SQLAlchemy models for inspection_jobs/results and wire a simple DB check route.
- M4: Implement POST /inspections (enqueue process_inspection_image) and GET status (mocked storage).
- M5: Implement /decide with basic weighted rules and unit tests.

Changelog
- 2025-10-14: Initial scaffolding created (backend services, Celery, tests, Dockerfile, docker-compose, Next.js minimal app).