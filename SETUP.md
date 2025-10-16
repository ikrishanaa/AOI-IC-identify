# SETUP.md

This file records local setup actions performed to get the project ready for testing and running locally.

What was installed
- Python tooling
  - APT packages: python3-venv, python3-pip, build-essential, python3-dev, libexpat1-dev, zlib1g-dev, libpython3.11-dev
  - Virtualenv: created .venv at repository root
  - pip upgraded to 25.2
  - Python dependencies installed from backend/requirements.txt
  - Tests executed: `.venv/bin/pytest backend/tests -q` (passing)

- Docker Engine and Compose
  - Added Docker APT repo and GPG key (Debian bookworm)
  - Installed packages: docker-ce, docker-ce-cli, containerd.io, docker-buildx-plugin, docker-compose-plugin
  - Enabled and started docker service; added current user to docker group (log out/in to apply non-sudo usage)
  - Verified versions:
    - Docker: 28.5.1
    - Docker Compose: v2.40.0
  - Built images: `sudo docker compose build`

- Node.js and npm
  - Added NodeSource Node 20 repo
  - Installed nodejs (Node 20.19.5, npm 10.8.2)
  - Installed frontend deps: `npm install --prefix ./frontend`

Commands used (chronological)
- sudo apt update && sudo apt install -y python3-venv python3-pip build-essential python3-dev
- python3 -m venv .venv && .venv/bin/pip install --upgrade pip && \
  .venv/bin/pip install -r backend/requirements.txt && \
  .venv/bin/pytest backend/tests -q
- sudo apt-get install -y ca-certificates curl gnupg
- sudo install -m 0755 -d /etc/apt/keyrings
- curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
- echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian bookworm stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
- sudo apt-get update && sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
- sudo systemctl enable --now docker && sudo usermod -aG docker "$USER"
- sudo docker compose build
- curl -fsSL https://deb.nodesource.com/setup_20.x -o /tmp/nodesource_setup.sh
- sudo -E bash /tmp/nodesource_setup.sh && sudo apt-get install -y nodejs
- npm install --prefix ./frontend

Next steps to run locally
- Start services: `sudo docker compose up -d`
- Start frontend: `npm run dev --prefix ./frontend` then open http://localhost:3000
