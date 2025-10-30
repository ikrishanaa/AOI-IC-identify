# Local Development & Testing Guide

This guide helps you run the full stack locally and verify it’s working.

## Prerequisites
- Docker + Docker Compose (v2)
- Node.js 18+ and npm
- (Optional) Python 3.11 + venv for local-only backend runs

## Start stack with Docker Compose
1. Build images (first time or after backend changes):
   ```bash
   docker compose build
   ```
2. Start services (DB, Redis, backend services, worker):
   ```bash
   docker compose up -d
   docker compose ps
   ```
3. Verify health endpoints:
   ```bash
   curl -fsS http://localhost:8003/health   # API Gateway
   curl -fsS http://localhost:8001/health   # Inspection Service
   curl -fsS http://localhost:8002/health   # Stream Ingestion
   curl -fsS http://localhost:8004/health   # Decision Engine
   curl -fsS http://localhost:8005/health   # Verification Service
   ```

## Start frontend (local dev)
1. Ensure API URL points to API Gateway from Compose:
   ```bash
   export NEXT_PUBLIC_API_URL=http://localhost:8003
   ```
2. Run Next.js dev server:
   ```bash
   cd frontend
   npm run dev   # http://localhost:3000
   ```

## Smoke tests
- Open http://localhost:3000 in a browser; the dev server should be up.
- All health endpoints above should return 200 with service names.

## Run backend unit tests (optional)
```bash
pytest backend/tests -q
```

## Logs & troubleshooting
- Container logs:
  ```bash
  docker compose logs -f api_gateway
  docker compose logs -f inspection_service
  docker compose logs -f decision_engine
  docker compose logs -f verification_service
  docker compose logs -f stream_ingestion_service
  docker compose logs -f batch_worker
  docker compose logs -f postgres
  docker compose logs -f redis
  ```
- Restart a service:
  ```bash
  docker compose restart api_gateway
  ```
- Common issues:
  - Database unavailable: check `postgres` is healthy and `DATABASE_URL` in services.
  - Redis unavailable: ensure `redis` is healthy and Celery env vars match.
  - CORS/frontend errors: confirm `NEXT_PUBLIC_API_URL` and gateway CORS.

## Stop stack
```bash
docker compose down
```
