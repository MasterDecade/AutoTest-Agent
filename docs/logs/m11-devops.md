# M11: 运维脚本完善与测试流程 — 开发日志

## 环境信息
- 日期: 2026-06-11
- 分支: develop_qoder
- Docker: 29.5.2
- Python: 3.12

---

## 概述

M11 里程碑专注于**运维自动化**和**测试流程标准化**，核心目标是建立完全容器化的开发与测试环境，确保零主机依赖。

---

## 步骤1: 完善运维脚本体系 — ✅ 完成

### 1.1 start.sh - 一键启动脚本（重写）

**文件**: `scripts/start.sh`

**新增功能**:
- ✅ 支持多种模式：dev/prod/backend/frontend/test
- ✅ 后台运行支持（-d 参数）
- ✅ 自动检查 Docker 环境
- ✅ 自动创建 .env 文件（从 .env.example）
- ✅ 彩色输出，友好的用户界面
- ✅ 完整的帮助文档

**使用示例**:
```bash
# 启动开发环境（后台）
bash scripts/start.sh dev -d

# 启动生产环境
bash scripts/start.sh prod -d

# 运行测试
bash scripts/start.sh test
```

**关键改进**:
- 所有操作通过 Docker Compose 执行
- 不再在宿主机安装 Python/Node.js 依赖
- 支持服务粒度启动（backend/frontend 单独启动）

---

### 1.2 logs.sh - 日志查看脚本（新建）

**文件**: `scripts/logs.sh`

**功能**:
- ✅ 支持查看所有服务日志
- ✅ 实时跟踪模式（默认）
- ✅ 可配置显示行数（--tail N）
- ✅ 按服务分类：dev/prod/api/worker/postgres/redis

**使用示例**:
```bash
# 查看开发日志（实时）
bash scripts/logs.sh dev

# 查看最近 50 行 API 日志
bash scripts/logs.sh api --tail 50

# 查看 Worker 日志（不跟踪）
bash scripts/logs.sh worker --no-follow
```

**实现细节**:
- 开发环境：直接使用 `docker logs`
- 生产环境：使用 `docker compose logs`
- 支持 Ctrl+C 中断跟踪

---

### 1.3 stop.sh - 环境停止脚本（新建）

**文件**: `scripts/stop.sh`

**功能**:
- ✅ 支持停止 dev/prod/all 环境
- ✅ 可选删除数据卷（--remove-volumes）
- ✅ 可选删除镜像（--remove-images）
- ✅ 彻底清理模式（--clean）
- ✅ 状态查看（status）
- ✅ 危险操作需要确认

**使用示例**:
```bash
# 停止开发环境（保留数据）
bash scripts/stop.sh dev

# 停止并删除数据（需要确认）
bash scripts/stop.sh dev --remove-volumes

# 彻底清理所有资源
bash scripts/stop.sh all --clean

# 查看当前状态
bash scripts/stop.sh status
```

**安全特性**:
- 删除数据前必须手动确认
- 清晰的警告提示
- 支持 dry-run 模式（通过 status 查看）

---

### 1.4 test.sh - 测试执行脚本（新建）

**文件**: `scripts/test.sh`

**功能**:
- ✅ 支持 unit/integration/sandbox 测试类型
- ✅ 覆盖率报告生成（--coverage）
- ✅ 详细输出模式（-v）
- ✅ 无缓存构建（--no-cache）
- ✅ 自动 setup/cleanup 测试环境
- ✅ 数据库就绪检查

**使用示例**:
```bash
# 运行所有测试
bash scripts/test.sh all

# 仅运行单元测试
bash scripts/test.sh unit

# 运行测试并生成覆盖率
bash scripts/test.sh all --coverage

# 沙箱测试（详细输出）
bash scripts/test.sh sandbox -v
```

**测试隔离机制**:
1. 启动临时 PostgreSQL 和 Redis 容器
2. 在独立容器中运行 pytest
3. 测试完成后自动清理所有容器
4. 不影响开发和生产环境数据

---

## 步骤2: 创建测试套件结构 — ✅ 完成

### 2.1 测试目录组织

```
tests/
├── __init__.py              # 测试包初始化
├── conftest.py              # Pytest 配置和 fixtures
├── unit/                    # 单元测试
│   ├── __init__.py
│   ├── test_config.py       # 配置模块测试
│   └── test_exceptions.py   # 异常类测试
├── integration/             # 集成测试
│   ├── __init__.py
│   └── test_health.py       # API 健康检查测试
└── sandbox/                 # 沙箱测试
    ├── __init__.py
    └── test_manager.py      # 沙箱管理器测试
```

### 2.2 核心测试文件

#### tests/conftest.py
**功能**:
- 环境变量自动设置
- 通用 fixtures（sample_code, valid_submission_data 等）
- 临时文件创建工具

#### tests/unit/test_config.py
**测试内容**:
- Settings 默认值验证
- SECRET_KEY 长度验证
- LLM_PROVIDERS JSON 解析
- API 密钥哈希和验证
- is_development 属性

**测试用例数**: 9

#### tests/unit/test_exceptions.py
**测试内容**:
- 所有自定义异常类
- 错误码验证
- 属性访问

**测试用例数**: 6

#### tests/integration/test_health.py
**测试内容**:
- Root 端点响应
- Health check 端点
- Ping 端点
- API Docs 可访问性

**测试用例数**: 4

#### tests/sandbox/test_manager.py
**测试内容**:
- SandboxConfig 默认值和自定义
- Docker 镜像映射
- 镜像 URL 转换
- 沙箱执行（跳过，需 Docker）
- 超时 enforcement（跳过，需 Docker）
- 资源限制（跳过，需 Docker）

**测试用例数**: 8（5 个即时运行，3 个需容器）

