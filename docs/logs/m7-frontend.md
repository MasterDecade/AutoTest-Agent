# M7: 前端开发 (React) — 开发日志

## 环境信息
- 日期: 2026-06-04
- 分支: develop
- Node.js: v22.22.1
- npm: 9.2.0

---

## 步骤1: 初始化日志 + 创建 React 项目 — ✅ 完成

## 步骤2: 项目骨架 — ✅ 完成

- `package.json` — React 18 + TS + Vite + Ant Design + ECharts + Axios + Router
- `vite.config.ts` — 开发服务器端口3000 / API代理到localhost:8080
- `tsconfig.json` — TypeScript 严格模式配置
- `index.html` — 入口HTML
- `src/main.tsx` — React 应用入口（中文 Ant Design）
- `src/index.css` — 全局样式
- `src/App.tsx` — 路由定义（6个页面）
- `src/api.ts` — Axios API 封装（所有后端端点）

## 步骤3-7: 页面组件 — ✅ 完成

- `src/layouts/MainLayout.tsx` — 侧边栏布局（Logo/菜单导航/内容区）
- `src/pages/Dashboard.tsx` — 系统总览（后端状态/快速入门）
- `src/pages/Projects.tsx` — 项目管理（创建/表格/操作按钮）
- `src/pages/SubmitCode.tsx` — 代码提交（输入/分析/测试/结果展示）
- `src/pages/ReviewPlan.tsx` — 检测计划审核（生成/查看/批准/驳回）
- `src/pages/CompareScores.tsx` — 评分对比看板（排名表/雷达图/柱状图）
- `src/pages/SettingsLLM.tsx` — LLM 配置（添加/删除/测试 API Key）

## 步骤8: npm install — ✅ 完成

168 packages installed via npmmirror.com (国内镜像)

## 前端文件清单（15个源文件）

- 配置文件: package.json, vite.config.ts, tsconfig.json
- 入口: index.html, src/main.tsx, src/index.css
- 核心: src/App.tsx, src/api.ts
- 布局: src/layouts/MainLayout.tsx
- 页面: Dashboard, Projects, SubmitCode, ReviewPlan, CompareScores, SettingsLLM


## M7 补修 — ✅ 完成

- MainLayout 菜单新增"语言配置"入口（GlobalOutlined 图标）
- 新增 `frontend/public/vite.svg` favicon

## M7 文件总数

15 个前端源文件 + 1 favicon + 3 配置文件 + package-lock.json

