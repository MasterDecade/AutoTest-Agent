# AutoTest-Agent

AI-powered automated code testing agent supporting Python, C/C++, and Java.

**AutoTest-Agent** 是一个基于 LLM 的智能代码检测与自动化测试平台，面向学校教育和企业外包场景，支持多语言代码的自动分析、测试用例生成、隔离化测试执行和评分对比。

---

## 功能特性

- 🔍 **多语言代码分析** — Python/C++/Java 静态分析
- 🤖 **AI 测试用例生成** — LLM 驱动的测试用例生成与扩写
- 📋 **检测计划审核** — 文档分析 → 生成计划 → 人工审核 → 执行
- 🐳 **Docker 沙箱执行** — 隔离运行，安全可控
- 📊 **评分对比看板** — 多维度评分 + 雷达图 + 排名
- ⚡ **批量并发处理** — 自适应并发 + 优先级队列
- 🌏 **国内网络适配** — Docker/pip/npm 镜像源自动配置
- 🔒 **环境隔离架构** — 所有操作在容器中进行，零主机依赖

---

## 快速开始

### 方式一：Docker Compose（推荐，完全隔离）

```bash
git clone git@github.com:MasterDecade/AutoTest-Agent.git
cd AutoTest-Agent
cp .env.example .env   # 编辑 .env 填入 API Key

# 启动开发环境
bash scripts/start.sh dev -d

# 查看服务状态
bash scripts/stop.sh status

# 查看日志
bash scripts/logs.sh dev
```

访问：
- Web UI: http://localhost:3000
- API 文档: http://localhost:8080/api/docs
- API 地址: http://localhost:8080/api

### 方式二：一键管理脚本（全新）

```bash
# 启动开发环境
bash scripts/start.sh dev -d

# 查看实时日志
bash scripts/logs.sh dev

# 停止服务
bash scripts/stop.sh dev

# 运行测试（完全隔离）
bash scripts/test.sh all --coverage

# 清理所有资源
bash scripts/stop.sh all --clean
```

### 方式三：生产环境部署

```bash
# 启动生产环境
bash scripts/start.sh prod -d

# 扩展 Worker 数量
docker compose -f docker-compose.yml up -d --scale worker=3

# 查看生产日志
bash scripts/logs.sh prod
```

---

## 运维脚本使用指南

项目提供了一套完整的运维脚本，所有操作均通过 Docker 容器执行，**严禁在本地主机安装依赖或运行服务**。

### 1. start.sh - 一键启动

```bash
bash scripts/start.sh [mode] [-d]

Modes:
  dev       - 启动开发环境（默认）
  prod      - 启动生产环境
  backend   - 仅启动后端服务
  frontend  - 仅启动前端服务
  test      - 运行测试套件

Options:
  -d        - 后台运行（detached mode）

Examples:
  bash scripts/start.sh dev           # 前台启动开发环境
  bash scripts/start.sh dev -d        # 后台启动开发环境
  bash scripts/start.sh prod -d       # 后台启动生产环境
  bash scripts/start.sh test          # 运行测试
```

### 2. logs.sh - 日志查看

```bash
bash scripts/logs.sh [service] [--tail N]

Services:
  dev       - 开发容器日志
  prod      - 所有生产服务日志
  api       - API 服务器日志
  worker    - Celery Worker 日志
  postgres  - PostgreSQL 日志
  redis     - Redis 日志

Options:
  -f        - 实时跟踪（默认）
  --tail N  - 显示最后 N 行（默认 100）

Examples:
  bash scripts/logs.sh dev                  # 查看开发日志（跟踪模式）
  bash scripts/logs.sh api --tail 50        # 查看最近 50 行 API 日志
  bash scripts/logs.sh worker               # 查看 Worker 日志
```

### 3. stop.sh - 环境关闭

```bash
bash scripts/stop.sh [mode] [options]

Modes:
  dev       - 停止开发环境（默认）
  prod      - 停止生产环境
  all       - 停止所有环境
  status    - 查看当前状态

Options:
  --remove-volumes  - 删除数据卷（警告：会删除数据库！）
  --remove-images   - 删除 Docker 镜像
  --clean           - 清理所有容器、卷和网络

Examples:
  bash scripts/stop.sh dev                      # 停止开发环境（保留数据）
  bash scripts/stop.sh prod                     # 停止生产环境
  bash scripts/stop.sh dev --remove-volumes     # 停止并删除数据
  bash scripts/stop.sh all --clean              # 彻底清理
  bash scripts/stop.sh status                   # 查看状态
```