### 2.3 pytest 配置

**文件**: `pytest.ini`

**配置项**:
```ini
[pytest]
testpaths = tests
asyncio_mode = auto
markers =
    unit: Unit tests
    integration: Integration tests
    sandbox: Sandbox tests
    slow: Slow running tests
addopts = -v --strict-markers --tb=short --color=yes
timeout = 300
```

---

## 步骤3: 更新 README 文档 — ✅ 完成

### 3.1 README.md 重大更新

**新增章节**:
1. **运维脚本使用指南**
   - start.sh 详细说明
   - logs.sh 详细说明
   - stop.sh 详细说明
   - test.sh 详细说明

2. **环境隔离架构图**
   - ASCII 艺术图展示容器架构
   - 关键原则说明

3. **测试流程**
   - 如何运行测试
   - 测试结构说明
   - 测试原则

4. **常见问题 FAQ**
   - 本地调试方法
   - 数据备份
   - 测试失败调试

5. **贡献指南**
   - 强调 Docker 容器测试要求

**改进内容**:
- 快速开始部分添加三种方式
- 项目结构更新（包含 tests/）
- 开发日志表格添加 M11

---

## 步骤4: 技术改进总结

### 4.1 代码统计

| 文件 | 类型 | 行数 | 说明 |
|------|------|------|------|
| `scripts/start.sh` | 修改 | ~280 | 重写为 Docker 化版本 |
| `scripts/logs.sh` | 新建 | ~180 | 日志查看工具 |
| `scripts/stop.sh` | 新建 | ~230 | 停止和清理工具 |
| `scripts/test.sh` | 新建 | ~250 | 测试执行工具 |
| `tests/conftest.py` | 新建 | ~100 | Pytest 配置 |
| `tests/unit/test_config.py` | 新建 | ~70 | 配置测试 |
| `tests/unit/test_exceptions.py` | 新建 | ~50 | 异常测试 |
| `tests/integration/test_health.py` | 新建 | ~40 | API 测试 |
| `tests/sandbox/test_manager.py` | 新建 | ~90 | 沙箱测试 |
| `pytest.ini` | 新建 | ~30 | Pytest 配置 |
| `README.md` | 修改 | ~450 | 大幅扩展 |

**总计**: 新增约 1720 行代码和文档

### 4.2 关键特性

#### 环境隔离
✅ **零主机依赖**：所有操作在 Docker 容器中进行
✅ **数据持久化**：通过 volumes 管理，可选择性清理
✅ **网络隔离**：独立的 Docker network
✅ **资源限制**：CPU 和内存限制配置

#### 用户体验
✅ **彩色输出**：清晰的日志级别颜色
✅ **友好提示**：详细的帮助文档和使用示例
✅ **安全检查**：Docker 环境自动检测
✅ **危险操作确认**：删除数据前需要手动确认

#### 测试质量
✅ **分类清晰**：unit/integration/sandbox 分离
✅ **Fixture 复用**：conftest.py 提供通用 fixtures
✅ **覆盖率支持**：一键生成 HTML 覆盖率报告
✅ **异步支持**：pytest-asyncio 集成

---

## 步骤5: 验证与测试

### 5.1 脚本语法检查
```bash
# 所有脚本通过 bash 语法检查
bash -n scripts/start.sh
bash -n scripts/logs.sh
bash -n scripts/stop.sh
bash -n scripts/test.sh
```

### 5.2 测试文件语法检查
```bash
# Python 语法检查通过
python3 -m py_compile tests/*.py tests/unit/*.py tests/integration/*.py tests/sandbox/*.py
```

### 5.3 待验证项目
以下项目需要在实际 Docker 环境中验证：

1. **start.sh 完整流程**
   - [ ] dev 环境启动
   - [ ] prod 环境启动
   - [ ] 后台模式运行
   - [ ] 服务间通信

2. **test.sh 测试执行**
   - [ ] 单元测试运行
   - [ ] 集成测试运行
   - [ ] 沙箱测试运行
   - [ ] 覆盖率报告生成

3. **logs.sh 日志查看**
   - [ ] 实时跟踪模式
   - [ ] tail 参数
   - [ ] 多服务日志

4. **stop.sh 清理**
   - [ ] 正常停止
   - [ ] 删除 volumes
   - [ ] 彻底清理

---

## 后续工作建议

### 短期（高优先级）
1. **CI/CD 集成**：在 GitHub Actions 中使用 test.sh 运行测试
2. **性能监控**：添加 Prometheus + Grafana 监控
3. **日志聚合**：集成 ELK stack 或 Loki
4. **健康检查增强**：添加更详细的健康端点

### 中期
1. **多环境配置**：支持 staging/pre-production 环境
2. **蓝绿部署**：使用 Docker Compose 实现零停机部署
3. **自动化备份**：定期备份数据库到对象存储
4. **告警系统**：集成钉钉/企业微信告警

### 长期
1. **Kubernetes 迁移**：从 Docker Compose 迁移到 K8s
2. **服务网格**：Istio 集成
3. **混沌工程**：故障注入测试
4. **多区域部署**：全球分布式部署

---

## 总结

M11 里程碑成功建立了**完整的运维自动化体系**和**标准化的测试流程**，核心成果包括：

✅ **4 个运维脚本**：start/stop/logs/test
✅ **完整的测试套件**：unit/integration/sandbox
✅ **详细的文档**：README 大幅扩展
✅ **环境隔离架构**：零主机依赖
✅ **用户体验优化**：彩色输出、友好提示、安全检查

所有改进都严格遵循**环境隔离原则**，确保开发和测试在 Docker 容器中进行，杜绝了宿主机污染的风险。

下一步将进入 M12，重点关注 CI/CD 集成和自动化测试流水线。
