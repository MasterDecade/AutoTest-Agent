# M12: 系统流程修复 — 开发日志

## 环境信息
- 日期: 2026-06-30
- 分支: develop_qoder
- 目标: 修复项目创建到测试执行的完整业务流程

---

## 问题总览

当前系统存在四个核心流程断裂问题：
1. 项目创建仅存于前端内存，无法持久化到数据库
2. 缺乏"项目内容定义"环节，无法上传文档提取需求
3. 审核通过后无"执行计划"按钮，流程中断
4. 代码提交仅支持文本粘贴，不支持文件/压缩包上传和批量导入

---

## 修复 1: 项目持久化与手动保存按钮

### 问题描述
`Projects.tsx` 中创建项目仅存入 React 本地状态（`Date.now().toString()` 作为 ID），未调用任何后端 API。用户创建项目后退出再进入，项目消失。

### 解决方案
- **后端**: 新建 `src/api/routes/projects.py` 实现 `POST /api/projects`（创建并持久化）、`GET /api/projects`（列表含 submission_count 统计）、`GET /api/projects/{id}`（单个查询），使用 `AsyncSession` 异步写入 `projects` 表
- **Schema**: 新建 `src/api/schemas/projects.py`（`ProjectCreateRequest` / `ProjectResponse`）
- **路由注册**: `src/main.py` 中导入并注册 `projects_router`
- **前端 API**: `frontend/src/api.ts` 新增 `createProject`、`getProjects`、`getProject`
- **前端页面**: `frontend/src/pages/Projects.tsx` 全面重写：
  - `useEffect` 挂载时调用 `getProjects()` 加载列表
  - Modal 确认按钮改为 `handleSave`，调用 `createProject` API 写入数据库
  - 保存成功后刷新列表并导航到 `/projects/:id/content`

### 变更文件
| 操作 | 文件 |
|------|------|
| 新建 | `src/api/schemas/projects.py` |
| 新建 | `src/api/routes/projects.py` |
| 修改 | `src/main.py` |
| 修改 | `frontend/src/api.ts` |
| 修改 | `frontend/src/pages/Projects.tsx` |

---

## 修复 2: 项目内容输入与分析流程

### 问题描述
创建项目后直接跳转"提交代码"页面，缺少中间环节：用户无法输入项目需求、上传需求文档、让系统提取关键信息并生成测试计划。

### 解决方案
- **新建页面**: `frontend/src/pages/ProjectContent.tsx` 实现完整的项目内容定义页：
  - 文本输入区域：填写项目要求、格式约束、评分标准
  - 文件拖拽上传：支持 PDF/MD/DOCX/TXT，调用 `uploadDocument` API 自动提取文本并分析
  - "分析文本内容"按钮：调用 `/api/documents/analyze-text` 进行 LLM 分析
  - 分析结果展示：列出关键需求、测试标准、评分规则、不确定项
  - "生成检测计划"按钮：调用 `/api/documents/generate-plan`，成功后跳转审核页
- **路由注册**: `frontend/src/App.tsx` 新增 `/projects/:projectId/content` → `<ProjectContent />`
- **后端增强**: `src/api/routes/documents.py` 中 `/analyze-text` 接口新增 `project_id` 参数

### 变更文件
| 操作 | 文件 |
|------|------|
| 新建 | `frontend/src/pages/ProjectContent.tsx` |
| 修改 | `frontend/src/App.tsx` |
| 修改 | `src/api/routes/documents.py` |

---

## 修复 3: 检测计划执行按钮

### 问题描述
`ReviewPlan.tsx` 在计划审批通过后（`status === 'approved'`）没有任何后续操作按钮，审核后的流程完全中断。原有页面还包含内联代码输入框（应从上一步获得 plan），设计不合理。

### 解决方案
- **页面重写**: `frontend/src/pages/ReviewPlan.tsx` 全面重构：
  - 通过 URL 参数 `plan_id` 加载已有计划（而非内联代码输入）
  - **pending_review** 状态：显示"批准计划"/"驳回计划"按钮 + 审核意见输入
  - **approved** 状态：显示"执行计划"按钮，调用 `generateAndRun` 在沙箱中执行测试
  - **executed** 状态：显示完成信息 + "查看评分对比"跳转按钮
  - **无计划**状态：显示引导提示 + "前往项目内容页面"按钮
  - 新增测试结果展示卡片（通过/失败/覆盖率/耗时/输出日志）

### 变更文件
| 操作 | 文件 |
|------|------|
| 修改 | `frontend/src/pages/ReviewPlan.tsx` |

---

## 修复 4: 文件上传代替文本输入 + 批量导入

