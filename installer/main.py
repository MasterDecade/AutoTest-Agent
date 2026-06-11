"""AutoTest-Agent Windows Installer — tkinter-based 7-step setup wizard.

Provides a native Windows GUI for:
- Environment detection (Docker, WSL2, system resources)
- LLM API Key configuration
- Docker mirror/image source configuration
- Language support selection
- One-click launch after installation
"""

import sys
import tkinter as tk
from tkinter import ttk
from typing import Optional

# Attempt to import ttkbootstrap for modern styling (optional, graceful fallback)
try:
    import ttkbootstrap as ttkb
    from ttkbootstrap.constants import *

    HAS_TTKB = True
except ImportError:
    HAS_TTKB = False

from installer.pages.welcome_page import WelcomePage
from installer.pages.env_check_page import EnvCheckPage
from installer.pages.api_key_page import ApiKeyPage
from installer.pages.docker_page import DockerPage
from installer.pages.language_page import LanguagePage
from installer.pages.progress_page import ProgressPage
from installer.pages.complete_page import CompletePage


class InstallerWizard(tk.Tk):
    """Main installer wizard window.

    Steps:
    1. Welcome — project intro + install path selection
    2. Environment Check — Docker/WSL2 detection
    3. API Key — LLM provider configuration
    4. Docker — image source and mirror configuration
    5. Languages — supported language selection
    6. Progress — installation progress bar
    7. Complete — success/failure summary
    """

    def __init__(self):
        super().__init__()

        self.title("AutoTest-Agent 安装向导")
        self.geometry("720x520")
        self.resizable(False, False)

        # Shared state across all pages
        self.shared_state = {
            "install_path": r"C:\Program Files\AutoTest-Agent",
            "docker_available": False,
            "wsl2_available": False,
            "use_lightweight_mode": False,
            "llm_providers": [],
            "docker_mirror": "registry.cn-hangzhou.aliyuncs.com",
            "selected_languages": ["python", "cpp", "java"],
            "installation_complete": False,
        }

        self.pages = {}
        self.current_page: Optional[tk.Frame] = None

        self._build_ui()
        self.show_page("welcome")

    def _build_ui(self):
        """Build all pages."""
        container = tk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True)

        self.pages["welcome"] = WelcomePage(container, self)
        self.pages["env_check"] = EnvCheckPage(container, self)
        self.pages["api_key"] = ApiKeyPage(container, self)
        self.pages["docker"] = DockerPage(container, self)
        self.pages["languages"] = LanguagePage(container, self)
        self.pages["progress"] = ProgressPage(container, self)
        self.pages["complete"] = CompletePage(container, self)

    def show_page(self, name: str):
        """Switch to a specific page by name.

        Args:
            name: Page identifier (welcome, env_check, api_key, etc.)
        """
        if self.current_page:
            self.current_page.pack_forget()

        page = self.pages.get(name)
        if page:
            page.pack(fill=tk.BOTH, expand=True)
            self.current_page = page
            if hasattr(page, "on_show"):
                page.on_show()

    def next_page(self, current: str):
        """Advance to the next page in the wizard sequence.

        Args:
            current: Current page identifier.
        """
        sequence = ["welcome", "env_check", "api_key", "docker", "languages", "progress", "complete"]
        try:
            idx = sequence.index(current)
            self.show_page(sequence[idx + 1])
        except (ValueError, IndexError):
            pass

    def prev_page(self, current: str):
        """Go back to the previous page.

        Args:
            current: Current page identifier.
        """
        sequence = ["welcome", "env_check", "api_key", "docker", "languages", "progress", "complete"]
        try:
            idx = sequence.index(current)
            if idx > 0:
                self.show_page(sequence[idx - 1])
        except (ValueError, IndexError):
            pass

    def get_llm_providers_json(self) -> str:
        """Serialize configured LLM providers to JSON string.

        Returns:
            JSON string suitable for LLM_PROVIDERS env variable.
        """
        import json

        providers = {}
        for p in self.shared_state.get("llm_providers", []):
            providers[p.get("provider_type", "")] = {
                "api_key": p.get("api_key", ""),
                "model_name": p.get("model_name", ""),
                "api_base": p.get("api_base", ""),
            }
        return json.dumps(providers)


def run_installer():
    """Entry point for running the installer GUI."""
    app = InstallerWizard()
    app.mainloop()


if __name__ == "__main__":
    run_installer()