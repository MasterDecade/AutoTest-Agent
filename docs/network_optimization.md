# 中国大陆网络环境优化指南

本文档说明 AutoTest-Agent 项目针对中国大陆网络环境的优化配置和使用方法。

## 目录

- [概述](#概述)
- [镜像源配置](#镜像源配置)
- [Docker 镜像加速](#docker-镜像加速)
- [故障排查](#故障排查)
- [测试验证](#测试验证)

## 概述

AutoTest-Agent 项目已针对中国大陆网络环境进行了全面优化，包括：

1. **Python 包管理** - 使用清华大学/阿里云 PyPI 镜像
2. **Node.js 包管理** - 使用淘宝 npm 镜像
3. **Docker 镜像** - 多层镜像回退策略（阿里云、中科大、腾讯云、网易）
4. **系统包管理** - 使用中科大 APT 镜像
5. **Rust Cargo** - 使用清华大学 crates.io 镜像

## 镜像源配置

### 自动配置脚本

运行以下命令自动配置所有镜像源：

```bash
bash scripts/configure_mirrors.sh
```

**选项：**

- `--force` - 强制重新配置（即使已配置）
- `--test` - 配置后测试连通性

**示例：**

```bash
# 配置并测试连通性
bash scripts/configure_mirrors.sh --test

# 强制重新配置
bash scripts/configure_mirrors.sh --force
```

### 手动配置

#### 1. pip (Python)

编辑 `~/.config/pip/pip.conf`：

```ini
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
```

#### 2. npm (Node.js)

```bash
npm config set registry https://registry.npmmirror.com
```

#### 3. Docker

编辑 `/etc/docker/daemon.json`：

```json
{
  "registry-mirrors": ["https://registry.cn-hangzhou.aliyuncs.com"],
  "live-restore": true
}
```

重启 Docker：

```bash
sudo systemctl restart docker
```

#### 4. 环境变量

复制 `.env.example` 到 `.env`：

```bash
cp .env.example .env
```

关键配置项：

```env
DOCKER_MIRROR=registry.cn-hangzhou.aliyuncs.com
PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
NPM_REGISTRY=https://registry.npmmirror.com
```

## Docker 镜像加速

### 支持的镜像源

项目内置支持以下 Docker 镜像加速器（按优先级）：

1. **阿里云** - `registry.cn-hangzhou.aliyuncs.com` （默认）
2. **中科大** - `docker.mirrors.ustc.edu.cn`
3. **腾讯云** - `mirror.ccs.tencentyun.com`
4. **网易** - `hub-mirror.c.163.com`

### 智能回退策略

当拉取 Docker 镜像时，系统会按以下顺序尝试：

1. **本地缓存** - 检查是否已有镜像
2. **直接拉取** - 尝试官方仓库（如果 Docker daemon 已配置镜像则成功）
3. **配置的镜像** - 使用 `DOCKER_MIRROR` 环境变量指定的镜像
4. **默认镜像列表** - 依次尝试阿里云、中科大、腾讯云、网易镜像
5. **错误提示** - 所有尝试失败后提供详细的解决方案

### 示例代码

```python
from src.sandbox.manager import SandboxManager

# 使用默认镜像（阿里云）
manager = SandboxManager()

# 或指定自定义镜像
manager = SandboxManager(mirror="docker.mirrors.ustc.edu.cn")

# 创建沙箱时自动处理镜像拉取
result = await manager.create_and_run(config)
```

## 故障排查

### 问题 1: Docker 镜像拉取超时

**症状：**

```
Failed to pull image 'python:3.11-slim': Connection timeout
```

**解决方案：**

1. 运行镜像源配置脚本：
   ```bash
   bash scripts/configure_mirrors.sh --test
   ```

2. 手动测试镜像连通性：
   ```bash
   curl -fs --max-time 5 https://registry.cn-hangzhou.aliyuncs.com/v2/
   ```

3. 检查 Docker daemon 配置：
   ```bash
   cat /etc/docker/daemon.json
   ```

4. 重启 Docker 服务：
   ```bash
   sudo systemctl restart docker
   ```

### 问题 2: pip 安装依赖失败

**症状：**

```
Could not connect to pypi.org
```

**解决方案：**

1. 设置 pip 镜像：
   ```bash
   export PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
   ```

2. 或在 `.env` 文件中配置：
   ```env
   PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
   ```

3. 测试连通性：
   ```bash
   curl -fs https://pypi.tuna.tsinghua.edu.cn/simple/ | head
   ```

### 问题 3: npm 安装包失败

**症状：**

```
npm ERR! network request to https://registry.npmjs.org failed
```

**解决方案：**

1. 设置淘宝镜像：
   ```bash
   npm config set registry https://registry.npmmirror.com
   ```

2. 验证配置：
   ```bash
   npm config get registry
   ```

### 问题 4: APT 更新失败

**症状：**

```
Err:1 http://deb.debian.org/debian bookworm InRelease
```

**解决方案：**

运行配置脚本自动替换为中科大镜像：

```bash
bash scripts/configure_mirrors.sh
```

或手动编辑 `/etc/apt/sources.list`，将 `deb.debian.org` 替换为 `mirrors.ustc.edu.cn`。

## 测试验证

### 单元测试

运行网络配置相关测试：

```bash
bash scripts/test.sh unit
```

测试覆盖：

- `tests/unit/test_network_config.py` - 网络配置单元测试
- `tests/integration/test_mirror_connectivity.py` - 镜像连通性集成测试
- `tests/sandbox/test_mirror_pull.py` - 沙箱镜像拉取测试

### 验证脚本

运行综合验证脚本：

```bash
python3 scripts/verify_network_fixes.py
```

该脚本检查：

- ✓ 镜像源配置脚本完整性
- ✓ SandboxManager 回退策略实现
- ✓ Docker Compose 环境变量支持
- ✓ Dockerfile 构建参数配置
- ✓ 测试脚本使用配置的镜像
- ✓ 测试文件覆盖率
- ✓ 环境配置文件完整性

### 完整测试流程

```bash
# 1. 配置镜像源
bash scripts/configure_mirrors.sh --test

# 2. 验证配置
python3 scripts/verify_network_fixes.py

# 3. 运行完整测试套件
bash scripts/test.sh all --coverage

# 4. 查看测试报告
xdg-open coverage/index.html
```

## 架构说明

### 镜像拉取流程图

```
开始
  ↓
检查本地缓存
  ↓ 找到 → 直接使用
  ↓ 未找到
尝试直接拉取
  ↓ 成功 → 完成
  ↓ 失败
尝试配置的镜像 (DOCKER_MIRROR)
  ↓ 成功 → 标记为原名 → 完成
  ↓ 失败
尝试阿里云镜像
  ↓ 成功 → 标记为原名 → 完成
  ↓ 失败
尝试中科大镜像
  ↓ 成功 → 标记为原名 → 完成
  ↓ 失败
尝试腾讯云镜像
  ↓ 成功 → 标记为原名 → 完成
  ↓ 失败
尝试网易镜像
  ↓ 成功 → 标记为原名 → 完成
  ↓ 失败
抛出详细错误信息（包含解决方案）
```

### 关键组件

1. **SandboxManager._ensure_image()** - 核心镜像确保方法
   - 位置：`src/sandbox/manager.py`
   - 功能：实现多层回退策略

2. **SandboxManager._mirror_image()** - 镜像名称转换
   - 位置：`src/sandbox/manager.py`
   - 功能：将原始镜像名转换为镜像加速器地址

3. **configure_mirrors.sh** - 自动配置脚本
   - 位置：`scripts/configure_mirrors.sh`
   - 功能：一键配置所有镜像源

4. **环境变量配置**
   - 位置：`.env.example`, `docker-compose.dev.yml`
   - 功能：通过环境变量传递镜像配置

## 最佳实践

1. **首次设置时运行配置脚本**
   ```bash
   bash scripts/configure_mirrors.sh --test
   ```

2. **在 CI/CD 环境中使用环境变量**
   ```yaml
   environment:
     DOCKER_MIRROR: registry.cn-hangzhou.aliyuncs.com
     PIP_INDEX_URL: https://pypi.tuna.tsinghua.edu.cn/simple
   ```

3. **定期测试镜像连通性**
   ```bash
   bash scripts/configure_mirrors.sh --test
   ```

4. **生产环境使用专用镜像仓库**
   - 考虑搭建私有 Docker Registry
   - 使用企业级镜像加速器

## 参考资源

- [清华大学开源软件镜像站](https://mirrors.tuna.tsinghua.edu.cn/)
- [中科大开源镜像站](http://mirrors.ustc.edu.cn/)
- [阿里云容器镜像服务](https://cr.console.aliyun.com/)
- [Docker 官方文档 - 配置镜像加速器](https://docs.docker.com/registry/recipes/mirror/)
