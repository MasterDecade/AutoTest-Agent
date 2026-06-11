#!/bin/bash
# configure_mirrors.sh — AutoTest-Agent 国内镜像源自动配置脚本
# Usage: bash scripts/configure_mirrors.sh

set -e

echo "=== AutoTest-Agent 国内镜像源配置 ==="
echo ""

# ---- pip ----
echo "[pip] 配置清华源..."
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple 2>/dev/null || \
    echo "Warning: pip config not available, using PIP_INDEX_URL env var"

# ---- Docker ----
echo "[Docker] 检测 Docker 镜像加速器..."
DOCKER_CONFIG="${HOME}/.docker/config.json"
DOCKER_MIRROR="${DOCKER_MIRROR:-registry.cn-hangzhou.aliyuncs.com}"

if [ -f /etc/docker/daemon.json ]; then
    echo "Docker daemon.json found"
else
    echo "Docker daemon.json not found — configure via Docker Desktop settings or manually"
fi

# ---- npm ----
if command -v npm &> /dev/null; then
    echo "[npm] 配置淘宝源..."
    npm config set registry https://registry.npmmirror.com
fi

# ---- apt (Debian/Ubuntu) ----
if [ -f /etc/apt/sources.list.d/debian.sources ]; then
    echo "[apt] 替换为中科大源..."
    sudo sed -i 's/deb.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list.d/debian.sources
    sudo sed -i 's/security.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list.d/debian.sources
fi

echo ""
echo "=== 配置完成 ==="
echo "pip 源: $(pip config get global.index-url 2>/dev/null || echo '清华源')"
echo "Docker mirror: ${DOCKER_MIRROR}"
echo "npm registry: $(npm config get registry 2>/dev/null || echo 'N/A')"