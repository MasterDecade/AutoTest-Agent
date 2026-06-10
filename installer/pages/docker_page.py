"""Docker configuration page — mirror registry and image source setup."""

import tkinter as tk
from tkinter import ttk


class DockerPage(tk.Frame):
    """Step 4: Configure Docker mirror and image pull sources."""

    def __init__(self, parent, wizard):
        super().__init__(parent)
        self.wizard = wizard

        ttk.Label(self, text="Docker 镜像源配置", font=("Microsoft YaHei", 14, "bold")).pack(pady=(20, 5))
        ttk.Label(
            self,
            text="选择 Docker 镜像加速器（解决国内网络问题）",
            font=("Microsoft YaHei", 10),
            foreground="#666",
        ).pack()

        # Mirror selection
        mirror_frame = ttk.LabelFrame(self, text=" 镜像加速器 ", padding=10)
        mirror_frame.pack(fill=tk.X, padx=40, pady=15)

        self.mirror_var = tk.StringVar(value="registry.cn-hangzhou.aliyuncs.com")

        mirrors = [
            ("阿里云 (推荐)", "registry.cn-hangzhou.aliyuncs.com"),
            ("中科大镜像", "docker.mirrors.ustc.edu.cn"),
            ("网易镜像", "hub-mirror.c.163.com"),
            ("腾讯云镜像", "mirror.ccs.tencentyun.com"),
            ("不使用镜像", ""),
        ]

        for label, value in mirrors:
            ttk.Radiobutton(
                mirror_frame,
                text=label,
                variable=self.mirror_var,
                value=value,
            ).pack(anchor=tk.W, pady=2)

        # Package registries
        pkg_frame = ttk.LabelFrame(self, text=" 包管理器源 ", padding=10)
        pkg_frame.pack(fill=tk.X, padx=40, pady=10)

        self.pip_var = tk.StringVar(value="https://pypi.tuna.tsinghua.edu.cn/simple")
        ttk.Label(pkg_frame, text="pip 源:").pack(side=tk.LEFT)
        pip_combo = ttk.Combobox(
            pkg_frame,
            textvariable=self.pip_var,
            values=[
                "https://pypi.tuna.tsinghua.edu.cn/simple",
                "https://mirrors.aliyun.com/pypi/simple/",
            ],
            width=40,
        )
        pip_combo.pack(side=tk.LEFT, padx=5)

        # Navigation
        nav_frame = ttk.Frame(self)
        nav_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=40, pady=20)
        ttk.Button(nav_frame, text="← 上一步", command=lambda: wizard.prev_page("docker")).pack(side=tk.LEFT)
        ttk.Button(nav_frame, text="下一步 →", command=self._on_next).pack(side=tk.RIGHT)

    def _on_next(self):
        self.wizard.shared_state["docker_mirror"] = self.mirror_var.get()
        self.wizard.next_page("docker")