"""Language support configuration page."""

import tkinter as tk
from tkinter import ttk


class LanguagePage(tk.Frame):
    """Step 5: Select which programming languages to support."""

    def __init__(self, parent, wizard):
        super().__init__(parent)
        self.wizard = wizard

        ttk.Label(self, text="语言支持配置", font=("Microsoft YaHei", 14, "bold")).pack(pady=(20, 5))
        ttk.Label(
            self,
            text="选择需要支持的编程语言（可多选）",
            font=("Microsoft YaHei", 10),
            foreground="#666",
        ).pack()

        lang_frame = ttk.LabelFrame(self, text=" 内置语言 ", padding=10)
        lang_frame.pack(fill=tk.X, padx=40, pady=15)

        self.python_var = tk.BooleanVar(value=True)
        self.cpp_var = tk.BooleanVar(value=True)
        self.java_var = tk.BooleanVar(value=True)

        ttk.Checkbutton(lang_frame, text="Python — pytest + Pylint", variable=self.python_var).pack(anchor=tk.W, pady=3)
        ttk.Checkbutton(lang_frame, text="C/C++ — GCC + Google Test + CPPCheck", variable=self.cpp_var).pack(anchor=tk.W, pady=3)
        ttk.Checkbutton(lang_frame, text="Java — OpenJDK + JUnit 5 + Checkstyle", variable=self.java_var).pack(anchor=tk.W, pady=3)

        # Navigation
        nav_frame = ttk.Frame(self)
        nav_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=40, pady=20)
        ttk.Button(nav_frame, text="← 上一步", command=lambda: wizard.prev_page("languages")).pack(side=tk.LEFT)
        ttk.Button(nav_frame, text="开始安装 →", command=self._on_next).pack(side=tk.RIGHT)

    def _on_next(self):
        langs = []
        if self.python_var.get():
            langs.append("python")
        if self.cpp_var.get():
            langs.extend(["cpp", "c"])
        if self.java_var.get():
            langs.append("java")
        self.wizard.shared_state["selected_languages"] = langs
        self.wizard.next_page("languages")