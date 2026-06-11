#!/bin/bash
# start.sh — AutoTest-Agent 一键启动脚本（Docker化版本）
# Usage: bash scripts/start.sh [dev|prod|backend|frontend|test] [-d]
#
# Modes:
#   dev      - Start development environment (docker-compose.dev.yml)
#   prod     - Start production environment (docker-compose.yml)
#   backend  - Start only backend service in container
#   frontend - Start only frontend service in container
#   test     - Start test environment with isolated containers
#
# Options:
#   -d       - Run in detached mode (background)
#
# Examples:
#   bash scripts/start.sh dev        # Start dev environment (foreground)
#   bash scripts/start.sh dev -d     # Start dev environment (background)
#   bash scripts/start.sh prod -d    # Start production environment
#   bash scripts/start.sh test       # Run tests in isolated containers

set -e

# ===== Configuration =====
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
COMPOSE_FILE_DEV="$ROOT_DIR/docker-compose.dev.yml"
COMPOSE_FILE_PROD="$ROOT_DIR/docker-compose.yml"
MODE="${1:-dev}"
DETACHED=false
COMPOSE_ARGS=""

# Parse options
while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--detach)
            DETACHED=true
            shift
            ;;
        *)
            if [ -z "$MODE" ]; then
                MODE="$1"
            fi
            shift
            ;;
    esac
done

# Set detached mode flag
if [ "$DETACHED" = true ]; then
    COMPOSE_ARGS="-d"
fi

# ===== Color Codes =====
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ===== Helper Functions =====
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_section() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running. Please start Docker Desktop or Docker Engine."
        exit 1
    fi

    if ! command -v docker compose &> /dev/null; then
        log_error "Docker Compose plugin is not installed. Please install docker-compose-plugin."
        exit 1
    fi
}

check_env_file() {
    if [ ! -f "$ROOT_DIR/.env" ]; then
        log_warn ".env file not found. Creating from .env.example..."
        if [ -f "$ROOT_DIR/.env.example" ]; then
            cp "$ROOT_DIR/.env.example" "$ROOT_DIR/.env"
            log_warn "Please edit .env file and set your LLM API keys before starting services."
        else
            log_error ".env.example not found. Cannot create .env file."
            exit 1
        fi
    fi
}

# ===== Service Functions =====
start_dev_environment() {
    log_section "Starting Development Environment"

    check_env_file

    cd "$ROOT_DIR"

    log_info "Building development containers..."
    docker compose -f "$COMPOSE_FILE_DEV" build

    log_info "Starting services..."
    docker compose -f "$COMPOSE_FILE_DEV" up $COMPOSE_ARGS

    if [ "$DETACHED" = true ]; then
        log_info "Development environment started in background."
        log_info ""
        log_info "Services:"
        log_info "  - Dev Container: http://localhost:8080 (API), http://localhost:3000 (Frontend)"
        log_info "  - PostgreSQL:    localhost:5432"
        log_info "  - Redis:         localhost:6379"
        log_info ""
        log_info "Useful commands:"
        log_info "  - View logs:     bash scripts/logs.sh dev"
        log_info "  - Stop services: bash scripts/stop.sh dev"
        log_info "  - Exec into dev: docker exec -it autotest-agent-dev bash"
    fi
}

start_prod_environment() {
    log_section "Starting Production Environment"

    check_env_file

    cd "$ROOT_DIR"

    log_info "Building production containers..."
    docker compose -f "$COMPOSE_FILE_PROD" build --no-cache

    log_info "Starting production services..."
    docker compose -f "$COMPOSE_FILE_PROD" up $COMPOSE_ARGS

    if [ "$DETACHED" = true ]; then
        log_info "Production environment started in background."
        log_info ""
        log_info "Services:"
        log_info "  - API Server:    http://localhost:8080"
        log_info "  - API Docs:      http://localhost:8080/api/docs"
        log_info "  - Celery Worker: Running"
        log_info "  - PostgreSQL:    localhost:5432"
        log_info "  - Redis:         localhost:6379"
        log_info ""
        log_info "Useful commands:"
        log_info "  - View logs:     bash scripts/logs.sh prod"
        log_info "  - Stop services: bash scripts/stop.sh prod"
        log_info "  - Scale worker:  docker compose -f docker-compose.yml up -d --scale worker=3"
    fi
}

