"""Docker Sandbox Manager — creates, manages, and destroys isolated test containers.

Provides secure, resource-limited execution environments for multi-language
code testing with automatic cleanup and timeout enforcement.
"""

import asyncio
import base64
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional

import docker
from docker.errors import APIError, DockerException, ImageNotFound

logger = logging.getLogger(__name__)


@dataclass
class SandboxConfig:
    """Configuration for a test sandbox."""

    language: str = "python"
    image: str = ""
    code: str = ""
    test_code: str = ""
    build_command: str = ""
    test_command: str = ""
    timeout: int = 300
    max_memory: str = "512m"
    max_cpu: float = 2.0
    network_disabled: bool = True
    environment: dict = field(default_factory=dict)
    working_dir: str = "/tmp/autotest"


@dataclass
class SandboxResult:
    """Result from a sandbox execution."""

    exit_code: int = -1
    stdout: str = ""
    stderr: str = ""
    timed_out: bool = False
    duration_ms: float = 0.0
    container_id: str = ""
    error: str = ""


class SandboxManager:
    """Manages Docker containers for isolated test execution.

    Features:
    - Create ephemeral containers per test run
    - Resource limits (CPU, memory)
    - Timeout enforcement
    - Network isolation
    - Automatic cleanup after test completion
    - Secure code writing via tar archives
    """

    def __init__(self, mirror: str = ""):
        """Initialize sandbox manager.

        Args:
            mirror: Docker registry mirror URL (e.g., registry.cn-hangzhou.aliyuncs.com).
        """
        self.mirror = mirror
        self._client: Optional[docker.DockerClient] = None

    def _get_client(self) -> docker.DockerClient:
        """Get or create Docker client instance."""
        if self._client is None:
            try:
                self._client = docker.from_env()
            except DockerException as e:
                raise RuntimeError(f"Failed to connect to Docker daemon: {e}")
        return self._client

    async def create_and_run(self, config: SandboxConfig) -> SandboxResult:
        """Create a container, execute test code, and return results.

        This method:
        1. Ensures the required Docker image is available
        2. Creates a container with resource limits
        3. Writes code securely via tar archive
        4. Executes build and test commands
        5. Cleans up the container

        Args:
            config: Sandbox configuration.

        Returns:
            SandboxResult with execution output.

        Raises:
            RuntimeError: If Docker operations fail.
            ValueError: If required image is not available.
        """
        client = self._get_client()
        container_id = f"autotest-sandbox-{uuid.uuid4().hex[:12]}"
        container = None

        try:
            # Determine image
            image = config.image or self._default_image(config.language)

            # Ensure image exists (pull if needed)
            await self._ensure_image(client, image)

            # Create container with resource limits
            logger.info(f"Creating sandbox container: {container_id}")
            container = client.containers.run(
                image=image,
                command="sleep infinity",
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
                # Write code to container securely
                await self._write_code_to_container_async(container, config)

                # Execute build command if provided
                if config.build_command:
                    build_result = await self._exec_command(
                        container, config.build_command, config.working_dir
                    )
                    if build_result.exit_code != 0:
                        return SandboxResult(
                            exit_code=build_result.exit_code,
                            stderr=f"Build failed:\n{build_result.stderr}",
                            duration_ms=(time.time() - start_time) * 1000,
                            container_id=container_id,
                        )

                # Execute test command with timeout
                test_result = await self._exec_command(
                    container,
                    f"timeout {config.timeout} {config.test_command}",
                    config.working_dir,
                )

                # Check for timeout
                if test_result.exit_code == 124:
                    return SandboxResult(
                        exit_code=0,
                        timed_out=True,
                        stdout=test_result.stdout,
                        stderr="Execution timed out",
                        duration_ms=(time.time() - start_time) * 1000,
                        container_id=container_id,
                    )

                return SandboxResult(
                    exit_code=test_result.exit_code,
                    stdout=test_result.stdout,
                    stderr=test_result.stderr,
                    duration_ms=(time.time() - start_time) * 1000,
                    container_id=container_id,
                )

            finally:
                # Cleanup container
                await self._cleanup_container(container)

        except ImageNotFound:
            raise ValueError(f"Docker image '{config.image}' not found. Pull it first.")
        except APIError as e:
            raise RuntimeError(f"Docker API error: {e}")
        except Exception as e:
            logger.error(f"Sandbox execution failed: {e}")
            raise RuntimeError(f"Sandbox execution failed: {e}")

    async def _exec_command(
        self, container, command: str, workdir: str = "/tmp/autotest"
    ) -> SandboxResult:
        """Execute a command in the container asynchronously.

        Args:
            container: Docker container.
            command: Command to execute.
            workdir: Working directory.

        Returns:
            SandboxResult with command output.
        """
        loop = asyncio.get_event_loop()
        try:
            exec_result = await loop.run_in_executor(
                None,
                lambda: container.exec_run(
                    f"sh -c '{command}'",
                    workdir=workdir,
                    stderr=True,
                ),
            )

            stdout = exec_result.output.decode("utf-8", errors="replace") if exec_result.output else ""
            stderr = ""

            return SandboxResult(
                exit_code=exec_result.exit_code,
                stdout=stdout,
                stderr=stderr,
            )
        except Exception as e:
            return SandboxResult(exit_code=1, stderr=str(e))

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
            "c++": "gcc:latest",
            "c": "gcc:latest",
            "java": "openjdk:17-slim",
            "go": "golang:1.22-alpine",
            "rust": "rust:1.75-slim",
        }
        return mapping.get(language, "python:3.11-slim")

    async def _ensure_image(self, client: docker.DockerClient, image: str) -> None:
        """Ensure Docker image is available (pull if needed).

        Args:
            client: Docker client.
            image: Image name to ensure.
        """
        loop = asyncio.get_event_loop()

        try:
            await loop.run_in_executor(None, client.images.get, image)
            logger.debug(f"Image '{image}' already present")
        except ImageNotFound:
            logger.info(f"Pulling image '{image}'...")
            try:
                await loop.run_in_executor(None, client.images.pull, image)
            except Exception as e:
                # Try mirror if configured
                if self.mirror:
                    mirror_image = self._mirror_image(image)
                    try:
                        logger.info(f"Trying mirror for '{image}': {mirror_image}")
                        await loop.run_in_executor(None, client.images.pull, mirror_image)
                        if image != mirror_image:
                            await loop.run_in_executor(
                                None,
                                lambda: client.images.get(mirror_image).tag(image),
                            )
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

    async def _write_code_to_container_async(self, container, config: SandboxConfig) -> None:
        """Write source code and test code into the container securely using tar.

        This method uses Docker's put_archive API to securely write files,
        avoiding shell injection vulnerabilities of echo-based approaches.

        Args:
            container: Docker container.
            config: Sandbox configuration with code and test_code.
        """
        import io
        import tarfile

        ext_map = {
            "python": ".py",
            "cpp": ".cpp",
            "c++": ".cpp",
            "c": ".c",
            "java": "Main.java",
            "go": "main.go",
            "rust": "main.rs",
        }
        ext = ext_map.get(config.language, ".txt")

        # Determine filenames
        main_filename = f"main{ext}" if config.language != "java" else "Main.java"
        test_filename = f"test_main{ext}" if config.language != "java" else "TestMain.java"

        # Create tar archive in memory
        tar_stream = io.BytesIO()
        with tarfile.open(fileobj=tar_stream, mode="w:") as tar:
            # Add main code file
            if config.code:
                code_bytes = config.code.encode("utf-8")
                code_info = tarfile.TarInfo(name=main_filename)
                code_info.size = len(code_bytes)
                code_info.mode = 0o644
                tar.addfile(code_info, io.BytesIO(code_bytes))

            # Add test code file
            if config.test_code:
                test_bytes = config.test_code.encode("utf-8")
                test_info = tarfile.TarInfo(name=test_filename)
                test_info.size = len(test_bytes)
                test_info.mode = 0o644
                tar.addfile(test_info, io.BytesIO(test_bytes))

        tar_stream.seek(0)

        # Create working directory
        await self._exec_command(container, f"mkdir -p {config.working_dir}")

        # Extract tar archive into container
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: container.put_archive(config.working_dir, tar_stream),
        )

        logger.debug(f"Code written to container: {main_filename}, {test_filename}")

    async def _cleanup_container(self, container) -> None:
        """Safely remove a container.

        Args:
            container: Docker container to remove.
        """
        if container is None:
            return

        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: container.remove(force=True))
            logger.debug(f"Container cleaned up successfully")
        except Exception as e:
            logger.warning(f"Container cleanup failed: {e}")