"""Integration tests for mirror connectivity and Docker image pulling."""

import pytest
import docker
from unittest.mock import MagicMock, patch, AsyncMock
from src.sandbox.manager import SandboxManager


class TestMirrorConnectivity:
    """Test connectivity to various Docker registry mirrors."""

    @pytest.mark.asyncio
    async def test_pull_with_alibaba_mirror(self):
        """Test pulling image using Alibaba Cloud mirror."""
        manager = SandboxManager(mirror="registry.cn-hangzhou.aliyuncs.com")

        # Mock Docker client
        mock_client = MagicMock()
        mock_client.images.get.side_effect = docker.errors.ImageNotFound("Image not found")

        # Mock successful pull
        mock_client.images.pull.return_value = MagicMock()
        mock_image = MagicMock()
        mock_image.tag.return_value = True
        mock_client.images.get.return_value = mock_image

        # Should succeed without raising exception
        await manager._ensure_image(mock_client, "python:3.11-slim")

        # Verify mirror was used
        assert mock_client.images.pull.called

    @pytest.mark.asyncio
    async def test_pull_with_ustc_mirror(self):
        """Test pulling image using USTC mirror."""
        manager = SandboxManager(mirror="docker.mirrors.ustc.edu.cn")

        mock_client = MagicMock()
        mock_client.images.get.side_effect = docker.errors.ImageNotFound("Image not found")
        mock_client.images.pull.return_value = MagicMock()

        mock_image = MagicMock()
        mock_image.tag.return_value = True
        mock_client.images.get.return_value = mock_image

        await manager._ensure_image(mock_client, "python:3.11-slim")
        assert mock_client.images.pull.called

    @pytest.mark.asyncio
    async def test_pull_failure_with_all_mirrors(self):
        """Test that appropriate error is raised when all mirrors fail."""
        manager = SandboxManager(mirror="registry.cn-hangzhou.aliyuncs.com")

        mock_client = MagicMock()
        mock_client.images.get.side_effect = docker.errors.ImageNotFound("Image not found")
        mock_client.images.pull.side_effect = Exception("Connection timeout")

        with pytest.raises(RuntimeError) as exc_info:
            await manager._ensure_image(mock_client, "python:3.11-slim")

        # Error message should mention fallback strategy
        assert "Failed to pull image" in str(exc_info.value)
        assert "Tried:" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_direct_pull_success(self):
        """Test that direct pull is attempted first before mirrors."""
        manager = SandboxManager(mirror="registry.cn-hangzhou.aliyuncs.com")

        mock_client = MagicMock()
        mock_client.images.get.side_effect = docker.errors.ImageNotFound("Image not found")
        # Direct pull succeeds
        mock_client.images.pull.return_value = MagicMock()

        await manager._ensure_image(mock_client, "python:3.11-slim")

        # Direct pull should be called first
        calls = mock_client.images.pull.call_args_list
        assert len(calls) >= 1
        # First call should be the original image name
        assert calls[0][0][0] == "python:3.11-slim"

    @pytest.mark.asyncio
    async def test_mirror_tagging_behavior(self):
        """Test that mirror images are properly tagged with original name."""
        manager = SandboxManager(mirror="registry.cn-hangzhou.aliyuncs.com")

        mock_client = MagicMock()
        mock_client.images.get.side_effect = [
            docker.errors.ImageNotFound("Not found"),  # Original not found
            MagicMock(),  # Mirror image object
        ]

        mock_pull_result = MagicMock()
        mock_client.images.pull.return_value = mock_pull_result

        mock_image_obj = MagicMock()
        mock_image_obj.tag.return_value = True
        mock_client.images.get.return_value = mock_image_obj

        await manager._ensure_image(mock_client, "python:3.11-slim")

        # Verify tagging was called
        assert mock_image_obj.tag.called
        tag_call = mock_image_obj.tag.call_args
        assert tag_call[0][0] == "python:3.11-slim"


class TestConfigurationIntegration:
    """Test configuration integration with settings."""

    def test_settings_docker_mirror_default(self):
        """Test that Settings has default Docker mirror configured."""
        from src.common.config import get_settings
        settings = get_settings()
        assert settings.docker_mirror == "registry.cn-hangzhou.aliyuncs.com"

    def test_sandbox_manager_from_settings(self):
        """Test creating SandboxManager with mirror from settings."""
        from src.common.config import get_settings
        settings = get_settings()

        manager = SandboxManager(mirror=settings.docker_mirror)
        assert manager.mirror == settings.docker_mirror

    def test_pip_mirror_url_in_settings(self):
        """Test that pip mirror URL is configured in settings."""
        from src.common.config import get_settings
        settings = get_settings()
        assert "pypi.tuna.tsinghua.edu.cn" in settings.pip_index_url or \
               "aliyun.com" in settings.pip_index_url

    def test_npm_registry_in_settings(self):
        """Test that npm registry is configured in settings."""
        from src.common.config import get_settings
        settings = get_settings()
        assert "npmmirror.com" in settings.npm_registry or \
               "taobao.org" in settings.npm_registry
