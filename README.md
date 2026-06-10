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

---

## 快速开始

### Docker Compose（推荐）

```bash
git clone git@github.com:MasterDecade/AutoTest-Agent.git
cd AutoTest-Agent
cp .env.example .env   # 编辑 .env 填入 API Key
docker compose up -d
```

访问：
- Web UI: http://localhost:3000
- API 文档: http://localhost:8080/api/docs
- API 地址: http://localhost:8080/api

### 本地开发

```bash
# 后端
pip install -r requirements-dev.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
uvicorn src.main:app --reload

# 前端
cd frontend && npm install --registry=https://registry.npmmirror.com && npm run dev
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
├── frontend/                    # React 前端
├── installer/                   # Windows 安装程序 (tkinter)
├── scripts/                     # 运维脚本
└── docs/logs/                   # 开发日志
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

---

## 使用流程

### 1. 配置 LLM API Key

在 LLM 配置页面添加至少一个 API Key（支持 OpenAI / 通义千问 / DeepSeek / 智谱 AI 等）。

### 2. 创建项目

在项目管理页面创建一个项目，设置语言和测试标准。

### 3. 上传文档（可选）

上传项目需求文档（PDF/DOCX/MD），系统通过 LLM 自动提取关键需求、测试标准和评分规则。

### 4. 提交代码

提交学生/外包团队代码，系统自动：
1. **静态分析** — 语法检查、代码规范、潜在bug
2. **生成检测计划** — LLM 根据代码和文档生成测试计划
3. **人工审核** — 审核并批准检测计划
4. **生成并运行测试** — LLM 生成测试用例，Docker 沙箱执行
5. **评分** — 多维度评分（功能正确性/规范/质量/覆盖率/性能/文档）

### 5. 查看评分对比

在评分对比页面查看排名表、雷达图和柱状图，方便老师/项目主管裁定。

---

## 部署脚本

| 脚本 | 功能 |
|------|------|
| `scripts/start.sh` | 一键启动（backend/frontend/all） |
| `scripts/configure_mirrors.sh` | 国内镜像源自动配置 |
| `scripts/build_images.sh` | Docker 镜像构建/导出 |
| `scripts/deploy_aliyun.sh` | 阿里云 ECS 部署 |

---

## 环境变量

复制 `.env.example` 为 `.env` 并修改：

```bash
# 数据库
DATABASE_URL=postgresql://autotest:autotest_pass@localhost:5432/autotest

# Redis
REDIS_URL=redis://localhost:6379/0

# LLM API Keys（JSON 格式，支持多 Provider）
LLM_PROVIDERS={"openai": {"api_key": "sk-xxx", "model": "gpt-4o"}}

# Docker 沙箱
DOCKER_MIRROR=registry.cn-hangzhou.aliyuncs.com

# 并发控制
MAX_CONCURRENCY=10

# 国内镜像源
PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
```

---

## 开发日志

| 里程碑 | 内容 |
|--------|------|
| M1 | 基础框架搭建 |
| M2 | LLM 抽象层 |
| M3 | 文档分析与检测计划 |
| M4 | 代码分析引擎 |
| M5 | 测试引擎 & 沙箱管理 |
| M6 | 批处理与评分系统 |
| M7 | React 前端开发 |
| M8 | Windows 安装程序 |
| M9 | Docker 镜像体系 |
| M10 | 集成与部署 |

---

## License

MIT License