### 4. test.sh - 测试执行

```bash
bash scripts/test.sh [type] [options]

Types:
  unit         - 仅运行单元测试
  integration  - 仅运行集成测试
  sandbox      - 仅运行沙箱测试
  all          - 运行所有测试（默认）

Options:
  --coverage   - 生成覆盖率报告
  -v           - 详细输出
  --no-cache   - 无缓存构建

Examples:
  bash scripts/test.sh                      # 运行所有测试
  bash scripts/test.sh unit                 # 仅运行单元测试
  bash scripts/test.sh all --coverage       # 所有测试 + 覆盖率
  bash scripts/test.sh sandbox -v           # 沙箱测试（详细）
```

---

## 环境隔离架构

AutoTest-Agent 采用**完全容器化**的架构设计，确保开发与测试环境与宿主机完全隔离：

```
┌─────────────────────────────────────────────┐
│           Host Machine (你的电脑)             │
│                                             │
│  ┌───────────────────────────────────────┐  │
│  │     Docker Network (autotest_network)  │  │
│  │                                       │  │
│  │  ┌─────────────┐  ┌───────────────┐  │  │
│  │  │ DevContainer│  │  PostgreSQL   │  │  │
│  │  │ (API+Front) │  │  (5432)       │  │  │
│  │  └─────────────┘  └───────────────┘  │  │
│  │                                       │  │
│  │  ┌─────────────┐  ┌───────────────┐  │  │
│  │  │ Test Runner │  │    Redis      │  │  │
│  │  │ (pytest)    │  │  (6379)       │  │  │
│  │  └─────────────┘  └───────────────┘  │  │
│  │                                       │  │
│  │  ┌─────────────────────────────┐     │  │
│  │  │  Sandbox Containers         │     │  │
│  │  │  (Ephemeral, Isolated)      │     │  │
│  │  └─────────────────────────────┘     │  │
│  └───────────────────────────────────────┘  │
│                                             │
└─────────────────────────────────────────────┘

关键原则：
✓ 所有依赖安装在容器内
✓ 所有服务运行在容器中
✓ 测试在隔离的沙箱容器执行
✓ 宿主机零污染
```

---

## 项目结构

```
AutoTest-Agent/
├── src/
│   ├── main.py                  # FastAPI 应用入口
│   ├── agent/                   # Agent 主编排器
│   ├── api/
│   │   ├── routes/              # 9 组 API 路由
│   │   └── schemas/             # Pydantic 模型
│   ├── analyzer/                # 代码分析 + 文档分析
│   ├── llm/                     # LLM 抽象层（多厂商适配）
│   ├── tester/                  # 测试用例生成 + 沙箱运行
│   ├── scheduler/               # Celery 任务调度
│   ├── standards/               # 评分引擎 + 模板管理
│   └── common/                  # 配置/日志/数据库
├── tests/                       # 测试套件（新增）
│   ├── unit/                    # 单元测试
│   ├── integration/             # 集成测试
│   └── sandbox/                 # 沙箱测试
├── scripts/                     # 运维脚本
│   ├── start.sh                 # 一键启动
│   ├── stop.sh                  # 环境停止
│   ├── logs.sh                  # 日志查看
│   ├── test.sh                  # 测试执行
│   ├── build_images.sh          # 镜像构建
│   └── deploy_aliyun.sh         # 阿里云部署
├── frontend/                    # React 前端
├── docs/
│   ├── improvements.md          # 改进总结文档
│   └── logs/                    # 开发日志
├── docker-compose.yml           # 生产环境配置
├── docker-compose.dev.yml       # 开发环境配置
└── .env.example                 # 环境变量模板
```

---

## API 端点

| 前缀 | 功能 | 端点数 |
|------|------|--------|
| `/api` | 基础 ping/health | 2 |
| `/api/agent` | 一键检测流水线 | 3 |
| `/api/analysis` | 代码分析 | 2 |
| `/api/batch` | 批量提交/队列 | 2 |
| `/api/documents` | 文档上传/检测计划 | 6 |
| `/api/languages` | 语言配置 | 3 |
| `/api/llm` | LLM 提供商管理 | 5 |
| `/api/scoring` | 评分计算/模板 | 5 |
| `/api/tests` | 测试生成/运行 | 4 |

完整 API 文档：http://localhost:8080/api/docs

---

## 使用流程

### 1. 配置 LLM API Key

