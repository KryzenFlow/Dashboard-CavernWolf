# Hermes Stack - WSL2 + Docker Setup Guide

## Architecture Overview

`
WSL2 (Ubuntu) - Native
├── Hermes Backend (FastAPI) - Port 8000
└── LLaMA/Ollama - Port 8080 (GPU access)

Docker Containers - Infrastructure
├── Redis - Port 6379 (cache + pub/sub)
├── Qdrant - Port 6333/6334 (vector DB)
├── CockroachDB - Port 26257/8081 (data)
└── Agent Claw - Port 9000 (WebSocket)
`

## Quick Start

### 1. Start Docker Infrastructure (Windows PowerShell)
`powershell
cd E:\Dashboard-CavernWolf
docker-compose -f docker-compose.infra.yml up -d
`

### 2. Start Hermes Backend (WSL2 Terminal)
`ash
# First time setup
cd /mnt/e/Dashboard-CavernWolf/scripts
chmod +x setup-wsl2-hermes.sh
./setup-wsl2-hermes.sh

# After setup, start Hermes
cd ~/hermes-backend
./start-hermes.sh
`

### 3. Start LLaMA (Optional - WSL2)
`ash
cd ~/hermes-backend
./start-llama.sh
`

## Service URLs

| Service | URL | Status |
|---------|-----|--------|
| Hermes API | http://localhost:8000 | WSL2 Native |
| LLaMA | http://localhost:8080 | WSL2 Native |
| Redis | redis://localhost:6379 | Docker |
| Qdrant | http://localhost:6333 | Docker |
| CockroachDB | localhost:26257 | Docker |
| Agent Claw | ws://localhost:9000 | Docker |

## Lifecycle Management

### Start Everything
`powershell
# Windows - Start Docker infra
docker-compose -f docker-compose.infra.yml up -d

# WSL2 - Start Hermes + LLaMA
cd ~/hermes-backend
./start-hermes.sh &
./start-llama.sh &
`

### Stop Everything
`powershell
# Windows - Stop Docker infra
docker-compose -f docker-compose.infra.yml down

# WSL2 - Stop Hermes + LLaMA
pkill -f uvicorn
pkill -f ollama
`

### Check Status
`powershell
# Docker containers
docker ps

# WSL2 processes
wsl -e bash -c "ps aux | grep -E 'uvicorn|ollama'"
`

## Why This Split?

- **WSL2 Native**: LLaMA needs direct GPU access (Docker GPU passthrough is painful)
- **WSL2 Native**: Hermes benefits from direct file system access to Windows paths
- **Docker**: Redis/Qdrant/CockroachDB are infrastructure - isolated, reproducible, easy to restart
- **Docker**: Agent Claw is a service - benefits from containerization

## Troubleshooting

### Docker containers can't connect to WSL2 services
- Use host.docker.internal instead of localhost in container configs
- Or use the WSL2 IP: ip addr show eth0 | grep inet

### WSL2 can't connect to Docker containers
- Use localhost - Docker Desktop exposes ports to WSL2 automatically
- Verify: curl http://localhost:6379 (Redis should respond)

### GPU not detected in WSL2
- Ensure NVIDIA drivers are installed on Windows
- Run 
vidia-smi in WSL2 to verify
