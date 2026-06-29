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
    # Multi-file support: relative_path -> content mapping
    files: dict[str, str] = field(default_factory=dict)


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

        Images are prefixed with DaoCloud mirror for China network compatibility.
        The _ensure_image method will handle multi-tier fallback if this mirror fails.

        Args:
            language: Language identifier.

        Returns:
            Docker image name with mirror prefix.
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
        base_image = mapping.get(language, "python:3.11-slim")

        # If mirror is configured, prepend it to the image name
        if self.mirror:
            return self._mirror_image(base_image, self.mirror)
        return base_image

    async def _ensure_image(self, client: docker.DockerClient, image: str) -> None:
        """Ensure Docker image is available (pull if needed).

        This method implements a multi-tier fallback strategy for China network:
        1. Check local cache
        2. Pull from official registry
        3. Try configured mirror registries (Alibaba, USTC, Tencent, NetEase)
        4. Try alternative mirrors in sequence

        Args:
            client: Docker client.
            image: Image name to ensure.

        Raises:
            RuntimeError: If all pull attempts fail.
        """
        loop = asyncio.get_event_loop()

        # Step 1: Check if image exists locally
        try:
            await loop.run_in_executor(None, client.images.get, image)
            logger.debug(f"Image '{image}' already present locally")
            return
        except ImageNotFound:
            logger.info(f"Image '{image}' not found locally, will pull...")

        # Step 2: Define mirror strategy
        mirrors_to_try = []

        # Add configured mirror if set
        if self.mirror:
            mirrors_to_try.append(self.mirror)

        # Add default China mirrors for fallback (priority order for 2026+)
        default_mirrors = [
            "docker.m.daocloud.io",           # DaoCloud (most stable, recommended)
            "dockerproxy.com",                # International proxy
            "registry.cn-hangzhou.aliyuncs.com",  # Alibaba Cloud (legacy)
            "docker.mirrors.ustc.edu.cn",     # USTC (education network)
            "mirror.ccs.tencentyun.com",      # Tencent Cloud
        ]

        # Add mirrors that aren't already in the list
        for mirror in default_mirrors:
            if mirror not in mirrors_to_try:
                mirrors_to_try.append(mirror)

        # Step 3: Try pulling with mirrors
        last_error = None

        # First, try direct pull (might work if Docker daemon has mirror configured)
        try:
            logger.info(f"Attempting direct pull of '{image}'...")
            await loop.run_in_executor(None, client.images.pull, image)
            logger.info(f"Successfully pulled '{image}' directly")
            return
        except Exception as e:
            logger.warning(f"Direct pull failed: {e}")
            last_error = e

        # Then try each mirror in sequence
        for mirror in mirrors_to_try:
            mirror_image = self._mirror_image(image, mirror)
            try:
                logger.info(f"Trying mirror '{mirror}' for '{image}': {mirror_image}")
                await loop.run_in_executor(None, client.images.pull, mirror_image)

                # Tag the mirror image with the original name
                if image != mirror_image:
                    mirror_img_obj = await loop.run_in_executor(
                        None, client.images.get, mirror_image
                    )
                    await loop.run_in_executor(
                        None,
                        lambda: mirror_img_obj.tag(image),
                    )
                    logger.info(f"Tagged '{mirror_image}' as '{image}'")

                logger.info(f"Successfully pulled '{image}' via mirror '{mirror}'")
                return

            except Exception as e:
                logger.warning(f"Mirror '{mirror}' failed: {e}")
                last_error = e
                continue

        # All attempts failed
        error_msg = (
            f"Failed to pull image '{image}'. Tried:\n"
            f"  - Direct pull\n"
        )
        if self.mirror:
            error_msg += f"  - Configured mirror: {self.mirror}\n"
        error_msg += f"  - Default mirrors: {', '.join(default_mirrors)}\n"
        error_msg += f"\nLast error: {last_error}\n\n"
        error_msg += (
            "Solutions:\n"
            "  1. Configure Docker daemon with registry mirrors in /etc/docker/daemon.json\n"
            "  2. Run 'bash scripts/configure_mirrors.sh' to auto-configure\n"
            "  3. Manually pull the image: docker pull <mirror>/<image>\n"
            "  4. Check network connectivity and firewall settings"
        )

        raise RuntimeError(error_msg)

    def _mirror_image(self, image: str, mirror: str = "") -> str:
        """Convert image name to use a specific mirror registry.

        This method transforms Docker image names to use mirror registries.
        For example:
          - python:3.11-slim → registry.cn-hangzhou.aliyuncs.com/python:3.11-slim
          - library/nginx:latest → registry.cn-hangzhou.aliyuncs.com/library/nginx:latest

        Args:
            image: Original image name (e.g., "python:3.11-slim").
            mirror: Mirror registry URL. If empty, uses self.mirror.

        Returns:
            Mirror-prefixed image name.
        """
        target_mirror = mirror or self.mirror
        if not target_mirror:
            return image

        # Handle images with explicit registry (e.g., docker.io/library/python:3.11)
        if "/" in image:
            parts = image.split("/", 1)
            # If already has a registry (contains dot), replace it
            if "." in parts[0]:
                return f"{target_mirror}/{parts[-1]}"
            # Otherwise just prepend mirror
            return f"{target_mirror}/{image}"

        # Simple image name (e.g., "python:3.11-slim")
        # For official Docker Hub images, add /library/ prefix
        if ":" in image:
            image_name = image.split(":")[0]
            tag = image.split(":")[1]
        else:
            image_name = image
            tag = "latest"
        
        # Official Docker Hub images need /library/ prefix
        official_images = ["python", "gcc", "openjdk", "golang", "rust", "node", "ruby", "java", "postgres", "redis", "nginx"]
        if image_name in official_images:
            return f"{target_mirror}/library/{image_name}:{tag}"
        
        return f"{target_mirror}/{image}"

    async def _write_code_to_container_async(self, container, config: SandboxConfig) -> None:
        """Write source code and test code into the container securely using tar.

        Supports both single-file mode (code/test_code) and multi-file mode (files dict).
        In multi-file mode, the files dict maps relative paths to file content,
        allowing complete project directory structures to be deployed.

        Args:
            container: Docker container.
            config: Sandbox configuration with code, test_code, and/or files.
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

        # Create tar archive in memory
        tar_stream = io.BytesIO()
        with tarfile.open(fileobj=tar_stream, mode="w:") as tar:
            # Multi-file mode: write files with directory structure
            if config.files:
                for rel_path, content in config.files.items():
                    # Skip empty content
                    if not content:
                        continue
                    content_bytes = content.encode("utf-8")
                    tar_info = tarfile.TarInfo(name=rel_path)
                    tar_info.size = len(content_bytes)
                    tar_info.mode = 0o644
                    tar.addfile(tar_info, io.BytesIO(content_bytes))

            # Single-file mode (backward compatible)
            else:
                # Determine filenames
                main_filename = f"main{ext}" if config.language != "java" else "Main.java"
                test_filename = f"test_main{ext}" if config.language != "java" else "TestMain.java"

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

        # Create working directory and subdirectories
        mkdir_result = await self._exec_command(container, f"mkdir -p {config.working_dir}", workdir="/")
        if mkdir_result.exit_code != 0:
            raise RuntimeError(f"Failed to create working directory: {mkdir_result.stderr}")

        # For multi-file projects, create necessary subdirectories
        if config.files:
            from pathlib import Path
            subdirs = set()
            for rel_path in config.files.keys():
                parent = str(Path(rel_path).parent)
                if parent and parent != ".":
                    subdirs.add(parent)
            for subdir in sorted(subdirs):
                full_path = f"{config.working_dir}/{subdir}"
                await self._exec_command(container, f"mkdir -p {full_path}", workdir="/")

        # Small delay to ensure directories are created
        await asyncio.sleep(0.1)

        # Extract tar archive into container
        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(
                None,
                lambda: container.put_archive(config.working_dir, tar_stream),
            )
        except Exception as e:
            raise RuntimeError(f"Failed to write code to container: {e}")

        if config.files:
            logger.debug(f"Multi-file code written to container: {len(config.files)} files")
        else:
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