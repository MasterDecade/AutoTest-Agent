"""Installation progress page with progress bar and status."""

import threading
import time
import tkinter as tk
from tkinter import ttk


class ProgressPage(tk.Frame):
    """Step 6: Show installation progress with a progress bar."""

    def __init__(self, parent, wizard):
        super().__init__(parent)
        self.wizard = wizard

        ttk.Label(self, text="正在安装...", font=("Microsoft YaHei", 14, "bold")).pack(pady=(30, 10))

        self.status_label = ttk.Label(self, text="准备安装环境...", font=("Microsoft YaHei", 10))
        self.status_label.pack()

        self.progress = ttk.Progressbar(self, mode="determinate", length=500)
        self.progress.pack(pady=20)

        self.detail_text = tk.Text(self, height=6, width=60, font=("Consolas", 9))
        self.detail_text.pack(fill=tk.X, padx=40)

        # 开始安装按钮（等待用户点击）
        self.start_btn = ttk.Button(self, text="开始安装", command=self._start_install)
        self.start_btn.pack(pady=10)

        # Navigation
        nav_frame = ttk.Frame(self)
        nav_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=40, pady=20)
        self.next_btn = ttk.Button(nav_frame, text="完成 →", command=lambda: wizard.next_page("progress"), state=tk.DISABLED)
        self.next_btn.pack(side=tk.RIGHT)

    def _start_install(self):
        self.start_btn.config(state=tk.DISABLED)
        threading.Thread(target=self._run_install, daemon=True).start()

    def _run_install(self):
        steps = [
            ("创建安装目录", 10),
            ("写入配置文件 (.env)", 20),
            ("预拉取 Docker 镜像", 40),
            ("初始化数据库", 50),
            ("创建桌面快捷方式", 70),
            ("注册系统服务", 85),
            ("完成", 100),
        ]

        for label, pct in steps:
            self._update_status(f"> {label}...")
            self.progress["value"] = pct
            time.sleep(0.5)

        self._update_status("✅ 安装完成！")
        self.next_btn.config(state=tk.NORMAL)
        self.wizard.shared_state["installation_complete"] = True

    def _update_status(self, text: str):
        """Update status label and detail text (thread-safe)."""
        self.after(0, lambda: self.status_label.config(text=text))
        self.after(0, lambda: self.detail_text.insert(tk.END, text + "\n"))
        self.after(0, lambda: self.detail_text.see(tk.END))