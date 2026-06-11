"""Tests for Docker sandbox manager."""

import pytest
from src.sandbox.manager import SandboxConfig, SandboxManager


@pytest.mark.asyncio
async def test_sandbox_config_defaults():
    """Test SandboxConfig default values."""
    config = SandboxConfig()
    assert config.language == "python"
    assert config.timeout == 300
    assert config.max_memory == "512m"
    assert config.network_disabled is True


@pytest.mark.asyncio
async def test_sandbox_config_custom():
    """Test SandboxConfig with custom values."""
    config = SandboxConfig(
        language="cpp",
        timeout=60,
        max_memory="1g",
        max_cpu=4.0,
    )
    assert config.language == "cpp"
    assert config.timeout == 60
    assert config.max_memory == "1g"
    assert config.max_cpu == 4.0


@pytest.mark.asyncio
async def test_default_image_mapping():
    """Test default Docker image mapping for languages."""
    manager = SandboxManager()

    assert manager._default_image("python") == "python:3.11-slim"
    assert manager._default_image("cpp") == "gcc:latest"
    assert manager._default_image("java") == "openjdk:17-slim"
    assert manager._default_image("unknown") == "python:3.11-slim"


@pytest.mark.asyncio
async def test_mirror_image_conversion():
    """Test mirror image URL conversion."""
    manager = SandboxManager(mirror="registry.cn-hangzhou.aliyuncs.com")

    # Test with official image
    mirrored = manager._mirror_image("python:3.11-slim")
    assert mirrored == "registry.cn-hangzhou.aliyuncs.com/python:3.11-slim"

    # Test with already prefixed image
    mirrored = manager._mirror_image("library/python:3.11-slim")
    assert mirrored == "registry.cn-hangzhou.aliyuncs.com/python:3.11-slim"


@pytest.mark.asyncio
async def test_mirror_disabled():
    """Test mirror conversion when mirror is disabled."""
    manager = SandboxManager()
    mirrored = manager._mirror_image("python:3.11-slim")
    assert mirrored == "python:3.11-slim"


@pytest.mark.skip(reason="Requires Docker daemon - run in container only")
@pytest.mark.asyncio
async def test_sandbox_execution_python():
    """Test Python code execution in sandbox."""
    manager = SandboxManager()
    config = SandboxConfig(
        language="python",
        code="print('Hello from sandbox!')",
        test_command="python /tmp/autotest/main.py",
        timeout=10,
    )

    result = await manager.create_and_run(config)
    assert result.exit_code == 0
    assert "Hello from sandbox!" in result.stdout


@pytest.mark.skip(reason="Requires Docker daemon - run in container only")
@pytest.mark.asyncio
async def test_sandbox_timeout_enforcement():
    """Test that sandbox enforces timeout limits."""
    manager = SandboxManager()
    config = SandboxConfig(
        language="python",
        code="import time; time.sleep(100)",
        test_command="python /tmp/autotest/main.py",
        timeout=2,
    )

    result = await manager.create_and_run(config)
    assert result.timed_out is True


@pytest.mark.skip(reason="Requires Docker daemon - run in container only")
@pytest.mark.asyncio
async def test_sandbox_resource_limits():
    """Test that sandbox applies resource limits."""
    manager = SandboxManager()
    config = SandboxConfig(
        language="python",
        code="print('Resource limited')",
        test_command="python /tmp/autotest/main.py",
        max_memory="128m",
        max_cpu=0.5,
    )

    result = await manager.create_and_run(config)
    assert result.exit_code == 0
