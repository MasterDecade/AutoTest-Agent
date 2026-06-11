"""Sandbox tests for Docker image pulling with mirror support."""

import pytest
from unittest.mock import MagicMock, patch
from src.sandbox.manager import SandboxManager, SandboxConfig


class TestSandboxMirrorPull:
    """Test sandbox container creation with mirror-pulled images."""

    @pytest.mark.asyncio
    async def test_create_sandbox_with_local_image(self):
        """Test sandbox creation when image is already local."""
        manager = SandboxManager(mirror="registry.cn-hangzhou.aliyuncs.com")

        mock_client = MagicMock()
        mock_container = MagicMock()
        mock_client.containers.run.return_value = mock_container

        # Mock successful exec commands
        mock_container.exec_run.return_value = MagicMock(
            exit_code=0,
            output=b"Test passed"
        )

        config = SandboxConfig(
            language="python",
            code="print('Hello')",
            test_command="python main.py"
        )

        # Should succeed without pulling
        result = await manager.create_and_run(config)

        # Container should be created and run
        assert mock_client.containers.run.called

    @pytest.mark.asyncio
    async def test_create_sandbox_triggers_mirror_pull(self):
        """Test that missing image triggers pull via mirror."""
        manager = SandboxManager(mirror="registry.cn-hangzhou.aliyuncs.com")

        mock_client = MagicMock()

        # Image not found locally
        mock_client.images.get.side_effect = [
            Exception("Not found"),  # First call in _ensure_image
            MagicMock(),  # Second call after pull (for tagging)
        ]

        # Pull succeeds
        mock_client.images.pull.return_value = MagicMock()

        # Mock container operations
        mock_container = MagicMock()
        mock_client.containers.run.return_value = mock_container
        mock_container.exec_run.return_value = MagicMock(
            exit_code=0,
            output=b"Success"
        )

        # Mock image object for tagging
        mock_image_obj = MagicMock()
        mock_image_obj.tag.return_value = True
        mock_client.images.get.return_value = mock_image_obj

        config = SandboxConfig(
            language="python",
            code="print('test')",
            test_command="python main.py"
        )

        # Should succeed by pulling via mirror
        result = await manager.create_and_run(config)
        assert result.exit_code == 0

    @pytest.mark.asyncio
    async def test_sandbox_with_custom_image(self):
        """Test sandbox creation with custom Docker image."""
        manager = SandboxManager(mirror="docker.mirrors.ustc.edu.cn")

        mock_client = MagicMock()
        mock_client.images.get.return_value = MagicMock()  # Image exists

        mock_container = MagicMock()
        mock_client.containers.run.return_value = mock_container
        mock_container.exec_run.return_value = MagicMock(
            exit_code=0,
            output=b"Custom image test passed"
        )

        config = SandboxConfig(
            language="python",
            image="my-custom-image:latest",
            code="print('custom')",
            test_command="python main.py"
        )

        result = await manager.create_and_run(config)
        assert result.exit_code == 0

        # Verify custom image was used
        call_args = mock_client.containers.run.call_args
        assert "my-custom-image:latest" in str(call_args)

    @pytest.mark.asyncio
    async def test_sandbox_cleanup_after_execution(self):
        """Test that sandbox containers are properly cleaned up."""
        manager = SandboxManager()

        mock_client = MagicMock()
        mock_client.images.get.return_value = MagicMock()

        mock_container = MagicMock()
        mock_client.containers.run.return_value = mock_container
        mock_container.exec_run.return_value = MagicMock(
            exit_code=0,
            output=b"Test"
        )

        config = SandboxConfig(
            language="python",
            code="pass",
            test_command="echo test"
        )

        await manager.create_and_run(config)

        # Verify cleanup was called
        assert mock_container.remove.called
        assert mock_container.remove.call_args[1]["force"] is True

    @pytest.mark.asyncio
    async def test_multiple_language_sandboxes(self):
        """Test sandbox creation for multiple programming languages."""
        manager = SandboxManager(mirror="registry.cn-hangzhou.aliyuncs.com")

        languages = ["python", "java", "go", "cpp"]

        for lang in languages:
            mock_client = MagicMock()
            mock_client.images.get.return_value = MagicMock()

            mock_container = MagicMock()
            mock_client.containers.run.return_value = mock_container
            mock_container.exec_run.return_value = MagicMock(
                exit_code=0,
                output=f"{lang} test passed".encode()
            )

            config = SandboxConfig(
                language=lang,
                code="dummy code",
                test_command="echo test"
            )

            # Should not raise exception
            result = await manager.create_and_run(config)
            assert result.exit_code == 0


class TestMirrorErrorHandling:
    """Test error handling in mirror pull scenarios."""

    @pytest.mark.asyncio
    async def test_graceful_failure_when_all_mirrors_fail(self):
        """Test graceful error when all mirrors fail."""
        manager = SandboxManager(mirror="registry.cn-hangzhou.aliyuncs.com")

        mock_client = MagicMock()
        mock_client.images.get.side_effect = Exception("Not found")
        mock_client.images.pull.side_effect = Exception("Connection refused")

        config = SandboxConfig(
            language="python",
            code="print('test')",
            test_command="python main.py"
        )

        # Should raise RuntimeError with helpful message
        with pytest.raises(RuntimeError) as exc_info:
            await manager.create_and_run(config)

        error_msg = str(exc_info.value)
        assert "Failed to pull image" in error_msg
        assert "Solutions:" in error_msg or "configure" in error_msg.lower()

    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test timeout handling during image pull."""
        manager = SandboxManager()

        mock_client = MagicMock()
        mock_client.images.get.side_effect = Exception("Timeout")
        mock_client.images.pull.side_effect = Exception("Read timed out")

        with pytest.raises(RuntimeError):
            await manager._ensure_image(mock_client, "python:3.11-slim")
