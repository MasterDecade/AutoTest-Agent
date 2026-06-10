"""Completion page — installation summary and launch options."""

import tkinter as tk
from tkinter import ttk


class CompletePage(tk.Frame):
    """Step 7: Installation complete — summary and launch options."""

    def __init__(self, parent, wizard):
        super().__init__(parent)
        self.wizard = wizard

        # Success icon
        ttk.Label(self, text="✅", font=("Segoe UI Emoji", 48)).pack(pady=(30, 5))

        ttk.Label(self, text="安装完成！", font=("Microsoft YaHei", 16, "bold")).pack()
        ttk.Label(
            self, text="AutoTest-Agent 已成功安装到您的计算机", font=("Microsoft YaHei", 10), foreground="#666"
        ).pack(pady=(5, 15))

        # Info summary
        info_frame = ttk.LabelFrame(self, text=" 安装信息 ", padding=10)
        info_frame.pack(fill=tk.X, padx=60, pady=10)

        info_text = f"""🌐 Web UI:     http://localhost:3000
🔌 API 地址:   http://localhost:8080/api
📁 安装路径:   {wizard.shared_state.get('install_path', 'N/A')}
⚙️ 安装模式:   {'轻量模式' if wizard.shared_state.get('use_lightweight_mode') else '完整模式 (Docker)'}
🔑 LLM 提供商: {len(wizard.shared_state.get('llm_providers', []))} 个
🌍 支持语言:   {', '.join(wizard.shared_state.get('selected_languages', []))}
"""
        info_label = ttk.Label(info_frame, text=info_text, font=("Consolas", 9), justify=tk.LEFT)
        info_label.pack()

        # Options
        opt_frame = ttk.Frame(self)
        opt_frame.pack(pady=15)

        self.open_web_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(opt_frame, text="立即打开 Web UI", variable=self.open_web_var).pack(anchor=tk.W)

        # Finish button
        ttk.Button(
            self,
            text="完成",
            command=self._on_finish,
            style="Accent.TButton",
        ).pack(pady=10)

    def _on_finish(self):
        if self.open_web_var.get():
            import webbrowser

            webbrowser.open("http://localhost:3000")
        self.wizard.destroy()