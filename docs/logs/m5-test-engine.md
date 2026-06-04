# M5: 测试引擎 & 沙箱管理 — 开发日志

## 环境信息
- 日期: 2026-06-04
- 分支: develop
- Docker: 29.5.2
- Python: 3.14.4

---

## 步骤1: 初始化日志 + 分支确认 — ✅ 完成

当前分支: develop

## 步骤2: Sandbox Manager — ✅ 完成

文件: `src/sandbox/manager.py`
- `SandboxConfig` / `SandboxResult` — 沙箱配置与结果数据结构
- `SandboxManager` — Docker 沙箱管理器
  - `create_and_run()` — 创建容器/写入代码/编译/执行/清理
  - 镜像自动拉取（含国内镜像 fallback）
  - 资源限制（内存/CPU/网络隔离）
  - 超时控制 + 自动清理

## 步骤3: 镜像构建器 — ✅ 完成

文件: `src/sandbox/image_builder.py`
- `ImageBuilder` — 预配置语言镜像构建器
- 内置 Python/C++/Java Dockerfile 模板（含国内镜像源）
- `get_build_config()` — 各语言编译/测试命令配置
- 支持自定义 Dockerfile

## 步骤4: Test Case Generator — ✅ 完成

文件: `src/tester/generator.py`
- `GeneratedTestCase` / `GeneratedTestSuite` — 测试用例数据结构
- `TestCaseGenerator.generate()` — LLM 驱动的测试用例生成
- `TestCaseGenerator.expand()` — 基于用户示例的测试扩写
- 支持 Python/C++/Java 及对应测试框架

## 步骤5: Test Runner — ✅ 完成

文件: `src/tester/runner.py`
- `TestResult` / `TestRunResult` — 测试执行结果数据结构
- `TestRunner` — 沙箱中执行测试用例
  - 代码与测试合并 → 编译 → 执行 → 解析结果
  - 支持 Pytest 输出解析（passed/failed 计数）
  - 支持 C/C++ 和 Java 退出码判断
  - pass_rate 计算

## 步骤6: Coverage Analyzer — ✅ 完成

文件: `src/tester/coverage.py`
- `CoverageResult` — 覆盖率数据
- `CoverageAnalyzer` — 从测试输出估算覆盖率
- 支持 Pytest-cov 输出解析

## 步骤7: 测试 API 路由 — ✅ 完成

文件: `src/api/routes/tests.py`
- `POST /api/tests/generate` — 生成测试用例
- `POST /api/tests/expand` — 扩写测试用例
- `POST /api/tests/run` — 在沙箱中执行测试
- `POST /api/tests/generate-and-run` — 生成+执行一气呵成

## 步骤8: Schema — ✅ 完成

文件: `src/api/schemas/tests.py`
- `TestGenerateRequest` / `TestExpandRequest` / `TestRunRequest` — 请求模型
- `TestSuiteResponse` / `TestResultResponse` — 响应模型

额外更新:
- `src/main.py` — 挂载 tests 路由器
