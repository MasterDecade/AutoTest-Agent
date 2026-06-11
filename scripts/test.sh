#!/bin/bash
# test.sh — AutoTest-Agent 测试执行脚本（完全Docker化）
# Usage: bash scripts/test.sh [unit|integration|sandbox|all] [--coverage] [--verbose]
#
# Test Types:
#   unit         - Run unit tests only
#   integration  - Run integration tests only
#   sandbox      - Run sandbox isolation tests
#   all          - Run all tests (default)
#
# Options:
#   --coverage   Generate coverage report
#   --verbose    Enable verbose output
#   --no-cache   Build containers without cache
#
# Examples:
#   bash scripts/test.sh                  # Run all tests
#   bash scripts/test.sh unit             # Run unit tests only
#   bash scripts/test.sh all --coverage   # Run all tests with coverage
#   bash scripts/test.sh sandbox --verbose  # Run sandbox tests verbosely

set -e

# ===== Configuration =====
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
COMPOSE_FILE_DEV="$ROOT_DIR/docker-compose.dev.yml"
TEST_TYPE="${1:-all}"
WITH_COVERAGE=false
VERBOSE=false
NO_CACHE=false

# Parse options
shift || true
while [[ $# -gt 0 ]]; do
    case $1 in
        --coverage)
            WITH_COVERAGE=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --no-cache)
            NO_CACHE=true
            shift
            ;;
        *)
            if [ -z "$TEST_TYPE" ]; then
                TEST_TYPE="$1"
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
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running."
        exit 1
    fi

    if ! command -v docker compose &> /dev/null; then
        log_error "Docker Compose plugin is not installed."
        exit 1
    fi
}

# ===== Test Functions =====
setup_test_environment() {
    log_section "Setting Up Test Environment"

    cd "$ROOT_DIR"

    log_info "Building test containers..."
    local cache_flag=""
    if [ "$NO_CACHE" = true ]; then
        cache_flag="--no-cache"
    fi
    docker compose -f "$COMPOSE_FILE_DEV" build $cache_flag

    log_info "Starting dependencies (PostgreSQL, Redis)..."
    docker compose -f "$COMPOSE_FILE_DEV" up -d postgres redis

    log_info "Waiting for services to be ready..."
    local retry=0
    local max_retries=30
    until docker exec autotest-dev-postgres pg_isready -U autotest -d autotest_dev > /dev/null 2>&1 || [ $retry -eq $max_retries ]; do
        log_info "Waiting for PostgreSQL... ($(($retry + 1))/$max_retries)"
        sleep 2
        retry=$((retry + 1))
    done

    if [ $retry -eq $max_retries ]; then
        log_error "PostgreSQL failed to start within timeout"
        cleanup_test_environment
        exit 1
    fi

    log_info "Database is ready!"
}

cleanup_test_environment() {
    log_info "Cleaning up test environment..."
    cd "$ROOT_DIR"
    docker compose -f "$COMPOSE_FILE_DEV" down
}

run_unit_tests() {
    log_section "Running Unit Tests"

    local verbose_flag=""
    if [ "$VERBOSE" = true ]; then
        verbose_flag="-v"
    fi

    local coverage_flag=""
    if [ "$WITH_COVERAGE" = true ]; then
        coverage_flag="--cov=src --cov-report=term-missing --cov-report=html:coverage"
    fi

    log_info "Executing unit tests in isolated container..."
    docker compose -f "$COMPOSE_FILE_DEV" run --rm devcontainer bash -c "
        cd /workspace && \
        pip install --index-url https://pypi.tuna.tsinghua.edu.cn/simple -r requirements-dev.txt && \
        pytest tests/unit/ $verbose_flag $coverage_flag -W ignore::DeprecationWarning
    "

    return $?
}

