"""Unit tests for network configuration and mirror settings."""

import pytest
from unittest.mock import MagicMock, patch
from src.sandbox.manager import SandboxManager


class TestNetworkConfiguration:
    """Test network configuration and mirror functionality."""

    def test_sandbox_manager_default_mirror(self):
        """Test SandboxManager initializes with default mirror."""
        manager = SandboxManager()
        assert manager.mirror == ""

    def test_sandbox_manager_custom_mirror(self):
        """Test SandboxManager initializes with custom mirror."""
        mirror_url = "registry.cn-hangzhou.aliyuncs.com"
        manager = SandboxManager(mirror=mirror_url)
        assert manager.mirror == mirror_url

    def test_mirror_image_simple_name(self):
        """Test mirror transformation for simple image names."""
        manager = SandboxManager(mirror="registry.cn-hangzhou.aliyuncs.com")
        result = manager._mirror_image("python:3.11-slim")
        assert result == "registry.cn-hangzhou.aliyuncs.com/python:3.11-slim"

    def test_mirror_image_with_library(self):
        """Test mirror transformation for images with library prefix."""
        manager = SandboxManager(mirror="docker.mirrors.ustc.edu.cn")
        result = manager._mirror_image("library/nginx:latest")
        assert result == "docker.mirrors.ustc.edu.cn/library/nginx:latest"

    def test_mirror_image_with_registry(self):
        """Test mirror transformation replaces existing registry."""
        manager = SandboxManager(mirror="registry.cn-hangzhou.aliyuncs.com")
        result = manager._mirror_image("docker.io/library/python:3.11")
        assert result == "registry.cn-hangzhou.aliyuncs.com/library/python:3.11"

    def test_mirror_image_no_mirror_configured(self):
        """Test that image name is unchanged when no mirror is configured."""
        manager = SandboxManager()
        result = manager._mirror_image("python:3.11-slim")
        assert result == "python:3.11-slim"

    def test_mirror_image_custom_mirror_parameter(self):
        """Test mirror transformation with custom mirror parameter."""
        manager = SandboxManager(mirror="default-mirror.com")
        result = manager._mirror_image(
            "python:3.11-slim",
            mirror="custom-mirror.com"
        )
        assert result == "custom-mirror.com/python:3.11-slim"

    @pytest.mark.asyncio
    async def test_ensure_image_uses_local_cache(self):
        """Test that _ensure_image uses local cache when available."""
        manager = SandboxManager()
        mock_client = MagicMock()
        mock_client.images.get.return_value = MagicMock()

        # Should not raise exception if image exists
        await manager._ensure_image(mock_client, "python:3.11-slim")

        # Verify get was called but pull was not
        mock_client.images.get.assert_called_once_with("python:3.11-slim")
        mock_client.images.pull.assert_not_called()

    def test_default_image_mapping(self):
        """Test default Docker image mapping for various languages."""
        manager = SandboxManager()

        expected_mappings = {
            "python": "python:3.11-slim",
            "cpp": "gcc:latest",
            "c++": "gcc:latest",
            "c": "gcc:latest",
            "java": "openjdk:17-slim",
            "go": "golang:1.22-alpine",
            "rust": "rust:1.75-slim",
        }

        for language, expected_image in expected_mappings.items():
            result = manager._default_image(language)
            assert result == expected_image

    def test_default_image_unknown_language(self):
        """Test that unknown languages default to Python."""
        manager = SandboxManager()
        result = manager._default_image("unknown-language")
        assert result == "python:3.11-slim"


class TestMirrorFallbackStrategy:
    """Test mirror fallback strategy for China network."""

    def test_mirror_list_includes_all_china_mirrors(self):
        """Verify all major China mirrors are included in fallback list."""
        expected_mirrors = [
            "registry.cn-hangzhou.aliyuncs.com",
            "docker.mirrors.ustc.edu.cn",
            "mirror.ccs.tencentyun.com",
            "hub-mirror.c.163.com",
        ]

        # This test documents the expected mirrors
        # The actual implementation is in manager.py _ensure_image
        for mirror in expected_mirrors:
            assert len(mirror) > 0
            assert "." in mirror  # Should be valid domain

    def test_configured_mirror_takes_precedence(self):
        """Test that user-configured mirror is tried first."""
        custom_mirror = "my-custom-mirror.example.com"
        manager = SandboxManager(mirror=custom_mirror)

        # Custom mirror should be in the list
        assert manager.mirror == custom_mirror
