# M2: LLM 抽象层 — 开发日志

## 环境信息
- 日期: 2026-06-04
- 分支: develop
- Docker: 29.5.2
- Python: 3.14.4

---


## 步骤2: BaseProvider 抽象接口 — ✅ 完成

文件: `src/llm/base.py`
- `LLMConfig` — LLM 提供商配置数据类
- `LLMMessage` — 聊天消息数据类（system/user/assistant）
- `LLMResponse` — 响应数据类（含 token 用量统计）
- `LLMStreamChunk` — 流式响应块
- `BaseProvider` — 抽象基类（chat/chat_stream/_validate_config）
- 静态辅助方法: `system()`, `user()`, `assistant()`

## 步骤3: ProviderManager 管理器 — ✅ 完成

文件: `src/llm/provider.py`
- `ProviderManager` — 提供商注册、路由、failover、健康检查
  - `register()` / `unregister()` — 动态增删提供商
  - `get_provider()` — 按类型/模型查找或按优先级返回
  - `list_providers()` — 列出所有提供商及状态
  - `health_check()` — 健康检查（ping 测试）
  - `chat_with_fallback()` — 自动 failover + 指数退避重试
  - `chat_stream_with_fallback()` — 流式 failover
- `get_provider_manager()` — 全局单例

## 步骤4: LiteLLM 适配器 — ✅ 完成

文件: `src/llm/adapters/litellm_adapter.py`
- `LiteLLMAdapter` — 基于 LiteLLM SDK 的多厂商适配
- 支持: OpenAI, Anthropic, Azure, Gemini, Qwen, DeepSeek, ZhipuAI, Ollama, vLLM 等
- 统一 `provider_type/model_name` 路由
- 流式和非流式两种模式

## 步骤5: 自定义 API 适配器 — ✅ 完成

文件: `src/llm/adapters/custom_adapter.py`
- `CustomAdapter` — 基于 httpx 的自定义 API 适配
- 支持 OpenAI 兼容格式和自定义请求/响应格式
- 可配置 endpoint、请求映射模板
- 流式 SSE 解析

## 步骤6: OpenAI 兼容适配器 — ✅ 完成

文件: `src/llm/adapters/openai_compat.py`
- `OpenAICompatAdapter` — 继承 CustomAdapter，预设 OpenAI 格式
- 面向自部署方案: vLLM, Ollama, LocalAI, TGI

## 步骤7: Prompt 模板管理 — ✅ 完成

文件:
- `src/llm/prompt_templates/__init__.py` — 模板导出
- `src/llm/prompt_templates/code_analysis.py` — 代码分析 Prompt（JSON输出）
- `src/llm/prompt_templates/test_generation.py` — 测试用例生成 + 扩写 Prompt
- `src/llm/prompt_templates/result_analysis.py` — 测试结果分析 Prompt

## 步骤8: LLM API 路由 — ✅ 完成

文件: `src/api/routes/llm.py`
- `GET /api/llm/providers` — 列出所有提供商
- `POST /api/llm/providers` — 注册新提供商（自动选择适配器）
- `DELETE /api/llm/providers/{type}/{model}` — 删除提供商
- `POST /api/llm/providers/test` — 测试连接
- `POST /api/llm/chat` — 聊天补全（支持指定 provider 或自动 failover）

## 步骤9: Schema 定义 — ✅ 完成

文件: `src/api/schemas/llm.py`
- `ChatRequest` / `ChatResponse` — 聊天请求/响应模型
- `ProviderConfigRequest` / `ProviderConfigResponse` — 提供商配置
- `ProviderTestRequest` / `ProviderTestResponse` — 连接测试
- `ProviderInfo` / `ProviderListResponse` — 提供商列表

额外更新:
- `src/main.py` — 挂载 LLM 路由器 (`app.include_router(llm_router)`)

