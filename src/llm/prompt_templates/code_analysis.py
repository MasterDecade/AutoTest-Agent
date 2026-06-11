"""Prompt template for code analysis."""


def code_analysis_prompt(
    language: str,
    code: str,
    project_context: str = "",
) -> str:
    """Generate a prompt for analyzing student/submitted code.

    Args:
        language: Programming language (python, cpp, java, etc.).
        code: The source code to analyze.
        project_context: Optional project requirements/context.

    Returns:
        A formatted prompt string for the LLM.
    """
    context_section = ""
    if project_context:
        context_section = f"""
## 项目要求/上下文
{project_context}
"""

    return f"""你是一个专业的代码审查专家。请分析以下 {language.upper()} 代码。

{context_section}

## 代码
```{language}
{code}
```

请从以下维度进行分析（只输出 JSON 格式，不要其他文字）：

```json
{{
  "language": "{language}",
  "summary": "一句话总结代码功能",
  "syntax_issues": [
    {{"line": 行号, "severity": "error|warning", "message": "问题描述"}}
  ],
  "style_issues": [
    {{"line": 行号, "severity": "warning|info", "message": "问题描述", "rule": "规则名称"}}
  ],
  "potential_bugs": [
    {{"line": 行号, "severity": "error|warning", "description": "潜在bug描述", "fix_suggestion": "修复建议"}}
  ],
  "complexity_score": 1-10,
  "code_quality_notes": ["改进建议列表"],
  "strengths": ["代码优点列表"]
}}
```
"""