### 问题描述
`SubmitCode.tsx` 仅支持在 TextArea 中粘贴代码文本，不支持文件上传。无法处理多文件项目、zip 压缩包、以及批量学生提交的场景。

### 解决方案

#### 后端 — 提交管理
- **新建路由**: `src/api/routes/submissions.py`
  - `POST /api/projects/{id}/submissions/upload` — 单/多文件上传，自动解压 zip 并保持目录结构，通过 `LanguageDetector` 识别语言，写入 `submissions` 表
  - `GET /api/projects/{id}/submissions` — 获取提交列表
  - `POST /api/projects/{id}/submissions/batch` — 批量上传（多提交者模式）
- **新建 Schema**: `src/api/schemas/submissions.py`（`SubmissionUploadResponse` / `BatchUploadResponse`）
- **路由注册**: `src/main.py` 中导入并注册 `submissions_router`

#### 后端 — 沙箱多文件支持
- **`src/sandbox/manager.py`**:
  - `SandboxConfig` 新增 `files: dict[str, str]` 字段（相对路径 → 内容映射）
  - `_write_code_to_container_async` 重写为双模式：
    - 多文件模式：遍历 `files` 字典，创建完整目录结构，通过 tar 写入容器
    - 单文件模式：保持原有的 `code`/`test_code` 合并写入（向后兼容）
- **`src/tester/runner.py`**:
  - `run_tests` 新增 `files` 可选参数
  - 区分多文件/单文件模式构造 `SandboxConfig`

#### 前端
- **`frontend/src/pages/SubmitCode.tsx`** 全面重写：
  - 使用 antd `Upload.Dragger` 组件替代 TextArea
  - 支持多文件选择和拖拽
  - 支持 ZIP 压缩包上传
  - 显示上传进度条和文件列表（含语言标签、文件大小）
  - 提交者名称输入
  - 语言手动指定或自动检测
  - 上传后显示详细结果（文件列表、检测语言、提交ID）
  - "执行测试"按钮触发沙箱执行
- **`frontend/src/api.ts`** 新增 `uploadSubmission`、`getSubmissions`

### 变更文件
| 操作 | 文件 |
|------|------|
| 新建 | `src/api/schemas/submissions.py` |
| 新建 | `src/api/routes/submissions.py` |
| 修改 | `src/main.py` |
| 修改 | `src/sandbox/manager.py` |
| 修改 | `src/tester/runner.py` |
| 修改 | `frontend/src/api.ts` |
| 修改 | `frontend/src/pages/SubmitCode.tsx` |

---

## 完整变更文件清单

| 操作 | 文件 |
|------|------|
| 新建 | `src/api/schemas/projects.py` |
| 新建 | `src/api/routes/projects.py` |
| 新建 | `src/api/schemas/submissions.py` |
| 新建 | `src/api/routes/submissions.py` |
| 新建 | `frontend/src/pages/ProjectContent.tsx` |
| 新建 | `docs/logs/m12-system-flow-fixes.md` |
| 修改 | `src/main.py` |
| 修改 | `src/api/routes/documents.py` |
| 修改 | `src/sandbox/manager.py` |
| 修改 | `src/tester/runner.py` |
| 修改 | `frontend/src/api.ts` |
| 修改 | `frontend/src/App.tsx` |
| 修改 | `frontend/src/pages/Projects.tsx` |
| 修改 | `frontend/src/pages/ReviewPlan.tsx` |
| 修改 | `frontend/src/pages/SubmitCode.tsx` |

---

## 端到端流程验证路径

1. **创建项目** → 项目管理页 → 点击"创建项目" → 填写名称/描述/语言 → "保存到数据库" → 列表刷新可见 → 自动跳转项目内容页
2. **内容定义** → 输入文本 或 上传 PDF/MD/DOCX → "分析文本内容" → 查看提取的需求/标准/规则 → "生成检测计划" → 自动跳转审核页
3. **审核执行** → 查看计划（测试用例/评分维度/风险提示） → 输入审核意见 → "批准计划" → 显示"执行计划"按钮 → 点击执行 → 查看测试结果
4. **代码提交** → 上传单个/多个代码文件或 zip 包 → 自动语言检测 → 查看文件列表 → "执行测试" → 沙箱执行 → 查看结果

---

## 编译验证

所有新增/修改的 Python 文件已通过 `py_compile` 编译检查，无语法错误：
```
OK: src/api/schemas/projects.py
OK: src/api/routes/projects.py
OK: src/api/schemas/submissions.py
OK: src/api/routes/submissions.py
OK: src/sandbox/manager.py
OK: src/tester/runner.py
OK: src/api/routes/documents.py
OK: src/main.py
```