start_backend_only() {
    log_section "Starting Backend Service Only"

    check_env_file

    cd "$ROOT_DIR"

    log_info "Starting backend in dev container..."
    docker compose -f "$COMPOSE_FILE_DEV" up -d devcontainer

    log_info "Waiting for database to be ready..."
    sleep 5

    # Execute uvicorn inside container
    docker exec -d autotest-agent-dev bash -c "cd /workspace && uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload"

    log_info "Backend started inside dev container."
    log_info "  - API: http://localhost:8080"
    log_info "  - Docs: http://localhost:8080/api/docs"
    log_info ""
    log_info "View logs: docker logs -f autotest-agent-dev"
}

start_frontend_only() {
    log_section "Starting Frontend Service Only"

    cd "$ROOT_DIR/frontend"

    log_info "Starting frontend in dev container..."
    docker compose -f "$COMPOSE_FILE_DEV" up -d devcontainer

    # Execute npm run dev inside container
    docker exec -d autotest-agent-dev bash -c "cd /workspace/frontend && npm run dev"

    log_info "Frontend started inside dev container."
    log_info "  - UI: http://localhost:3000"
    log_info ""
    log_info "View logs: docker logs -f autotest-agent-dev"
}

run_tests_in_container() {
    log_section "Running Tests in Isolated Container"

    check_env_file

    cd "$ROOT_DIR"

    log_info "Building test environment..."
    docker compose -f "$COMPOSE_FILE_DEV" build

    log_info "Starting dependencies (PostgreSQL, Redis)..."
    docker compose -f "$COMPOSE_FILE_DEV" up -d postgres redis

    log_info "Waiting for services to be ready..."
    sleep 10

    log_info "Running tests in isolated container..."
    docker compose -f "$COMPOSE_FILE_DEV" run --rm devcontainer bash -c "
        cd /workspace && \
        pip install --index-url https://pypi.tuna.tsinghua.edu.cn/simple -r requirements-dev.txt && \
        pytest tests/ -v --cov=src --cov-report=term-missing
    "

    TEST_EXIT_CODE=$?

    if [ $TEST_EXIT_CODE -eq 0 ]; then
        log_info "All tests passed!"
    else
        log_error "Tests failed with exit code: $TEST_EXIT_CODE"
    fi

    # Cleanup test dependencies
    log_info "Cleaning up test environment..."
    docker compose -f "$COMPOSE_FILE_DEV" down

    exit $TEST_EXIT_CODE
}

show_help() {
    cat << EOF
AutoTest-Agent Management Script

USAGE:
    bash scripts/start.sh [MODE] [-d]

MODES:
    dev       Start development environment (default)
    prod      Start production environment
    backend   Start only backend service
    frontend  Start only frontend service
    test      Run tests in isolated container

OPTIONS:
    -d, --detach    Run in detached mode (background)
    -h, --help      Show this help message

EXAMPLES:
    bash scripts/start.sh dev           # Start dev environment (foreground)
    bash scripts/start.sh dev -d        # Start dev environment (background)
    bash scripts/start.sh prod -d       # Start production environment
    bash scripts/start.sh backend       # Start backend only
    bash scripts/start.sh test          # Run tests

RELATED SCRIPTS:
    bash scripts/logs.sh [dev|prod]     # View service logs
    bash scripts/stop.sh [dev|prod]     # Stop services
    bash scripts/build_images.sh        # Build and export images

EOF
}

# ===== Main Execution =====
main() {
    check_docker

    case "$MODE" in
        dev)
            start_dev_environment
            ;;
        prod)
            start_prod_environment
            ;;
        backend)
            start_backend_only
            ;;
        frontend)
            start_frontend_only
            ;;
        test)
            run_tests_in_container
            ;;
        -h|--help|help)
            show_help
            ;;
        *)
            log_error "Unknown mode: $MODE"
            show_help
            exit 1
            ;;
    esac
}

main
