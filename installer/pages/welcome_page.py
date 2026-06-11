"""Welcome page — project introduction and install path selection."""

import os
import tkinter as tk
from tkinter import filedialog, ttk


class WelcomePage(tk.Frame):
    def __init__(self, parent, wizard):
        super().__init__(parent)
        self.wizard = wizard

        # Title
        title = ttk.Label(self, text="欢迎使用 AutoTest-Agent", font=("Microsoft YaHei", 16, "bold"))
        title.pack(pady=(30, 10))

        subtitle = ttk.Label(
            self,
            text="智能代码检测与自动化测试平台",
            font=("Microsoft YaHei", 11),
            foreground="#666",
        )
        subtitle.pack()

        # Features list
        features_frame = ttk.LabelFrame(self, text=" 功能特性 ", padding=10)
        features_frame.pack(fill=tk.X, padx=40, pady=20)

        features = [
            "✓ 多语言代码自动检测 (Python/C++/Java)",
            "✓ AI 驱动测试用例生成",
            "✓ 批量提交与评分对比",
            "✓ 统一测试标准管理",
            "✓ 隔离化 Docker 沙箱执行",
        ]
        for f in features:
            ttk.Label(features_frame, text=f, font=("Microsoft YaHei", 10)).pack(anchor=tk.W)

        # Install path
        path_frame = ttk.Frame(self)
        path_frame.pack(fill=tk.X, padx=40, pady=(10, 5))

        ttk.Label(path_frame, text="安装路径:", font=("Microsoft YaHei", 10)).pack(side=tk.LEFT)

        self.path_var = tk.StringVar(value=self.wizard.shared_state["install_path"])
        path_entry = ttk.Entry(path_frame, textvariable=self.path_var, width=40)
        path_entry.pack(side=tk.LEFT, padx=(10, 5))

        def browse():
            result = filedialog.askdirectory(initialdir=self.path_var.get())
            if result:
                self.path_var.set(result)

        ttk.Button(path_frame, text="浏览...", command=browse).pack(side=tk.LEFT)

        # Options
        options_frame = ttk.Frame(self)
        options_frame.pack(fill=tk.X, padx=40, pady=10)

        self.desktop_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="创建桌面快捷方式", variable=self.desktop_var).pack(anchor=tk.W)

        self.startup_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="开机自动启动服务", variable=self.startup_var).pack(anchor=tk.W)

        # Navigation
        nav_frame = ttk.Frame(self)
        nav_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=40, pady=20)

        ttk.Button(nav_frame, text="下一步 →", command=self._on_next).pack(side=tk.RIGHT)

    def _on_next(self):
        self.wizard.shared_state["install_path"] = self.path_var.get()
        self.wizard.next_page("welcome")