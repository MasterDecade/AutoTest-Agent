"""API Key configuration page — LLM provider setup with test connection."""

import tkinter as tk
from tkinter import ttk, messagebox


class ApiKeyPage(tk.Frame):
    """Step 3: Configure LLM API keys for multiple providers."""

    def __init__(self, parent, wizard):
        super().__init__(parent)
        self.wizard = wizard
        self.providers = []  # List of provider dicts

        ttk.Label(self, text="配置 LLM API Key", font=("Microsoft YaHei", 14, "bold")).pack(pady=(20, 5))
        ttk.Label(
            self,
            text="AutoTest-Agent 需要至少一个 LLM API 密钥才能工作",
            font=("Microsoft YaHei", 10),
            foreground="#666",
        ).pack()

        # Provider list frame
        self.list_frame = ttk.Frame(self)
        self.list_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=10)

        self._add_provider_row()

        # Add provider button
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=40, pady=5)
        ttk.Button(btn_frame, text="+ 添加更多提供商", command=self._add_provider_row).pack(side=tk.LEFT)

        # Navigation
        nav_frame = ttk.Frame(self)
        nav_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=40, pady=20)
        ttk.Button(nav_frame, text="← 上一步", command=lambda: wizard.prev_page("api_key")).pack(side=tk.LEFT)
        ttk.Button(nav_frame, text="下一步 →", command=self._on_next).pack(side=tk.RIGHT)
        ttk.Button(nav_frame, text="跳过 (稍后配置)", command=self._on_skip).pack(side=tk.RIGHT, padx=10)

    def _add_provider_row(self):
        row = ttk.Frame(self.list_frame)
        row.pack(fill=tk.X, pady=5)

        ttk.Label(row, text="提供商:", width=8).pack(side=tk.LEFT)
        provider_combo = ttk.Combobox(
            row,
            values=["openai", "qwen", "deepseek", "zhipuai", "custom"],
            width=12,
        )
        provider_combo.current(0)
        provider_combo.pack(side=tk.LEFT, padx=5)

        ttk.Label(row, text="API Key:", width=7).pack(side=tk.LEFT, padx=(10, 0))
        api_entry = ttk.Entry(row, show="*", width=30)
        api_entry.pack(side=tk.LEFT, padx=5)

        ttk.Label(row, text="模型:", width=5).pack(side=tk.LEFT, padx=(10, 0))
        model_entry = ttk.Entry(row, width=18)
        model_entry.insert(0, "gpt-4o")
        model_entry.pack(side=tk.LEFT, padx=5)

        self.providers.append({
            "frame": row,
            "provider_type": provider_combo,
            "api_key": api_entry,
            "model_name": model_entry,
        })

    def _on_next(self):
        providers_data = []
        for p in self.providers:
            pt = p["provider_type"].get().strip()
            key = p["api_key"].get().strip()
            model = p["model_name"].get().strip()
            if key:
                providers_data.append({
                    "provider_type": pt,
                    "api_key": key,
                    "model_name": model,
                    "api_base": "",
                })

        if not providers_data:
            if not messagebox.askyesno("提示", "您还未配置任何 API Key。确定要跳过吗？"):
                return

        self.wizard.shared_state["llm_providers"] = providers_data
        self.wizard.next_page("api_key")

    def _on_skip(self):
        self.wizard.next_page("api_key")