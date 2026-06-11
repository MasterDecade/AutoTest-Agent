"""Pytest configuration and fixtures for AutoTest-Agent tests.

Provides shared fixtures for database, Redis, and test utilities.
All fixtures are designed to work in Dockerized environments.
"""

import os
import pytest
from typing import Generator


# ===== Environment Setup =====
@pytest.fixture(autouse=True)
def setup_test_env():
    """Setup test environment variables."""
    os.environ["DATABASE_URL"] = "postgresql+asyncpg://autotest:autotest_dev@postgres:5432/autotest_dev"
    os.environ["REDIS_URL"] = "redis://redis:6379/0"
    os.environ["DEBUG"] = "true"
    os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only-1234567890"
    os.environ["API_KEY_ENCRYPTION_KEY"] = "test-encryption-key-for-testing-1234567890"
    yield
    # Cleanup if needed


# ===== Database Fixtures =====
@pytest.fixture(scope="session")
def test_database_url() -> str:
    """Return test database URL."""
    return "postgresql+asyncpg://autotest:autotest_dev@postgres:5432/autotest_dev"


@pytest.fixture
def sample_code_python() -> str:
    """Sample Python code for testing."""
    return '''
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b

if __name__ == "__main__":
    print(add(2, 3))
'''


@pytest.fixture
def sample_code_cpp() -> str:
    """Sample C++ code for testing."""
    return '''
#include <iostream>

int add(int a, int b) {
    return a + b;
}

int main() {
    std::cout << add(2, 3) << std::endl;
    return 0;
}
'''


@pytest.fixture
def sample_code_java() -> str:
    """Sample Java code for testing."""
    return '''
public class Main {
    public static int add(int a, int b) {
        return a + b;
    }

    public static void main(String[] args) {
        System.out.println(add(2, 3));
    }
}
'''


# ===== Test Data Fixtures =====
@pytest.fixture
def valid_submission_data() -> dict:
    """Valid submission data for API tests."""
    return {
        "project_id": "test-project-123",
        "submitter_name": "Test User",
        "code_content": "print('Hello, World!')",
        "language": "python",
        "file_name": "test.py",
    }


@pytest.fixture
def valid_llm_config() -> dict:
    """Valid LLM configuration for testing."""
    return {
        "provider_type": "openai",
        "api_key": "sk-test-key-1234567890",
        "model_name": "gpt-4o",
        "api_base": "",
    }


# ===== Helper Functions =====
@pytest.fixture
def create_temp_file(tmp_path):
    """Create a temporary file with given content."""
    def _create(filename: str, content: str):
        file_path = tmp_path / filename
        file_path.write_text(content)
        return str(file_path)
    return _create
