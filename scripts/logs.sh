#!/bin/bash
# logs.sh — AutoTest-Agent 日志查看脚本
# Usage: bash scripts/logs.sh [dev|prod|api|worker|postgres|redis] [-f] [--tail N]
#
# Services:
#   dev      - Development container logs
#   prod     - All production services logs
#   api      - API server logs only
#   worker   - Celery worker logs only
#   postgres - PostgreSQL logs only
#   redis    - Redis logs only
#
# Options:
#   -f, --follow     Follow log output (default: true)
#   --tail N         Number of lines to show from end (default: 100)
#
# Examples:
#   bash scripts/logs.sh dev              # View dev container logs (follow mode)
#   bash scripts/logs.sh prod -f          # View all prod logs (follow)
#   bash scripts/logs.sh api --tail 50    # View last 50 lines of API logs
#   bash scripts/logs.sh worker           # View Celery worker logs

set -e

# ===== Configuration =====
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
COMPOSE_FILE_DEV="$ROOT_DIR/docker-compose.dev.yml"
COMPOSE_FILE_PROD="$ROOT_DIR/docker-compose.yml"
SERVICE="${1:-dev}"
FOLLOW=true
TAIL_LINES=100

# Parse options
shift || true
while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--follow)
            FOLLOW=true
            shift
            ;;
        --no-follow)
            FOLLOW=false
            shift
            ;;
        --tail)
            TAIL_LINES="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

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

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed."
        exit 1
    fi

    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running."
        exit 1
    fi
}

# ===== Log Functions =====
show_dev_logs() {
    local follow_flag=""
    if [ "$FOLLOW" = true ]; then
        follow_flag="-f"
    fi

    log_info "Showing logs for development container..."
    docker logs $follow_flag --tail "$TAIL_LINES" autotest-agent-dev
}

show_prod_logs() {
    cd "$ROOT_DIR"

    if [ "$FOLLOW" = true ]; then
        log_info "Following logs for all production services..."
        docker compose -f "$COMPOSE_FILE_PROD" logs -f --tail="$TAIL_LINES"
    else
        log_info "Showing logs for all production services..."
        docker compose -f "$COMPOSE_FILE_PROD" logs --tail="$TAIL_LINES"
    fi
}

show_api_logs() {
    local follow_flag=""
    if [ "$FOLLOW" = true ]; then
        follow_flag="-f"
    fi

    log_info "Showing API server logs..."
    docker logs $follow_flag --tail "$TAIL_LINES" autotest-api
}

show_worker_logs() {
    local follow_flag=""
    if [ "$FOLLOW" = true ]; then
        follow_flag="-f"
    fi

    log_info "Showing Celery worker logs..."
    docker logs $follow_flag --tail "$TAIL_LINES" autotest-worker
}

show_postgres_logs() {
    local follow_flag=""
    if [ "$FOLLOW" = true ]; then
        follow_flag="-f"
    fi

    log_info "Showing PostgreSQL logs..."
    docker logs $follow_flag --tail "$TAIL_LINES" autotest-postgres
}

show_redis_logs() {
    local follow_flag=""
    if [ "$FOLLOW" = true ]; then
        follow_flag="-f"
    fi

    log_info "Showing Redis logs..."
    docker logs $follow_flag --tail "$TAIL_LINES" autotest-redis
}

show_help() {
    cat << EOF
AutoTest-Agent Log Viewer

USAGE:
    bash scripts/logs.sh [SERVICE] [OPTIONS]

SERVICES:
    dev       Development container logs
    prod      All production services logs
    api       API server logs only
    worker    Celery worker logs only
    postgres  PostgreSQL logs only
    redis     Redis logs only

OPTIONS:
    -f, --follow      Follow log output (default: true)
    --no-follow       Show logs without following
    --tail N          Number of lines to show (default: 100)
    -h, --help        Show this help message

EXAMPLES:
    bash scripts/logs.sh dev                  # View dev logs (follow mode)
    bash scripts/logs.sh prod                 # View all prod logs
    bash scripts/logs.sh api --tail 50        # Last 50 lines of API logs
    bash scripts/logs.sh worker --no-follow   # Worker logs (no follow)

TIPS:
    - Use Ctrl+C to stop following logs
    - Combine with grep: bash scripts/logs.sh api | grep ERROR
    - Save to file: bash scripts/logs.sh prod > logs.txt

EOF
}

# ===== Main Execution =====
main() {
    check_docker

    case "$SERVICE" in
        dev)
            show_dev_logs
            ;;
        prod)
            show_prod_logs
            ;;
        api)
            show_api_logs
            ;;
        worker)
            show_worker_logs
            ;;
        postgres)
            show_postgres_logs
            ;;
        redis)
            show_redis_logs
            ;;
        -h|--help|help)
            show_help
            ;;
        *)
            log_error "Unknown service: $SERVICE"
            show_help
            exit 1
            ;;
    esac
}

main
