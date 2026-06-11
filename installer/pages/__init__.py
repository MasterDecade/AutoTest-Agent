"""Installer wizard pages."""

from .welcome_page import WelcomePage
from .env_check_page import EnvCheckPage
from .api_key_page import ApiKeyPage
from .docker_page import DockerPage
from .language_page import LanguagePage
from .progress_page import ProgressPage
from .complete_page import CompletePage

__all__ = [
    "WelcomePage",
    "EnvCheckPage",
    "ApiKeyPage",
    "DockerPage",
    "LanguagePage",
    "ProgressPage",
    "CompletePage",
]