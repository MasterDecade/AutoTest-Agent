"""Prompt template for test case generation."""


def test_generation_prompt(
    language: str,
    code: str,
    test_framework: str = "",
    num_cases: int = 5,
    project_requirements: str = "",
) -> str:
    """Generate a prompt for creating test cases.

    Args:
        language: Programming language.
        code: Source code to generate tests for.
        test_framework: Test framework name (pytest, Google Test, JUnit 5, etc.).
        num_cases: Approximate number of test cases to generate.
        project_requirements: Optional project requirements to inform test design.

    Returns:
        A formatted prompt string for the LLM.
    """
    framework_hint = ""
    if test_framework:
        framework_hint = f"使用 {test_framework} 测试框架编写测试用例。"

    req_section = ""
    if project_requirements:
        req_section = f"""
## 项目需求
{project_requirements}
请确保测试用例覆盖所有需求点。
"""

    return f"""你是一个专业的软件测试工程师。请为以下 {language.upper()} 代码编写测试用例。

{framework_hint}
{req_section}

## 代码
```{language}
{code}
```

请生成约 {num_cases} 个测试用例，覆盖以下场景：
1. 正常功能测试（happy path）
2. 边界条件测试
3. 空值/null 处理测试
4. 异常/错误输入测试
5. 性能相关测试（如适用）

只输出 JSON 格式，不要其他文字：

```json
{{
  "language": "{language}",
  "test_framework": "{test_framework}",
  "test_cases": [
    {{
      "id": "TC-001",
      "description": "测试描述",
      "category": "happy_path|boundary|null_handling|error_handling|performance",
      "priority": "critical|high|medium|low",
      "input": "测试输入描述",
      "expected_output": "期望输出",
      "test_code": "具体的测试代码片段（{language} 语言）",
      "notes": "额外说明"
    }}
  ]
}}
```
"""


def test_expansion_prompt(
    language: str,
    code: str,
    existing_test_cases: str,
    test_framework: str = "",
) -> str:
    """Generate a prompt for expanding existing test cases.

    Args:
        language: Programming language.
        code: Source code.
        existing_test_cases: User-provided example test cases.
        test_framework: Test framework name.

    Returns:
        A formatted prompt string for the LLM.
    """
    return f"""你是一个专业的软件测试工程师。用户已提供了一些测试用例示例，请基于这些示例扩展更多测试用例。

## 代码
```{language}
{code}
```

## 用户提供的示例测试用例
{existing_test_cases}

## 测试框架
{test_framework or "未指定"}

请基于示例的风格和格式，补充更多测试用例（约 3-5 个），覆盖用户示例未涉及的场景（如边界条件、异常处理等）。

只输出 JSON 格式，与示例格式保持一致。
"""