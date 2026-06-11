#!/bin/bash
# stop.sh — AutoTest-Agent 环境停止和清理脚本
# Usage: bash scripts/stop.sh [dev|prod|all] [--remove-volumes] [--remove-images]
#
# Modes:
#   dev      - Stop development environment
#   prod     - Stop production environment
#   all      - Stop all environments
#
# Options:
#   --remove-volumes    Remove data volumes (WARNING: deletes database data!)
#   --remove-images     Remove Docker images (requires rebuild next time)
#   --clean             Remove all containers, volumes, and networks
#
# Examples:
#   bash scripts/stop.sh dev                # Stop dev environment (keep data)
#   bash scripts/stop.sh prod               # Stop production environment
#   bash scripts/stop.sh dev --remove-volumes  # Stop dev and delete data
#   bash scripts/stop.sh all --clean        # Clean everything

set -e

# ===== Configuration =====
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
COMPOSE_FILE_DEV="$ROOT_DIR/docker-compose.dev.yml"
COMPOSE_FILE_PROD="$ROOT_DIR/docker-compose.yml"
MODE="${1:-dev}"
REMOVE_VOLUMES=false
REMOVE_IMAGES=false
CLEAN_ALL=false

# Parse options
shift || true
while [[ $# -gt 0 ]]; do
    case $1 in
        --remove-volumes)
            REMOVE_VOLUMES=true
            shift
            ;;
        --remove-images)
            REMOVE_IMAGES=true
            shift
            ;;
        --clean)
            CLEAN_ALL=true
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

# ===== Color Codes =====
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
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
        log_error "Docker is not installed."
        exit 1
    fi

    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running."
        exit 1
    fi
}

confirm_action() {
    local message="$1"
    echo -e "${YELLOW}$message${NC}"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Operation cancelled."
        exit 0
    fi
}

# ===== Stop Functions =====
stop_dev_environment() {
    log_section "Stopping Development Environment"

    cd "$ROOT_DIR"

    log_info "Stopping development containers..."
    docker compose -f "$COMPOSE_FILE_DEV" down

    if [ "$REMOVE_VOLUMES" = true ] || [ "$CLEAN_ALL" = true ]; then
        confirm_action "WARNING: This will delete all development database data!"
        log_warn "Removing development volumes..."
        docker volume rm autotest_dev_postgres_data 2>/dev/null || true
        docker volume rm autotest_dev_redis_data 2>/dev/null || true
    fi

    if [ "$REMOVE_IMAGES" = true ] || [ "$CLEAN_ALL" = true ]; then
        log_warn "Removing development images..."
        docker rmi autotest-agent-devcontainer 2>/dev/null || true
    fi

    log_info "Development environment stopped."
}

stop_prod_environment() {
    log_section "Stopping Production Environment"

    cd "$ROOT_DIR"

    log_info "Stopping production containers..."
    docker compose -f "$COMPOSE_FILE_PROD" down

    if [ "$REMOVE_VOLUMES" = true ] || [ "$CLEAN_ALL" = true ]; then
        confirm_action "WARNING: This will delete ALL production database data!"
        log_warn "Removing production volumes..."
        docker volume rm autotest_postgres_data 2>/dev/null || true
        docker volume rm autotest_redis_data 2>/dev/null || true
        docker volume rm autotest_app_data 2>/dev/null || true
    fi

    if [ "$REMOVE_IMAGES" = true ] || [ "$CLEAN_ALL" = true ]; then
        log_warn "Removing production images..."
        docker rmi autotest-agent:latest 2>/dev/null || true
    fi

    log_info "Production environment stopped."
}

stop_all_environments() {
    log_section "Stopping All Environments"

    log_info "Stopping development environment..."
    stop_dev_environment

    log_info "Stopping production environment..."
    stop_prod_environment

    if [ "$CLEAN_ALL" = true ]; then
        clean_docker_system
    fi
}

clean_docker_system() {
    log_section "Cleaning Docker System"

    confirm_action "WARNING: This will remove ALL unused Docker resources!"

    log_warn "Removing stopped containers..."
    docker container prune -f

    log_warn "Removing unused networks..."
    docker network prune -f

    log_warn "Removing dangling images..."
    docker image prune -f

    if [ "$REMOVE_VOLUMES" = true ]; then
        log_warn "Removing unused volumes..."
        docker volume prune -f
    fi

    log_info "Docker system cleaned."
}

show_status() {
    log_section "Current Container Status"

    echo -e "${CYAN}Running Containers:${NC}"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "autotest|NAME" || echo "No AutoTest containers running"

    echo -e "\n${CYAN}AutoTest Volumes:${NC}"
    docker volume ls --filter name=autotest --format "table {{.Name}}\t{{.Driver}}" || echo "No AutoTest volumes"

    echo -e "\n${CYAN}AutoTest Images:${NC}"
    docker images --filter reference="autotest*" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" || echo "No AutoTest images"
}

show_help() {
    cat << EOF
AutoTest-Agent Stop & Cleanup Script

USAGE:
    bash scripts/stop.sh [MODE] [OPTIONS]

MODES:
    dev       Stop development environment (default)
    prod      Stop production environment
    all       Stop all environments

OPTIONS:
    --remove-volumes    Remove data volumes (WARNING: deletes database!)
    --remove-images     Remove Docker images
    --clean             Remove all containers, volumes, and networks
    -h, --help          Show this help message

EXAMPLES:
    bash scripts/stop.sh dev                      # Stop dev (keep data)
    bash scripts/stop.sh prod                     # Stop production
    bash scripts/stop.sh dev --remove-volumes     # Stop dev and delete data
    bash scripts/stop.sh all --clean              # Clean everything

SAFETY:
    - Data removal requires confirmation
    - Use --remove-volumes with caution!
    - Regular cleanup recommended to free disk space

RELATED COMMANDS:
    bash scripts/start.sh [mode]    # Start services
    bash scripts/logs.sh [mode]     # View logs
    docker ps                       # List running containers
    docker stats                    # Show resource usage

EOF
}

# ===== Main Execution =====
main() {
    check_docker

    case "$MODE" in
        dev)
            stop_dev_environment
            ;;
        prod)
            stop_prod_environment
            ;;
        all)
            stop_all_environments
            ;;
        status)
            show_status
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

    if [ "$MODE" != "status" ]; then
        echo ""
        log_info "Done. Use 'bash scripts/stop.sh status' to check current status."
    fi
}

main
