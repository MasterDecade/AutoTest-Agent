"""Environment check page — Docker, WSL2, and system detection."""

import platform
import subprocess
import tkinter as tk
from tkinter import ttk


class EnvCheckPage(tk.Frame):
    def __init__(self, parent, wizard):
        super().__init__(parent)
        self.wizard = wizard
        self.checks_done = False

        # Title
        ttk.Label(self, text="环境检测", font=("Microsoft YaHei", 14, "bold")).pack(pady=(20, 10))
        ttk.Label(self, text="正在检查您的系统环境...", font=("Microsoft YaHei", 10), foreground="#666").pack()

        # Results area
        self.result_frame = ttk.LabelFrame(self, text=" 检测结果 ", padding=10)
        self.result_frame.pack(fill=tk.X, padx=40, pady=15)

        self.results_text = tk.Text(self.result_frame, height=8, width=60, font=("Consolas", 9))
        self.results_text.pack(fill=tk.X)

        # Mode selection
        self.mode_frame = ttk.LabelFrame(self, text=" 安装模式 ", padding=10)

        self.mode_var = tk.StringVar(value="docker")

        self.docker_radio = ttk.Radiobutton(
            self.mode_frame, text="完整模式 (Docker) — 推荐，支持隔离沙箱", variable=self.mode_var, value="docker"
        )
        self.docker_radio.pack(anchor=tk.W)

        self.lite_radio = ttk.Radiobutton(
            self.mode_frame,
            text="轻量模式 — 无需 Docker，功能受限",
            variable=self.mode_var,
            value="lite",
        )
        self.lite_radio.pack(anchor=tk.W)

        # Action buttons
        action_frame = ttk.Frame(self)
        action_frame.pack(fill=tk.X, padx=40, pady=10)

        self.recheck_btn = ttk.Button(action_frame, text="重新检测", command=self._run_checks)
        self.recheck_btn.pack(side=tk.LEFT)

        # Navigation
        nav_frame = ttk.Frame(self)
        nav_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=40, pady=20)

        ttk.Button(nav_frame, text="← 上一步", command=lambda: wizard.prev_page("env_check")).pack(side=tk.LEFT)
        self.next_btn = ttk.Button(nav_frame, text="下一步 →", command=self._on_next)
        self.next_btn.pack(side=tk.RIGHT)

    def on_show(self):
        if not self.checks_done:
            self._run_checks()

    def _run_checks(self):
        self.results_text.delete(1.0, tk.END)
        self.checks_done = True

        self._log(f"操作系统: {platform.system()} {platform.release()}")
        self._log(f"Python 版本: {platform.python_version()}")
        self._log(f"CPU 核心数: {self._get_cpu_count()}")
        self._log(f"内存总量: {self._get_memory_gb():.1f} GB")

        # Check Docker
        docker_ok = self._check_command("docker")
        self.wizard.shared_state["docker_available"] = docker_ok
        status = "✅ Docker 已安装" if docker_ok else "❌ Docker 未安装（需要 Docker Desktop for Windows）"
        self._log(status)

        # Check WSL2
        wsl2_ok = self._check_wsl2()
        self.wizard.shared_state["wsl2_available"] = wsl2_ok
        wsl_status = "✅ WSL2 已启用" if wsl2_ok else "⚠ WSL2 未检测到（Docker 依赖 WSL2）"
        self._log(wsl_status)

        # Update mode recommendation
        if not docker_ok:
            self.mode_var.set("lite")
            self.docker_radio.config(state=tk.DISABLED)
            self._log("⚠ 推荐使用轻量模式")
        else:
            self.mode_var.set("docker")

    def _log(self, text: str):
        self.results_text.insert(tk.END, text + "\n")
        self.results_text.see(tk.END)

    def _check_command(self, cmd: str) -> bool:
        try:
            result = subprocess.run([cmd, "--version"], capture_output=True, timeout=10)
            return result.returncode == 0
        except Exception:
            return False

    def _check_wsl2(self) -> bool:
        try:
            result = subprocess.run(["wsl", "--status"], capture_output=True, timeout=10, text=True)
            return "kernel" in result.stdout.lower()
        except Exception:
            return False

    def _get_cpu_count(self) -> int:
        import os

        return os.cpu_count() or 4

    def _get_memory_gb(self) -> float:
        try:
            import psutil

            return psutil.virtual_memory().total / (1024**3)
        except ImportError:
            return 8.0

    def _on_next(self):
        self.wizard.shared_state["use_lightweight_mode"] = self.mode_var.get() == "lite"
        self.wizard.next_page("env_check")