# SETUP.md

This file records local setup actions and instructions for running the project.

---

## Prerequisites Installation

### Docker Engine and Compose
- Added Docker APT repo and GPG key (Debian bookworm)
- Installed packages: docker-ce, docker-ce-cli, containerd.io, docker-buildx-plugin, docker-compose-plugin
- Enabled and started docker service; added current user to docker group (log out/in to apply non-sudo usage)
- Verified versions:
  - Docker: 28.5.1
  - Docker Compose: v2.40.0

**Installation commands:**
```bash
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian bookworm stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update && sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo systemctl enable --now docker && sudo usermod -aG docker "$USER"
```

### Node.js and npm
- Added NodeSource Node 20 repo
- Installed nodejs (Node 20.19.5, npm 10.8.2)

**Installation commands:**
```bash
curl -fsSL https://deb.nodesource.com/setup_20.x -o /tmp/nodesource_setup.sh
sudo -E bash /tmp/nodesource_setup.sh && sudo apt-get install -y nodejs
```

### Python tooling (only needed for Method 2: Local Services)
- APT packages: python3-venv, python3-pip, build-essential, python3-dev, libexpat1-dev, zlib1g-dev, libpython3.11-dev
- Virtualenv: created .venv at repository root
- pip upgraded to 25.2
- Python dependencies installed from backend/requirements.txt

**Installation commands:**
```bash
sudo apt update && sudo apt install -y python3-venv python3-pip build-essential python3-dev
python3 -m venv .venv && .venv/bin/pip install --upgrade pip
.venv/bin/pip install -r backend/requirements.txt
```

---

## Running the Project

There are **two methods** to run the backend services:

### Method 1: Full Docker (Recommended for simplicity)
**Everything runs in containers - simplest approach, no Python setup needed**

#### Prerequisites:
- Docker Engine + Compose plugin installed
- Node.js installed (for frontend only)

#### Steps:
1. **Build Docker images:**
   ```bash
   docker compose build
   ```

2. **Start all services (backend + databases):**
   ```bash
   docker compose up -d
   # or if using older Docker:
   # docker-compose up -d
   ```

3. **Start frontend:**
   ```bash
   npm install --prefix ./frontend
   npm run dev --prefix ./frontend
   ```

4. **Access the app:**
   - Frontend: http://localhost:3000

#### Service URLs:
- API Gateway: http://localhost:8003/health
- Inspection Service: http://localhost:8001/health, http://localhost:8001/db/health
- Stream Ingestion: http://localhost:8002/health, ws://localhost:8002/ws/live/analysis
- Decision Engine: http://localhost:8004/health
- Verification Service: http://localhost:8005/health

#### Stop services:
```bash
docker compose down
```

---

### Method 2: Local Services with Docker Databases (For development)
**Backend services run locally via uvicorn, only databases in Docker**

#### Prerequisites:
- Docker Engine + Compose plugin installed
- Node.js installed
- Python 3 + virtualenv with dependencies installed

#### Steps:
1. **Start only Postgres & Redis via Docker:**
   ```bash
   docker compose up postgres redis -d
   ```

2. **Activate Python virtual environment:**
   ```bash
   source .venv/bin/activate
   ```

3. **Start each backend service in a separate terminal:**
   
   **Terminal 1 - API Gateway:**
   ```bash
   PYTHONPATH=$(pwd)/backend .venv/bin/uvicorn api_gateway.main:app --host 0.0.0.0 --port 8003 --reload --app-dir backend
   ```
   
   **Terminal 2 - Inspection Service:**
   ```bash
   PYTHONPATH=$(pwd)/backend .venv/bin/uvicorn inspection_service.main:app --host 0.0.0.0 --port 8001 --reload --app-dir backend
   ```
   
   **Terminal 3 - Stream Ingestion:**
   ```bash
   PYTHONPATH=$(pwd)/backend .venv/bin/uvicorn stream_ingestion_service.main:app --host 0.0.0.0 --port 8002 --reload --app-dir backend
   ```
   
   **Terminal 4 - Decision Engine:**
   ```bash
   PYTHONPATH=$(pwd)/backend .venv/bin/uvicorn decision_engine.main:app --host 0.0.0.0 --port 8004 --reload --app-dir backend
   ```
   
   **Terminal 5 - Verification Service:**
   ```bash
   PYTHONPATH=$(pwd)/backend .venv/bin/uvicorn verification_service.main:app --host 0.0.0.0 --port 8005 --reload --app-dir backend
   ```
   
   **Terminal 6 - Celery Worker (optional for batch processing):**
   ```bash
   celery -A backend.batch_processing_service.celery_app worker --loglevel=info
   ```

4. **Start frontend (in another terminal):**
   ```bash
   npm run dev --prefix ./frontend
   ```

5. **Access the app:**
   - Frontend: http://localhost:3000

#### Service URLs:
Same as Method 1 (see above)

#### Stop services:
```bash
# Stop backend services: Ctrl+C in each terminal
# Stop databases:
docker compose down
```

---

## Testing

**Run all tests:**
```bash
.venv/bin/pytest backend/tests -q
```

**Run specific test file:**
```bash
.venv/bin/pytest backend/tests/test_health_endpoints.py -q
```

**Run single test:**
```bash
.venv/bin/pytest backend/tests/test_health_endpoints.py::test_api_gateway_health -q
```

---

## Environment Variables

Optional environment variables (can be set in `.env` file or exported in shell):
- `DATABASE_URL` - PostgreSQL connection string
- `CELERY_BROKER_URL` - Redis broker URL for Celery
- `CELERY_RESULT_BACKEND` - Redis backend for Celery results
- `NEXAR_API_KEY` - API key for Nexar component verification
- `NEXT_PUBLIC_API_URL` - Frontend API endpoint URL

---

## Migration to New PC

1. Install Docker (with Compose plugin) and Node.js
2. Clone this repository
3. Copy your `.env` file (or set environment variables)
4. Choose your method:
   - **Method 1:** `docker compose build && docker compose up -d`
   - **Method 2:** Install Python deps, then follow Method 2 steps
5. Start frontend: `npm install --prefix ./frontend && npm run dev --prefix ./frontend`
6. If needed, restore Postgres data by importing a dump into the postgres container
