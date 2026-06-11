# WSL2 + Docker Desktop 网络配置指南

## 问题说明

在 WSL2 环境中使用 Docker Desktop 时，可能会遇到以下问题：

1. **Docker Hub 连接超时**：`registry-1.docker.io` 无法访问
2. **国内镜像源 DNS 解析失败**：部分镜像源域名无法解析
3. **构建镜像失败**：基础镜像拉取超时

## 解决方案

### 方案 1：配置 Docker Desktop 代理（推荐）

1. **打开 Docker Desktop 设置**
   - 在 Windows 端打开 Docker Desktop
   - 点击右上角齿轮图标进入设置

2. **配置代理**
   - 进入 `Settings` -> `Resources` -> `Proxies`
   - 启用 `Manual proxy configuration`
   - 配置 HTTP 和 HTTPS 代理（使用你的代理服务器）

3. **配置镜像加速器**
   - 进入 `Settings` -> `Docker Engine`
   - 添加以下配置：
   ```json
   {
     "registry-mirrors": [
       "https://docker.m.daocloud.io",
       "https://huecker.io",
       "https://dockerhub.timeweb.cloud",
       "https://noohub.ru"
     ]
   }
   ```
   - 点击 `Apply & Restart`

4. **验证配置**
   ```bash
   docker info | grep -A 5 "Registry Mirrors"
   ```

### 方案 2：使用 Windows 端的 Docker CLI

如果你已经在 Windows 端配置了代理，可以直接在 Windows PowerShell 中运行测试：

```powershell
cd C:\path\to\AutoTest-Agent
bash scripts/test.sh unit --verbose
```

### 方案 3：使用原生 Linux Docker（需要重新安装）

如果你有访问 Linux 服务器的权限，可以安装原生 Docker Engine：

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com | bash -s docker --mirror Aliyun

# 配置 Docker daemon
sudo mkdir -p /etc/docker
sudo tee /etc/docker/daemon.json <<EOF
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://huecker.io"
  ]
}
EOF

sudo systemctl restart docker
```

## 代码层面的改进

本项目已经完成了以下网络优化：

### 1. 多层回退策略

`src/sandbox/manager.py` 中的 `_ensure_image()` 方法实现了 5 层回退：

1. 检查本地缓存
2. 尝试直接拉取（如果 Docker daemon 已配置镜像则成功）
3. 使用用户配置的镜像（DOCKER_MIRROR 环境变量）
4. 依次尝试默认镜像列表（阿里云、中科大、腾讯云、网易）
5. 所有尝试失败后抛出包含详细解决方案的错误信息

### 2. 可配置的镜像源

通过环境变量配置所有镜像源：

```bash
# .env 文件
DOCKER_MIRROR=registry.cn-hangzhou.aliyuncs.com
PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
NPM_REGISTRY=https://registry.npmmirror.com
```

### 3. 自动化配置脚本

运行 `scripts/configure_mirrors.sh` 自动配置：

```bash
# 自动检测最快的镜像源并配置
bash scripts/configure_mirrors.sh

# 强制重新配置
bash scripts/configure_mirrors.sh --force

# 仅测试连通性
bash scripts/configure_mirrors.sh --test
```

## 测试验证

### 静态代码验证

```bash
python3 scripts/verify_network_fixes.py
```

这会执行 27 项检查，确保所有网络配置都正确。

### Docker 化测试

在正确配置 Docker Desktop 后，运行：

```bash
# 单元测试
bash scripts/test.sh unit --verbose

# 集成测试
bash scripts/test.sh integration --verbose

# 沙箱测试
bash scripts/test.sh sandbox --verbose

# 所有测试 + 覆盖率报告
bash scripts/test.sh all --coverage
```

## 常见问题

### Q: 为什么国内镜像源都无法访问？

A: 这可能是因为：
1. 镜像源服务已停止（如网易 hub-mirror.c.163.com 已不可用）
2. 防火墙或网络策略阻止访问
3. DNS 解析问题

### Q: 哪些镜像源目前可用？

A: 根据最新测试（2024年）：
- ✅ `docker.m.daocloud.io` - DaoCloud（推荐）
- ✅ `huecker.io` - Huecker（推荐）
- ✅ `dockerhub.timeweb.cloud` - TimeWeb（推荐）
- ⚠️ `registry.cn-hangzhou.aliyuncs.com` - 阿里云（需要登录）
- ❌ `docker.mirrors.ustc.edu.cn` - 中科大（已停止服务）
- ❌ `hub-mirror.c.163.com` - 网易（已停止服务）

### Q: 如何找到可用的镜像源？

A: 运行自动检测脚本：
```bash
bash scripts/configure_mirrors.sh --test
```

或者手动测试：
```bash
curl -fs --max-time 5 https://YOUR-MIRROR/v2/ && echo "OK" || echo "FAIL"
```

## 参考资源

- [Docker Desktop 官方文档](https://docs.docker.com/desktop/)
- [DaoCloud 镜像服务](https://www.daocloud.io/)
- [项目网络优化文档](./network_optimization.md)
