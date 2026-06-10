#!/bin/bash
# start.sh — AutoTest-Agent 一键启动脚本
# Usage: bash scripts/start.sh [backend|frontend|all]

set -e

MODE="${1:-all}"
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

start_backend() {
    echo "=== 启动后端服务 ==="
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    fi

    # Check Python dependencies
    python -c "import fastapi" 2>/dev/null || {
        echo "Installing Python dependencies..."
        pip install --index-url https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
    }

    echo "Starting uvicorn on 0.0.0.0:8080..."
    uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload
}

start_frontend() {
    echo "=== 启动前端服务 ==="
    cd "$ROOT_DIR/frontend"

    if [ ! -d "node_modules" ]; then
        echo "Installing npm dependencies..."
        npm install --registry=https://registry.npmmirror.com
    fi

    echo "Starting Vite dev server on http://localhost:3000..."
    npm run dev
}

case "$MODE" in
    backend)
        start_backend
        ;;
    frontend)
        start_frontend
        ;;
    all)
        echo "=== AutoTest-Agent 一键启动 ==="
        echo "后端: http://localhost:8080"
        echo "前端: http://localhost:3000"
        echo "API 文档: http://localhost:8080/api/docs"
        echo ""

        # Start backend in background
        start_backend &
        BACKEND_PID=$!

        # Give backend time to start
        sleep 2

        # Start frontend in foreground
        start_frontend

        # Cleanup
        kill $BACKEND_PID 2>/dev/null
        ;;
    *)
        echo "Usage: bash scripts/start.sh [backend|frontend|all]"
        exit 1
        ;;
esac