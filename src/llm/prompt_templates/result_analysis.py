"""Prompt template for test result analysis."""


def result_analysis_prompt(
    language: str,
    test_results: str,
    code: str = "",
    scoring_criteria: str = "",
) -> str:
    """Generate a prompt for analyzing test results.

    Args:
        language: Programming language.
        test_results: Raw test execution results.
        code: Optional source code for context.
        scoring_criteria: Optional custom scoring criteria.

    Returns:
        A formatted prompt string for the LLM.
    """
    code_section = ""
    if code:
        code_section = f"""
## 代码
```{language}
{code}
```
"""

    criteria_section = ""
    if scoring_criteria:
        criteria_section = f"""
## 评分标准
{scoring_criteria}
请严格按照上述标准进行评分。
"""

    return f"""你是一个专业的代码评估专家。请分析以下 {language.upper()} 代码的测试结果。

{code_section}

## 测试结果
```
{test_results}
```
{criteria_section}

请给出综合评估报告（只输出 JSON 格式，不要其他文字）：

```json
{{
  "language": "{language}",
  "overall_score": 0-100,
  "summary": "总体评估",
  "dimension_scores": {{
    "functionality": 0-100,
    "code_style": 0-100,
    "code_quality": 0-100,
    "test_coverage": 0-100,
    "performance": 0-100,
    "documentation": 0-100
  }},
  "issues": [
    {{
      "type": "critical|major|minor|suggestion",
      "category": "functionality|style|quality|performance|documentation",
      "description": "问题描述",
      "recommendation": "改进建议"
    }}
  ],
  "strengths": ["亮点列表"],
  "improvement_areas": ["需要改进的地方"],
  "grade": "A|B|C|D|F"
}}
```
"""