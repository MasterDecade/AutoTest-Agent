#!/bin/bash
# build_images.sh — AutoTest-Agent Docker image builder
# Builds the All-in-One production image and exports it as a tar archive
#
# Usage:
#   bash scripts/build_images.sh           # Build image
#   bash scripts/build_images.sh --export  # Build + export to autotest-agent.tar.gz
#   bash scripts/build_images.sh --push    # Build + push to registry

set -e

IMAGE_NAME="${IMAGE_NAME:-autotest-agent}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
DOCKER_REGISTRY="${DOCKER_REGISTRY:-}"
EXPORT=false
PUSH=false

# Parse arguments
for arg in "$@"; do
    case $arg in
        --export) EXPORT=true ;;
        --push) PUSH=true ;;
        --tag=*) IMAGE_TAG="${arg#*=}" ;;
        --registry=*) DOCKER_REGISTRY="${arg#*=}" ;;
    esac
done

FULL_IMAGE="${DOCKER_REGISTRY}${DOCKER_REGISTRY:+/}${IMAGE_NAME}:${IMAGE_TAG}"

echo "=== AutoTest-Agent Docker Image Builder ==="
echo "Image: ${FULL_IMAGE}"
echo ""

# ===== Step 1: Build =====
echo "[1/3] Building Docker image..."
docker build \
    --build-arg PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple \
    -t "${FULL_IMAGE}" \
    -f Dockerfile \
    .

echo "✅ Build complete: ${FULL_IMAGE}"

# ===== Step 2: Export (optional) =====
if [ "$EXPORT" = true ]; then
    OUTPUT_FILE="${IMAGE_NAME}-${IMAGE_TAG}.tar.gz"
    echo "[2/3] Exporting image to ${OUTPUT_FILE}..."
    docker save "${FULL_IMAGE}" | gzip > "${OUTPUT_FILE}"
    echo "✅ Exported: ${OUTPUT_FILE} ($(du -h ${OUTPUT_FILE} | cut -f1))"
fi

# ===== Step 3: Push (optional) =====
if [ "$PUSH" = true ]; then
    echo "[3/3] Pushing image to registry..."
    docker push "${FULL_IMAGE}"
    echo "✅ Pushed: ${FULL_IMAGE}"
fi

# ===== Summary =====
echo ""
echo "=== Build Summary ==="
docker images "${FULL_IMAGE}" --format "Image: {{.Repository}}:{{.Tag}} | Size: {{.Size}} | Created: {{.CreatedAt}}"

echo ""
echo "Next steps:"
echo "  docker compose up -d            # Start AutoTest-Agent"
echo "  docker run -p 8080:8080 ${FULL_IMAGE}   # Run standalone"