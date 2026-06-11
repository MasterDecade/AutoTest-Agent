"""Docker image builder — manages pre-built language-specific test images."""

import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

# Language-specific Dockerfile templates with domestic mirror support
LANGUAGE_DOCKERFILES = {
    "python": """
FROM python:3.11-slim
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \\
    pip install --no-cache-dir pytest coverage
WORKDIR /tmp/autotest
""",
    "cpp": """
FROM gcc:latest
RUN apt-get update -o Acquire::http::No-Cache=True && \\
    apt-get install -y --no-install-recommends cmake make && \\
    rm -rf /var/lib/apt/lists/*
WORKDIR /tmp/autotest
""",
    "java": """
FROM openjdk:17-slim
RUN apt-get update -o Acquire::http::No-Cache=True && \\
    apt-get install -y --no-install-recommends wget unzip && \\
    wget -q -O /opt/junit.jar https://repo1.maven.org/maven2/org/junit/platform/junit-platform-console-standalone/1.10.0/junit-platform-console-standalone-1.10.0.jar || true && \\
    rm -rf /var/lib/apt/lists/*
WORKDIR /tmp/autotest
""",
}


@dataclass
class ImageBuildConfig:
    """Configuration for building a test image."""

    language: str
    base_image: str = ""
    dependencies: list[str] = field(default_factory=list)
    custom_dockerfile: str = ""


class ImageBuilder:
    """Builds and manages Docker images for test sandboxes.

    Features:
    - Generate language-specific Dockerfiles
    - Build images with domestic mirror support
    - Pre-built image caching
    """

    def __init__(self, mirror: str = ""):
        self.mirror = mirror
        self._built_images: set[str] = set()

    def get_dockerfile(self, language: str, config: Optional[ImageBuildConfig] = None) -> str:
        """Get a Dockerfile for the given language.

        Args:
            language: Language identifier.
            config: Optional build configuration.

        Returns:
            Dockerfile content as string.
        """
        if config and config.custom_dockerfile:
            return config.custom_dockerfile
        return LANGUAGE_DOCKERFILES.get(language, LANGUAGE_DOCKERFILES["python"])

    def get_image_name(self, language: str) -> str:
        """Get the image tag for a test environment.

        Args:
            language: Language identifier.

        Returns:
            Image name/tag.
        """
        return f"autotest-sandbox:{language}-latest"

    def get_build_config(self, language: str) -> dict:
        """Get pre-built environment configuration for a language.

        Args:
            language: Language identifier.

        Returns:
            Dict with build_command, test_command, default_dependencies.
        """
        configs = {
            "python": {
                "build_command": "",
                "test_command": "python -m pytest --tb=short -x /tmp/autotest/ 2>&1",
                "default_dependencies": ["pytest"],
            },
            "cpp": {
                "build_command": "g++ -std=c++17 -Wall -o /tmp/autotest/program /tmp/autotest/*.cpp",
                "test_command": "./tmp/autotest/program",
                "default_dependencies": [],
            },
            "c": {
                "build_command": "gcc -std=c11 -Wall -o /tmp/autotest/program /tmp/autotest/*.c",
                "test_command": "./tmp/autotest/program",
                "default_dependencies": [],
            },
            "java": {
                "build_command": "javac -d /tmp/autotest/classes /tmp/autotest/*.java",
                "test_command": "java -cp /tmp/autotest/classes:/opt/junit.jar org.junit.platform.console.ConsoleLauncher --scan-classpath /tmp/autotest/classes",
                "default_dependencies": ["junit"],
            },
        }
        return configs.get(language, configs["python"])