#!/bin/bash
# configure_mirrors.sh — AutoTest-Agent 国内镜像源自动配置脚本
# Usage: bash scripts/configure_mirrors.sh [--force] [--test]
#
# Options:
#   --force   Force reconfiguration even if already configured
#   --test    Test connectivity after configuration
#
# This script configures:
# - pip (Python package manager) → Tsinghua/Alibaba mirrors
# - npm (Node.js package manager) → Taobao mirror
# - Docker daemon → Alibaba/USTC/Tencent mirrors
# - APT (Debian/Ubuntu) → USTC mirrors
# - Cargo (Rust) → Tsinghua mirror (if available)

set -e

# ===== Configuration =====
FORCE=false
TEST_CONNECTIVITY=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --force)
            FORCE=true
            shift
            ;;
        --test)
            TEST_CONNECTIVITY=true
            shift
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

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_section() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

test_url() {
    local url=$1
    local timeout=${2:-5}

    if curl -fs --max-time "$timeout" "$url" > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# ===== Main Configuration =====
log_section "AutoTest-Agent 国内镜像源配置"

# ---- pip Configuration ----
configure_pip() {
    log_info "[pip] 配置 Python 包管理器镜像源..."

    local pip_config_dir="${HOME}/.config/pip"
    local pip_config_file="${pip_config_dir}/pip.conf"

    mkdir -p "$pip_config_dir"

    # Check if already configured
    if [ -f "$pip_config_file" ] && [ "$FORCE" = false ]; then
        if grep -q "pypi.tuna.tsinghua.edu.cn" "$pip_config_file" || \
           grep -q "mirrors.aliyun.com/pypi" "$pip_config_file"; then
            log_warn "pip 已配置国内镜像源，跳过（使用 --force 强制重新配置）"
            return 0
        fi
    fi

    # Backup existing config
    if [ -f "$pip_config_file" ]; then
        cp "$pip_config_file" "${pip_config_file}.bak.$(date +%Y%m%d%H%M%S)"
        log_info "已备份原配置: ${pip_config_file}.bak.*"
    fi

    # Write new config with multiple fallback mirrors
    cat > "$pip_config_file" << 'EOF'
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
extra-index-url =
    https://mirrors.aliyun.com/pypi/simple/
    https://pypi.org/simple
trusted-host =
    pypi.tuna.tsinghua.edu.cn
    mirrors.aliyun.com
    pypi.org
timeout = 60
retries = 3
EOF

    log_success "pip 镜像源已配置: 清华源 (主) + 阿里云 (备)"

    # Verify configuration
    if command -v pip &> /dev/null; then
        local current_url=$(pip config get global.index-url 2>/dev/null || echo "未设置")
        log_info "当前 pip 源: $current_url"
    fi
}

# ---- Docker Configuration ----
configure_docker() {
    log_info "[Docker] 配置 Docker 镜像加速器..."

    local docker_daemon="/etc/docker/daemon.json"
    local docker_config_json="${HOME}/.docker/config.json"
    local docker_mirror="${DOCKER_MIRROR:-registry.cn-hangzhou.aliyuncs.com}"

    # Available mirrors for testing
    local mirrors=(
        "registry.cn-hangzhou.aliyuncs.com"
        "docker.mirrors.ustc.edu.cn"
        "mirror.ccs.tencentyun.com"
        "hub-mirror.c.163.com"
    )

    # Test and select fastest mirror if DOCKER_MIRROR not set
    if [ -z "$DOCKER_MIRROR" ] || [ "$DOCKER_MIRROR" = "auto" ]; then
        log_info "自动检测最快的 Docker 镜像源..."
        for mirror in "${mirrors[@]}"; do
            if test_url "https://${mirror}/v2/" 5; then
                docker_mirror="$mirror"
                log_success "检测到可用镜像: $mirror"
                break
            fi
        done
    fi

    # Configure daemon.json (Linux Docker Engine)
    if [ -w "/etc/docker" ] || [ "$(id -u)" -eq 0 ]; then
        if [ -f "$docker_daemon" ] && [ "$FORCE" = false ]; then
            if grep -q "registry-mirrors" "$docker_daemon"; then
                log_warn "Docker daemon.json 已配置镜像加速器，跳过（使用 --force 强制重新配置）"
                return 0
            fi
        fi

        # Create or update daemon.json
        if [ -f "$docker_daemon" ]; then
            # Backup existing config
            cp "$docker_daemon" "${docker_daemon}.bak.$(date +%Y%m%d%H%M%S)"
            log_info "已备份原配置: ${docker_daemon}.bak.*"

            # Use jq if available, otherwise use python
            if command -v jq &> /dev/null; then
                jq ".\"registry-mirrors\" = [\"https://${docker_mirror}\"]" "$docker_daemon" > "${docker_daemon}.tmp" && \
                    mv "${docker_daemon}.tmp" "$docker_daemon"
            elif command -v python3 &> /dev/null; then
                python3 -c "
import json
with open('$docker_daemon') as f:
    config = json.load(f)
config['registry-mirrors'] = ['https://${docker_mirror}']
with open('$docker_daemon', 'w') as f:
    json.dump(config, f, indent=2)
"
            else
                log_error "需要 jq 或 python3 来更新 JSON 配置"
                return 1
            fi
        else
            # Create new daemon.json
            cat > "$docker_daemon" << EOF
{
  "registry-mirrors": ["https://${docker_mirror}"],
  "live-restore": true
}
EOF
        fi

        log_success "Docker daemon.json 已配置: $docker_mirror"
        log_warn "请重启 Docker 服务使配置生效:"
        echo "  sudo systemctl restart docker"
    else
        log_warn "无权限修改 /etc/docker/daemon.json"
        log_info "如需配置 Docker 镜像加速器，请:"
        echo "  1. 打开 Docker Desktop 设置"
        echo "  2. 进入 Docker Engine 页面"
        echo "  3. 添加以下配置:"
        echo "     {"
        echo "       \"registry-mirrors\": [\"https://${docker_mirror}\"]"
        echo "     }"
    fi

    # Export for current session
    export DOCKER_MIRROR="$docker_mirror"
    log_info "当前会话 Docker 镜像: $docker_mirror"
}

# ---- npm Configuration ----
configure_npm() {
    if ! command -v npm &> /dev/null; then
        log_warn "npm 未安装，跳过配置"
        return 0
    fi

    log_info "[npm] 配置 Node.js 包管理器镜像源..."

    # Check if already configured
    local current_registry=$(npm config get registry 2>/dev/null || echo "")
    if [[ "$current_registry" == *"npmmirror.com"* ]] || [[ "$current_registry" == *"taobao.org"* ]]; then
        if [ "$FORCE" = false ]; then
            log_warn "npm 已配置国内镜像源，跳过（使用 --force 强制重新配置）"
            return 0
        fi
    fi

    # Set registry
    npm config set registry https://registry.npmmirror.com
    log_success "npm 镜像源已配置: 淘宝源 (npmmirror.com)"

    # Verify
    local new_registry=$(npm config get registry 2>/dev/null || echo "未设置")
    log_info "当前 npm 源: $new_registry"
}

# ---- APT Configuration (Debian/Ubuntu) ----
configure_apt() {
    if [ ! -f /etc/apt/sources.list.d/debian.sources ] && \
       [ ! -f /etc/apt/sources.list ] && \
       [ ! -f /etc/apt/sources.list.d/ubuntu.sources ]; then
        log_warn "APT 源配置文件不存在，跳过配置"
        return 0
    fi

    log_info "[APT] 配置系统包管理器镜像源..."

    # Only run if root or can use sudo
    if [ "$(id -u)" -ne 0 ]; then
        if ! command -v sudo &> /dev/null; then
            log_warn "非 root 用户且无 sudo，跳过 APT 配置"
            return 0
        fi
    fi

    local backup_suffix=".bak.$(date +%Y%m%d%H%M%S)"

    # Debian sources
    if [ -f /etc/apt/sources.list.d/debian.sources ]; then
        if grep -q "mirrors.ustc.edu.cn" /etc/apt/sources.list.d/debian.sources && [ "$FORCE" = false ]; then
            log_warn "Debian APT 源已配置为中科大镜像，跳过"
        else
            log_info "配置 Debian APT 源为中科大镜像..."
            sudo cp /etc/apt/sources.list.d/debian.sources "/etc/apt/sources.list.d/debian.sources${backup_suffix}"

            # Replace official repos with USTC mirrors
            sudo sed -i 's|https\?://deb\.debian\.org/debian|https://mirrors.ustc.edu.cn/debian|g' /etc/apt/sources.list.d/debian.sources
            sudo sed -i 's|https\?://security\.debian\.org/debian-security|https://mirrors.ustc.edu.cn/debian-security|g' /etc/apt/sources.list.d/debian.sources

            log_success "Debian APT 源已配置: 中科大镜像"
        fi
    fi

    # Ubuntu sources
    if [ -f /etc/apt/sources.list.d/ubuntu.sources ]; then
        if grep -q "mirrors.ustc.edu.cn" /etc/apt/sources.list.d/ubuntu.sources && [ "$FORCE" = false ]; then
            log_warn "Ubuntu APT 源已配置为中科大镜像，跳过"
        else
            log_info "配置 Ubuntu APT 源为中科大镜像..."
            sudo cp /etc/apt/sources.list.d/ubuntu.sources "/etc/apt/sources.list.d/ubuntu.sources${backup_suffix}"

            # Replace official repos with USTC mirrors
            sudo sed -i 's|https\?://archive\.ubuntu\.com/ubuntu|https://mirrors.ustc.edu.cn/ubuntu|g' /etc/apt/sources.list.d/ubuntu.sources
            sudo sed -i 's|https\?://security\.ubuntu\.com/ubuntu|https://mirrors.ustc.edu.cn/ubuntu|g' /etc/apt/sources.list.d/ubuntu.sources

            log_success "Ubuntu APT 源已配置: 中科大镜像"
        fi
    fi

    # Legacy sources.list
    if [ -f /etc/apt/sources.list ]; then
        if grep -q "mirrors.ustc.edu.cn" /etc/apt/sources.list && [ "$FORCE" = false ]; then
            log_warn "APT sources.list 已配置为中科大镜像，跳过"
        else
            log_info "配置传统 APT sources.list..."
            sudo cp /etc/apt/sources.list "/etc/apt/sources.list${backup_suffix}"

            # Detect distribution
            if grep -q "ubuntu.com" /etc/apt/sources.list; then
                # Ubuntu
                sudo sed -i 's|https\?://archive\.ubuntu\.com|https://mirrors.ustc.edu.cn|g' /etc/apt/sources.list
                sudo sed -i 's|https\?://security\.ubuntu\.com|https://mirrors.ustc.edu.cn|g' /etc/apt/sources.list
            elif grep -q "debian.org" /etc/apt/sources.list; then
                # Debian
                sudo sed -i 's|https\?://deb\.debian\.org|https://mirrors.ustc.edu.cn|g' /etc/apt/sources.list
                sudo sed -i 's|https\?://security\.debian\.org|https://mirrors.ustc.edu.cn|g' /etc/apt/sources.list
            fi

            log_success "APT sources.list 已配置: 中科大镜像"
        fi
    fi
}

# ---- Cargo Configuration (Rust) ----
configure_cargo() {
    if ! command -v cargo &> /dev/null; then
        log_warn "Cargo (Rust) 未安装，跳过配置"
        return 0
    fi

    log_info "[Cargo] 配置 Rust 包管理器镜像源..."

    local cargo_config_dir="${HOME}/.cargo"
    local cargo_config_file="${cargo_config_dir}/config.toml"

    mkdir -p "$cargo_config_dir"

    # Check if already configured
    if [ -f "$cargo_config_file" ] && [ "$FORCE" = false ]; then
        if grep -q "tuna.tsinghua.edu.cn/crates" "$cargo_config_file" || \
           grep -q "mirrors.ustc.edu.cn/crates" "$cargo_config_file"; then
            log_warn "Cargo 已配置国内镜像源，跳过（使用 --force 强制重新配置）"
            return 0
        fi
    fi

    # Backup existing config
    if [ -f "$cargo_config_file" ]; then
        cp "$cargo_config_file" "${cargo_config_file}.bak.$(date +%Y%m%d%H%M%S)"
        log_info "已备份原配置: ${cargo_config_file}.bak.*"
    fi

    # Write new config
    cat > "$cargo_config_file" << 'EOF'
[source.crates-io]
replace-with = 'tuna'

[source.tuna]
registry = "https://mirrors.tuna.tsinghua.edu.cn/git/crates.io-index.git"

[net]
retry = 3
timeout = 60
EOF

    log_success "Cargo 镜像源已配置: 清华源"
}

# ---- Test Connectivity ----
test_connectivity() {
    log_section "测试网络连接"

    local all_passed=true

    # Test pip
    log_info "测试 pip 镜像源连通性..."
    if test_url "https://pypi.tuna.tsinghua.edu.cn/simple/" 5; then
        log_success "✓ pip 清华源可达"
    else
        log_error "✗ pip 清华源不可达，尝试阿里云..."
        if test_url "https://mirrors.aliyun.com/pypi/simple/" 5; then
            log_success "✓ pip 阿里云源可达"
        else
            log_error "✗ pip 所有镜像源均不可达"
            all_passed=false
        fi
    fi

    # Test npm
    log_info "测试 npm 镜像源连通性..."
    if test_url "https://registry.npmmirror.com/" 5; then
        log_success "✓ npm 淘宝源可达"
    else
        log_error "✗ npm 淘宝源不可达"
        all_passed=false
    fi

    # Test Docker mirrors
    log_info "测试 Docker 镜像源连通性..."
    local docker_mirrors=(
        "registry.cn-hangzhou.aliyuncs.com"
        "docker.mirrors.ustc.edu.cn"
        "mirror.ccs.tencentyun.com"
    )

    local docker_ok=false
    for mirror in "${docker_mirrors[@]}"; do
        if test_url "https://${mirror}/v2/" 5; then
            log_success "✓ Docker 镜像 ${mirror} 可达"
            docker_ok=true
            break
        fi
    done

    if [ "$docker_ok" = false ]; then
        log_error "✗ 所有 Docker 镜像源均不可达"
        all_passed=false
    fi

    # Summary
    echo ""
    if [ "$all_passed" = true ]; then
        log_success "所有镜像源连通性测试通过！"
    else
        log_warn "部分镜像源不可达，请检查网络连接或防火墙设置"
    fi
}

# ===== Main Execution =====
main() {
    configure_pip
    configure_docker
    configure_npm
    configure_apt
    configure_cargo

    echo ""
    log_success "镜像源配置完成！"
    echo ""
    log_info "配置摘要:"
    echo "  • pip: 清华源 (主) + 阿里云 (备)"
    echo "  • npm: 淘宝源 (npmmirror.com)"
    echo "  • Docker: ${DOCKER_MIRROR:-registry.cn-hangzhou.aliyuncs.com}"
    echo "  • APT: 中科大镜像"
    echo "  • Cargo: 清华源"
    echo ""
    log_warn "注意: Docker 配置需要重启服务才能生效"
    echo "  sudo systemctl restart docker"
    echo ""

    # Test connectivity if requested
    if [ "$TEST_CONNECTIVITY" = true ]; then
        test_connectivity
    fi
}

main