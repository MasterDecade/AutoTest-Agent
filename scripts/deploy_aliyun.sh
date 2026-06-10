#!/bin/bash
# deploy_aliyun.sh — AutoTest-Agent 阿里云部署脚本
# Usage: bash scripts/deploy_aliyun.sh
#
# Prerequisites:
#   1. Aliyun ECS instance with Docker installed
#   2. Aliyun RDS PostgreSQL instance
#   3. Aliyun Redis instance
#   4. Configure environment variables in .env file

set -e

echo "=== AutoTest-Agent 阿里云部署脚本 ==="
echo ""

# ===== Configuration =====
if [ ! -f ".env" ]; then
    echo "Error: .env file not found. Copy .env.example to .env and configure it."
    exit 1
fi

source .env

# ===== Step 1: Install Docker (if needed) =====
if ! command -v docker &> /dev/null; then
    echo "[1/5] Installing Docker..."
    curl -fsSL https://get.docker.com | bash
    sudo systemctl enable docker && sudo systemctl start docker
    sudo usermod -aG docker $USER
    echo "Docker installed."
else
    echo "[1/5] Docker already installed."
fi

# ===== Step 2: Configure Docker mirrors =====
echo "[2/5] Configuring Docker mirror..."
if [ -n "${DOCKER_MIRROR}" ]; then
    sudo mkdir -p /etc/docker
    if [ ! -f /etc/docker/daemon.json ]; then
        echo "{\"registry-mirrors\": [\"https://${DOCKER_MIRROR}\"]}" | sudo tee /etc/docker/daemon.json
        sudo systemctl restart docker
    fi
    echo "Docker mirror configured: ${DOCKER_MIRROR}"
else
    echo "No DOCKER_MIRROR set, using default registries."
fi

# ===== Step 3: Pull or build images =====
echo "[3/5] Preparing Docker images..."

# Pull dependency images with domestic mirrors
docker pull ${POSTGRES_IMAGE:-postgres:16-alpine} || \
    docker pull registry.cn-hangzhou.aliyuncs.com/library/postgres:16-alpine && \
    docker tag registry.cn-hangzhou.aliyuncs.com/library/postgres:16-alpine postgres:16-alpine

docker pull ${REDIS_IMAGE:-redis:7-alpine} || \
    docker pull registry.cn-hangzhou.aliyuncs.com/library/redis:7-alpine && \
    docker tag registry.cn-hangzhou.aliyuncs.com/library/redis:7-alpine redis:7-alpine

# Build AutoTest-Agent image
docker compose build --no-cache
echo "Images prepared."

# ===== Step 4: Initialize database =====
echo "[4/5] Initializing database..."
# Run Alembic migrations (requires database to be accessible)
if command -v alembic &> /dev/null; then
    alembic upgrade head 2>/dev/null || echo "Database migration skipped (ensure RDS is accessible)"
else
    echo "alembic not installed — database migration skipped"
fi

# ===== Step 5: Start services =====
echo "[5/5] Starting services..."
docker compose up -d

# Wait for services to be healthy
echo "Waiting for API service to become healthy..."
for i in $(seq 1 30); do
    if curl -s http://localhost:${API_PORT:-8080}/api/health | grep -q "healthy"; then
        echo "✅ Services are running!"
        break
    fi
    sleep 2
done

echo ""
echo "=== Deployment Complete ==="
echo "API:       http://localhost:${API_PORT:-8080}"
echo "API Docs:  http://localhost:${API_PORT:-8080}/api/docs"
echo "Frontend:  http://localhost:${FRONTEND_PORT:-3000}"
echo ""
echo "Check logs: docker compose logs -f api"