编辑 `.env` 文件，设置 LLM_PROVIDERS：
```bash
LLM_PROVIDERS={"openai": {"api_key": "sk-xxx", "model": "gpt-4o"}}
```

### 2. 启动环境

```bash
bash scripts/start.sh dev -d
```

### 3. 创建项目

在项目管理页面创建一个项目，设置语言和测试标准。

### 4. 上传文档（可选）

上传项目需求文档（PDF/DOCX/MD），系统通过 LLM 自动提取关键需求。

### 5. 提交代码

提交学生/外包团队代码，系统自动执行检测流程。

### 6. 查看评分

在评分对比页面查看排名表、雷达图和柱状图。

---

## 测试流程

### 运行测试

```bash
# 运行所有测试（推荐）
bash scripts/test.sh all

# 运行特定类型测试
bash scripts/test.sh unit
bash scripts/test.sh integration
bash scripts/test.sh sandbox

# 生成覆盖率报告
bash scripts/test.sh all --coverage
```

### 测试结构

```
tests/
├── unit/                    # 单元测试
│   ├── test_config.py       # 配置模块测试
│   └── test_exceptions.py   # 异常类测试
├── integration/             # 集成测试
│   └── test_health.py       # API 健康检查测试
└── sandbox/                 # 沙箱测试
    └── test_manager.py      # 沙箱管理器测试
```

### 测试原则

✅ **所有测试在 Docker 容器中运行**
✅ **不依赖宿主机安装的 Python/Node.js**
✅ **数据库和 Redis 为临时容器，测试后自动清理**
✅ **沙箱测试验证真正的 Docker 隔离机制**

---

## 环境变量

复制 `.env.example` 为 `.env` 并修改：

```bash
# 数据库（开发环境）
DATABASE_URL=postgresql+asyncpg://autotest:autotest_dev@postgres:5432/autotest_dev

# Redis
REDIS_URL=redis://redis:6379/0

# LLM API Keys（JSON 格式）
LLM_PROVIDERS={"openai": {"api_key": "sk-xxx", "model": "gpt-4o"}}

# 安全密钥（必须至少 32 字符）
SECRET_KEY=your-secret-key-here-min-32-chars
API_KEY_ENCRYPTION_KEY=your-encryption-key-min-32-chars

# Docker 沙箱
DOCKER_MIRROR=registry.cn-hangzhou.aliyuncs.com

# 并发控制
MAX_CONCURRENCY=10
```

---

## 常见问题

### Q: 如何在本地调试代码？

A: 使用开发容器的 exec 功能：
```bash
bash scripts/start.sh dev -d
docker exec -it autotest-agent-dev bash
cd /workspace
# 在容器内进行开发
```

### Q: 数据库数据丢失怎么办？

A: 数据存储在 Docker volumes 中，除非显式使用 `--remove-volumes`，否则数据会保留。

### Q: 如何备份数据库？

A:
```bash
docker exec autotest-dev-postgres pg_dump -U autotest autotest_dev > backup.sql
```

### Q: 测试失败如何调试？

A:
```bash
# 查看详细日志
bash scripts/test.sh all -v

# 查看容器日志
bash scripts/logs.sh dev

# 进入测试容器调试
docker compose -f docker-compose.dev.yml run --rm devcontainer bash
```

---

## 开发日志

| 里程碑 | 内容 | 日期 |
|--------|------|------|
| M1 | 基础框架搭建 | 2026-06-01 |
| M2 | LLM 抽象层 | 2026-06-02 |
| M3 | 文档分析与检测计划 | 2026-06-03 |
| M4 | 代码分析引擎 | 2026-06-04 |
| M5 | 测试引擎 & 沙箱管理 | 2026-06-05 |
| M6 | 批处理与评分系统 | 2026-06-06 |
| M7 | React 前端开发 | 2026-06-07 |
| M8 | Windows 安装程序 | 2026-06-08 |
| M9 | Docker 镜像体系 | 2026-06-09 |
| M10 | 集成与部署 | 2026-06-10 |
| M11 | 运维脚本完善与测试流程 | 2026-06-11 |

详细日志见 [docs/logs/](docs/logs/)

---

## 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启 Pull Request

**重要**：所有代码更改必须在 Docker 容器中测试通过。

---

## License

MIT License

---

**注意**：本项目严格遵循环境隔离原则，禁止在本地宿主机直接安装依赖或运行服务。所有开发和测试必须通过 Docker 容器进行。
