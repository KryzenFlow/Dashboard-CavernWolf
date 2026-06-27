#!/bin/bash
# WSL2 Setup for Hermes Backend (Native)
# Run this inside WSL2 Ubuntu

set -e

echo "=== Hermes WSL2 Setup ==="

# 1. Create Hermes directory
HERMES_DIR="/home/whoami/hermes-backend"
mkdir -p ""
cd ""

# 2. Clone or link the backend
echo "Setting up Hermes backend..."
if [ ! -d "backend" ]; then
    # Option A: Clone from GitHub
    # git clone https://github.com/KryzenFlow/Dashboard-CavernWolf.git .
    
    # Option B: Link from Windows (if using /mnt/c/)
    WIN_PATH="/mnt/e/Dashboard-CavernWolf"
    if [ -d "" ]; then
        ln -s "/backend" ./backend
        ln -s "/shared" ./shared
        echo "Linked backend from Windows: "
    else
        echo "ERROR: Windows path not found: "
        exit 1
    fi
fi

# 3. Create Python virtual environment
echo "Creating Python environment..."
python3 -m venv venv
source venv/bin/activate

# 4. Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install fastapi uvicorn[standard] websockets python-dotenv
pip install redis qdrant-client cockroachdb sqlalchemy
pip install httpx aiofiles pyyaml

# 5. Create .env file
echo "Creating .env..."
cat > .env << 'EOF'
# Hermes Backend Config (WSL2 Native)
LLM_PROVIDER=mock
AGENT_STACK_ENABLED=1

# Infrastructure (Docker containers)
REDIS_URL=redis://localhost:6379
QDRANT_URL=http://localhost:6333
COCKROACH_URL=postgresql://root@localhost:26257/mock_test_clinic?sslmode=disable

# LLaMA (Native in WSL2)
LLAMA_HOST=http://localhost:8080

# Server
HOST=0.0.0.0
PORT=8000
EOF

# 6. Create startup script
echo "Creating startup script..."
cat > start-hermes.sh << 'EOF'
#!/bin/bash
cd /home/whoami/hermes-backend
source venv/bin/activate

echo "Starting Hermes Backend on port 8000..."
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
EOF
chmod +x start-hermes.sh

# 7. Create LLaMA startup script
cat > start-llama.sh << 'EOF'
#!/bin/bash
echo "Starting LLaMA server..."
# Install ollama if not present
if ! command -v ollama &> /dev/null; then
    curl -fsSL https://ollama.com/install.sh | sh
fi

# Start ollama service
ollama serve &
sleep 5

# Pull and run model
ollama pull llama2
ollama run llama2
EOF
chmod +x start-llama.sh

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Start Docker infrastructure: docker-compose -f docker-compose.infra.yml up -d"
echo "2. Start Hermes backend: ./start-hermes.sh"
echo "3. Start LLaMA (optional): ./start-llama.sh"
echo ""
echo "Services:"
echo "  - Hermes API: http://localhost:8000"
echo "  - Redis: localhost:6379"
echo "  - Qdrant: http://localhost:6333"
echo "  - CockroachDB: localhost:26257"
echo "  - LLaMA: http://localhost:8080"
