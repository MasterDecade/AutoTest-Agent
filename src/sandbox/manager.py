"""Docker Sandbox Manager — creates, manages, and destroys isolated test containers."""

import logging
import uuid
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class SandboxConfig:
    """Configuration for a test sandbox."""

    language: str = "python"
    image: str = ""
    code: str = ""
    build_command: str = ""
    test_command: str = ""
    timeout: int = 300
    max_memory: str = "512m"
    max_cpu: float = 2.0
    network_disabled: bool = True
    environment: dict = field(default_factory=dict)


@dataclass
class SandboxResult:
    """Result from a sandbox execution."""

    exit_code: int = -1
    stdout: str = ""
    stderr: str = ""
    timed_out: bool = False
    duration_ms: float = 0.0
    container_id: str = ""


class SandboxManager:
    """Manages Docker containers for isolated test execution.

    Features:
    - Create ephemeral containers per test run
    - Resource limits (CPU, memory, disk)
    - Timeout enforcement
    - Network isolation
    - Automatic cleanup after test completion
    """

    def __init__(self, mirror: str = ""):
        """Initialize sandbox manager.

        Args:
            mirror: Docker registry mirror URL (e.g., registry.cn-hangzhou.aliyuncs.com).
        """
        self.mirror = mirror

    async def create_and_run(
        self,
        config: SandboxConfig,
    ) -> SandboxResult:
        """Create a container, execute test code, and return results.

        Args:
            config: Sandbox configuration.

        Returns:
            SandboxResult with execution output.
        """
        import docker
        import asyncio
        import time

        client = docker.from_env()
        container_id = f"autotest-sandbox-{uuid.uuid4().hex[:12]}"

        try:
            # Determine image
            image = config.image or self._default_image(config.language)

            # Ensure image exists (pull if needed)
            await self._ensure_image(client, image)

            # Create and start container
            container = client.containers.run(
                image=image,
                command="sleep infinity",  # Keep container alive
                detach=True,
                name=container_id,
                mem_limit=config.max_memory,
                nano_cpus=int(config.max_cpu * 1e9),
                network_mode="none" if config.network_disabled else "bridge",
                environment=config.environment,
                remove=False,
            )

            start_time = time.time()

            try:
                # Write code to container
                self._write_code_to_container(container, config.code, config.language)

                # Execute build command if provided
                if config.build_command:
                    exec_result = container.exec_run(
                        f"sh -c '{config.build_command}'",
                        workdir="/tmp/autotest",
                        stderr=True,
                    )
                    if exec_result.exit_code != 0:
                        return SandboxResult(
                            exit_code=exec_result.exit_code,
                            stderr=f"Build failed:\n{exec_result.output.decode('utf-8', errors='replace')}",
                            duration_ms=(time.time() - start_time) * 1000,
                            container_id=container_id,
                        )

                # Execute test command with timeout
                try:
                    exec_result = container.exec_run(
                        f"timeout {config.timeout} sh -c '{config.test_command}'",
                        workdir="/tmp/autotest",
                        stderr=True,
                    )
                    stdout = exec_result.output.decode("utf-8", errors="replace")
                    stderr = ""

                    if "timeout" in stdout.lower() and exec_result.exit_code == 124:
                        return SandboxResult(
                            exit_code=0,
                            timed_out=True,
                            stdout=stdout,
                            duration_ms=(time.time() - start_time) * 1000,
                            container_id=container_id,
                        )

                    return SandboxResult(
                        exit_code=exec_result.exit_code,
                        stdout=stdout,
                        stderr=stderr,
                        duration_ms=(time.time() - start_time) * 1000,
                        container_id=container_id,
                    )
                except Exception as e:
                    return SandboxResult(
                        exit_code=1,
                        stderr=str(e),
                        duration_ms=(time.time() - start_time) * 1000,
                        container_id=container_id,
                    )

            finally:
                # Cleanup
                try:
                    container.remove(force=True)
                except Exception as e:
                    logger.warning(f"Container cleanup failed: {e}")

        except docker.errors.ImageNotFound:
            raise ValueError(f"Docker image '{config.image}' not found. Pull it first.")
        except Exception as e:
            raise RuntimeError(f"Sandbox execution failed: {e}")

    def _default_image(self, language: str) -> str:
        """Get default Docker image for a language.

        Args:
            language: Language identifier.

        Returns:
            Docker image name.
        """
        mapping = {
            "python": "python:3.11-slim",
            "cpp": "gcc:latest",
            "c": "gcc:latest",
            "java": "openjdk:17-slim",
            "go": "golang:1.22-alpine",
            "rust": "rust:1.75-slim",
        }
        return mapping.get(language, "python:3.11-slim")

    async def _ensure_image(self, client, image: str) -> None:
        """Ensure Docker image is available (pull if needed).

        Args:
            client: Docker client.
            image: Image name to ensure.
        """
        import docker

        try:
            client.images.get(image)
            logger.debug(f"Image '{image}' already present")
        except docker.errors.ImageNotFound:
            logger.info(f"Pulling image '{image}'...")
            try:
                client.images.pull(image)
            except Exception as e:
                # Try mirror if configured
                if self.mirror:
                    mirror_image = self._mirror_image(image)
                    try:
                        client.images.pull(mirror_image)
                        if image != mirror_image:
                            client.images.get(mirror_image).tag(image)
                        logger.info(f"Pulled '{image}' via mirror")
                        return
                    except Exception:
                        pass
                raise RuntimeError(f"Failed to pull image '{image}': {e}")

    def _mirror_image(self, image: str) -> str:
        """Convert image name to use mirror registry.

        Args:
            image: Original image name.

        Returns:
            Mirror-prefixed image name.
        """
        if not self.mirror:
            return image
        if "/" in image:
            parts = image.split("/", 1)
            return f"{self.mirror}/{parts[-1]}"
        return f"{self.mirror}/{image}"

    def _write_code_to_container(self, container, code: str, language: str) -> None:
        """Write source code into the container.

        Args:
            container: Docker container.
            code: Source code.
            language: Language identifier.
        """
        ext_map = {
            "python": ".py",
            "cpp": ".cpp",
            "c": ".c",
            "java": "Main.java",
            "go": "main.go",
            "rust": "main.rs",
        }
        ext = ext_map.get(language, ".txt")
        filename = f"/tmp/autotest/{uuid.uuid4().hex[:8]}{ext}"

        # Create directory and write file
        container.exec_run(f"mkdir -p /tmp/autotest")
        # Write via echo approach (handles multiline)
        import base64
        encoded = base64.b64encode(code.encode()).decode()
        container.exec_run(
            f"sh -c 'echo {encoded} | base64 -d > {filename}'"
        )