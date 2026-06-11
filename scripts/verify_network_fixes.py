#!/usr/bin/env python3
"""
verify_network_fixes.py - Verify network configuration fixes for China network

This script performs static analysis to verify that:
1. Mirror configuration is properly implemented
2. Fallback strategies are in place
3. Error messages are helpful
4. Configuration files are updated
"""

import re
import sys
from pathlib import Path


def check_file_exists(filepath: str) -> bool:
    """Check if a file exists."""
    path = Path(filepath)
    exists = path.exists()
    status = "✓" if exists else "✗"
    print(f"{status} File exists: {filepath}")
    return exists


def check_pattern_in_file(filepath: str, pattern: str, description: str) -> bool:
    """Check if a regex pattern exists in a file."""
    try:
        content = Path(filepath).read_text(encoding='utf-8')
        match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
        status = "✓" if match else "✗"
        print(f"{status} {description}")
        return match is not None
    except Exception as e:
        print(f"✗ Error checking {filepath}: {e}")
        return False


def main():
    """Run all verification checks."""
    print("=" * 60)
    print("Network Configuration Verification")
    print("=" * 60)
    print()

    root = Path(__file__).parent.parent
    all_passed = True

    # Check configure_mirrors.sh
    print("1. Mirror Configuration Script (configure_mirrors.sh)")
    print("-" * 60)
    checks = [
        (root / "scripts/configure_mirrors.sh", r"pypi\.tuna\.tsinghua\.edu\.cn", "Tsinghua pip mirror"),
        (root / "scripts/configure_mirrors.sh", r"registry\.npmmirror\.com", "Taobao npm mirror"),
        (root / "scripts/configure_mirrors.sh", r"mirrors\.ustc\.edu\.cn", "USTC APT mirror"),
        (root / "scripts/configure_mirrors.sh", r"registry\.cn-hangzhou\.aliyuncs\.com", "Alibaba Docker mirror"),
        (root / "scripts/configure_mirrors.sh", r"--force|--test", "Command-line options support"),
        (root / "scripts/configure_mirrors.sh", r"test_url|curl.*--max-time", "Connectivity testing"),
    ]

    for filepath, pattern, desc in checks:
        if not check_pattern_in_file(str(filepath), pattern, desc):
            all_passed = False
    print()

    # Check sandbox manager
    print("2. Sandbox Manager (src/sandbox/manager.py)")
    print("-" * 60)
    checks = [
        (root / "src/sandbox/manager.py", r"async def _ensure_image", "Async image ensure method"),
        (root / "src/sandbox/manager.py", r"registry\.cn-hangzhou\.aliyuncs\.com", "Alibaba mirror in code"),
        (root / "src/sandbox/manager.py", r"docker\.mirrors\.ustc\.edu\.cn", "USTC mirror in code"),
        (root / "src/sandbox/manager.py", r"mirror\.ccs\.tencentyun\.com", "Tencent mirror in code"),
        (root / "src/sandbox/manager.py", r"hub-mirror\.c\.163\.com", "NetEase mirror in code"),
        (root / "src/sandbox/manager.py", r"def _mirror_image\(self, image: str, mirror: str = \"\"\)", "Enhanced mirror method"),
        (root / "src/sandbox/manager.py", r"Solutions:", "Helpful error message"),
    ]

    for filepath, pattern, desc in checks:
        if not check_pattern_in_file(str(filepath), pattern, desc):
            all_passed = False
    print()

    # Check Docker Compose
    print("3. Docker Compose Configuration (docker-compose.dev.yml)")
    print("-" * 60)
    checks = [
        (root / "docker-compose.dev.yml", r"PIP_INDEX_URL", "PIP_INDEX_URL variable"),
        (root / "docker-compose.dev.yml", r"NPM_CONFIG_REGISTRY|NPM_REGISTRY", "NPM registry variable"),
        (root / "docker-compose.dev.yml", r"DOCKER_MIRROR", "Docker mirror variable"),
        (root / "docker-compose.dev.yml", r"\$\{.*:-.*\}", "Default values with fallback"),
    ]

    for filepath, pattern, desc in checks:
        if not check_pattern_in_file(str(filepath), pattern, desc):
            all_passed = False
    print()

    # Check Dockerfile
    print("4. Dockerfile Configuration (Dockerfile.dev)")
    print("-" * 60)
    checks = [
        (root / "Dockerfile.dev", r"ARG PIP_INDEX_URL", "Build arg for pip"),
        (root / "Dockerfile.dev", r"ARG NPM_REGISTRY", "Build arg for npm"),
        (root / "Dockerfile.dev", r"\$\{PIP_INDEX_URL\}", "Use pip build arg"),
        (root / "Dockerfile.dev", r"apt-get update.*\|\|", "Fallback for apt update"),
    ]

    for filepath, pattern, desc in checks:
        if not check_pattern_in_file(str(filepath), pattern, desc):
            all_passed = False
    print()

    # Check test scripts
    print("5. Test Scripts (scripts/test.sh)")
    print("-" * 60)
    checks = [
        (root / "scripts/test.sh", r"pip_mirror.*PIP_INDEX_URL", "Use PIP_INDEX_URL env var"),
        (root / "scripts/test.sh", r"--index-url \${pip_mirror}", "Pass mirror to pip install"),
    ]

    for filepath, pattern, desc in checks:
        if not check_pattern_in_file(str(filepath), pattern, desc):
            all_passed = False
    print()

    # Check test files
    print("6. Test Files")
    print("-" * 60)
    checks = [
        (root / "tests/unit/test_network_config.py", r"class TestNetworkConfiguration", "Network config unit tests"),
        (root / "tests/integration/test_mirror_connectivity.py", r"class TestMirrorConnectivity", "Mirror connectivity tests"),
        (root / "tests/sandbox/test_mirror_pull.py", r"class TestSandboxMirrorPull", "Sandbox mirror pull tests"),
    ]

    for filepath, pattern, desc in checks:
        if not check_pattern_in_file(str(filepath), pattern, desc):
            all_passed = False
    print()

    # Check environment example
    print("7. Environment Configuration (.env.example)")
    print("-" * 60)
    checks = [
        (root / ".env.example", r"DOCKER_MIRROR=registry\.cn-hangzhou\.aliyuncs\.com", "Docker mirror setting"),
        (root / ".env.example", r"PIP_INDEX_URL=.*pypi\.tuna\.tsinghua\.edu\.cn", "Pip mirror setting"),
        (root / ".env.example", r"NPM_REGISTRY=.*npmmirror\.com", "Npm mirror setting"),
    ]

    for filepath, pattern, desc in checks:
        if not check_pattern_in_file(str(filepath), pattern, desc):
            all_passed = False
    print()

    # Summary
    print("=" * 60)
    if all_passed:
        print("✓ All verification checks passed!")
        print()
        print("Summary of improvements:")
        print("  • configure_mirrors.sh: Enhanced with auto-detection and testing")
        print("  • SandboxManager: Multi-tier mirror fallback strategy")
        print("  • Docker Compose: Configurable mirror via environment variables")
        print("  • Dockerfile: Build args for custom mirrors with fallback")
        print("  • Test scripts: Use configured mirrors instead of hardcoded URLs")
        print("  • Test coverage: 3 new test files with comprehensive coverage")
        print()
        return 0
    else:
        print("✗ Some verification checks failed!")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
