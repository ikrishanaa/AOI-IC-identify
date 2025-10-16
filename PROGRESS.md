# PROGRESS.md

A running progress tracker for the AOI IC Marking project. Update this as milestones move forward.

Status legend: NOT STARTED | IN PROGRESS | DONE

Summary
- Tooling installed (Python venv, pip, build essentials); backend tests passing. Docker Engine + Compose installed and images built. Frontend deps installed (Node 20 + npm). Next up: M4 (enqueue + status) and M5 (decision engine v0); start frontend dev server.

Milestone status
- M0 Repo bootstrap and governance: DONE
- M1 Backend platform foundation (FastAPI microservices): DONE
- M2 Task queue foundation (Celery + Redis): DONE (stub tasks wired)
- M3 Database schema and persistence (PostgreSQL): DONE (models, create_all, /db/health, debug create/read)
- M4 Batch pipeline MVP (two signals): NOT STARTED
- M5 Decision Engine v0 (rule-based): NOT STARTED
- M6 Component Verification v0: NOT STARTED
- M7 Live stream skeleton (WebSocket + MJPEG): DONE (WS and feed stub)
- M8 Frontend MVP (Next.js): IN PROGRESS (scaffold exists; dev server/pages to wire up)
- M9 Containerized dev environment (Docker Compose): DONE
- M10 Testing and CI: IN PROGRESS (service health tests added)
- M11 Data audit trail (shadow tables + triggers): NOT STARTED
- M12 Observability and hardening: NOT STARTED

Next actions
- M4: Implement POST /inspections (enqueue process_inspection_image) and GET /inspections/{id} (mocked store).
- Frontend: npm install and run dev at http://localhost:3000; add basic pages and WS display for live stub.
- M5: Implement /decide with basic weighted rules and unit tests.

Changelog
- 2025-10-16: Installed Python tooling (venv/pip/build-essential), created venv and installed deps; ran pytest (passing). Installed Docker CE + Compose plugin, enabled service; built all images via `docker compose build`. Installed Node.js 20 + npm and `npm install` in frontend/.
- 2025-10-15: Installed Docker, Node, pip; built and started docker-compose; verified /health and /db/health OK.
- 2025-10-14: Completed database foundation (models, DB health route, debug create/read). Updated guide and .gitignore.
- 2025-10-14: Initial scaffolding created (backend services, Celery, tests, Dockerfile, docker-compose, Next.js minimal app).