run_integration_tests() {
    log_section "Running Integration Tests"

    local verbose_flag=""
    if [ "$VERBOSE" = true ]; then
        verbose_flag="-v"
    fi

    local coverage_flag=""
    if [ "$WITH_COVERAGE" = true ]; then
        coverage_flag="--cov=src --cov-report=term-missing --cov-append"
    fi

    log_info "Executing integration tests in isolated container..."
    docker compose -f "$COMPOSE_FILE_DEV" run --rm devcontainer bash -c "
        cd /workspace && \
        pip install --index-url https://pypi.tuna.tsinghua.edu.cn/simple -r requirements-dev.txt && \
        pytest tests/integration/ $verbose_flag $coverage_flag -W ignore::DeprecationWarning
    "

    return $?
}

run_sandbox_tests() {
    log_section "Running Sandbox Isolation Tests"

    local verbose_flag=""
    if [ "$VERBOSE" = true ]; then
        verbose_flag="-v"
    fi

    log_info "Testing sandbox isolation mechanisms..."
    docker compose -f "$COMPOSE_FILE_DEV" run --rm devcontainer bash -c "
        cd /workspace && \
        pip install --index-url https://pypi.tuna.tsinghua.edu.cn/simple -r requirements-dev.txt && \
        pytest tests/sandbox/ $verbose_flag -W ignore::DeprecationWarning
    "

    return $?
}

show_coverage_report() {
    if [ "$WITH_COVERAGE" = true ]; then
        log_section "Coverage Report"
        log_info "HTML coverage report generated at: coverage/index.html"
        log_info "Open with: xdg-open coverage/index.html"
    fi
}

show_help() {
    cat << EOF
AutoTest-Agent Test Runner (Dockerized)

USAGE:
    bash scripts/test.sh [TEST_TYPE] [OPTIONS]

TEST TYPES:
    unit         Run unit tests only
    integration  Run integration tests only
    sandbox      Run sandbox isolation tests
    all          Run all tests (default)

OPTIONS:
    --coverage   Generate coverage report
    -v, --verbose  Enable verbose output
    --no-cache   Build containers without cache
    -h, --help   Show this help message

EXAMPLES:
    bash scripts/test.sh                      # Run all tests
    bash scripts/test.sh unit                 # Run unit tests only
    bash scripts/test.sh all --coverage       # All tests with coverage
    bash scripts/test.sh sandbox --verbose    # Sandbox tests verbosely
    bash scripts/test.sh integration --no-cache  # Integration tests, no cache

TEST STRUCTURE:
    tests/
    ├── unit/           # Unit tests for individual modules
    ├── integration/    # Integration tests (API, database)
    └── sandbox/        # Sandbox isolation tests

NOTES:
    - All tests run in isolated Docker containers
    - No dependencies installed on host machine
    - Database and Redis are ephemeral (cleaned after tests)
    - Coverage reports saved to coverage/ directory

EOF
}

# ===== Main Execution =====
main() {
    check_docker

    local exit_code=0

    # Setup
    setup_test_environment

    # Run tests based on type
    case "$TEST_TYPE" in
        unit)
            run_unit_tests || exit_code=$?
            ;;
        integration)
            run_integration_tests || exit_code=$?
            ;;
        sandbox)
            run_sandbox_tests || exit_code=$?
            ;;
        all)
            run_unit_tests || exit_code=$?
            run_integration_tests || exit_code=$?
            run_sandbox_tests || exit_code=$?
            ;;
        -h|--help|help)
            show_help
            cleanup_test_environment
            exit 0
            ;;
        *)
            log_error "Unknown test type: $TEST_TYPE"
            show_help
            cleanup_test_environment
            exit 1
            ;;
    esac

    # Show coverage if enabled
    show_coverage_report

    # Cleanup
    cleanup_test_environment

    # Final status
    echo ""
    if [ $exit_code -eq 0 ]; then
        log_info "All tests passed!"
    else
        log_error "Tests failed with exit code: $exit_code"
    fi

    exit $exit_code
}

main
