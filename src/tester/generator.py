"""Test case generator — creates executable tests via LLM."""

import json
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class GeneratedTestCase:
    """A single generated test case."""

    id: str = ""
    description: str = ""
    category: str = ""  # happy_path, boundary, null_handling, error_handling, performance
    priority: str = "medium"
    test_code: str = ""  # Actual executable test code
    language: str = ""
    framework: str = ""


@dataclass
class GeneratedTestSuite:
    """Collection of generated test cases."""

    language: str = ""
    framework: str = ""
    test_cases: list[GeneratedTestCase] = field(default_factory=list)

    def to_text(self) -> str:
        """Combine all test cases into a single runnable string."""
        return "\n\n".join(tc.test_code for tc in self.test_cases)


class TestCaseGenerator:
    """Generates executable test cases using LLM providers."""

    @classmethod
    async def generate(
        cls,
        code: str,
        language: str,
        framework: str = "",
        num_cases: int = 5,
        provider_manager=None,
    ) -> GeneratedTestSuite:
        """Generate test cases for given code.

        Args:
            code: Source code to test.
            language: Programming language.
            framework: Test framework (e.g., pytest, Google Test, JUnit 5).
            num_cases: Number of test cases to generate.
            provider_manager: LLM provider manager.

        Returns:
            GeneratedTestSuite with executable test code.
        """
        from src.llm.base import BaseProvider
        from src.llm.prompt_templates.test_generation import test_generation_prompt

        if provider_manager is None:
            from src.llm.provider import get_provider_manager
            provider_manager = get_provider_manager()

        framework = framework or cls._default_framework(language)

        prompt = test_generation_prompt(
            language=language,
            code=code,
            test_framework=framework,
            num_cases=num_cases,
        )

        try:
            response = await provider_manager.chat_with_fallback(
                messages=[BaseProvider.user(prompt)],
                temperature=0.3,
                max_tokens=8192,
            )

            content = response.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            data = json.loads(content)
            test_cases = [
                GeneratedTestCase(
                    id=tc.get("id", f"TC-{i+1:03d}"),
                    description=tc.get("description", ""),
                    category=tc.get("category", "happy_path"),
                    priority=tc.get("priority", "medium"),
                    test_code=tc.get("test_code", ""),
                    language=language,
                    framework=framework,
                )
                for i, tc in enumerate(data.get("test_cases", []))
            ]

            return GeneratedTestSuite(
                language=language,
                framework=framework,
                test_cases=test_cases,
            )
        except Exception as e:
            logger.error(f"Test generation failed: {e}")
            return GeneratedTestSuite(language=language, framework=framework)

    @classmethod
    async def expand(
        cls,
        code: str,
        existing_test_cases: str,
        language: str,
        framework: str = "",
        provider_manager=None,
    ) -> GeneratedTestSuite:
        """Expand existing user-provided test cases.

        Args:
            code: Source code.
            existing_test_cases: User-provided test case examples.
            language: Programming language.
            framework: Test framework.
            provider_manager: LLM provider.

        Returns:
            GeneratedTestSuite with additional test cases.
        """
        from src.llm.base import BaseProvider
        from src.llm.prompt_templates.test_generation import test_expansion_prompt

        if provider_manager is None:
            from src.llm.provider import get_provider_manager
            provider_manager = get_provider_manager()

        prompt = test_expansion_prompt(
            language=language,
            code=code,
            existing_test_cases=existing_test_cases,
            test_framework=framework or cls._default_framework(language),
        )

        try:
            response = await provider_manager.chat_with_fallback(
                messages=[BaseProvider.user(prompt)],
                temperature=0.3,
                max_tokens=8192,
            )

            content = response.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()

            data = json.loads(content)
            test_cases = [
                GeneratedTestCase(
                    id=tc.get("id", f"TC-EX-{i+1:03d}"),
                    description=tc.get("description", ""),
                    category=tc.get("category", "happy_path"),
                    priority=tc.get("priority", "medium"),
                    test_code=tc.get("test_code", ""),
                    language=language,
                    framework=framework,
                )
                for i, tc in enumerate(data.get("test_cases", []))
            ]
            return GeneratedTestSuite(language=language, framework=framework, test_cases=test_cases)
        except Exception as e:
            logger.error(f"Test expansion failed: {e}")
            return GeneratedTestSuite(language=language, framework=framework)

    @staticmethod
    def _default_framework(language: str) -> str:
        """Get default test framework for a language."""
        mapping = {"python": "pytest", "cpp": "Google Test", "c": "CTest", "java": "JUnit 5"}
        return mapping.get(language, "pytest")