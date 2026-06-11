"""Inspection Plan Generator — creates a test plan from analyzed documents and code.

The plan is generated via LLM and presented for human approval before execution.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class InspectionPlan:
    """A complete inspection plan for code testing."""

    plan_id: str = ""
    project_id: str = ""
    plan_version: str = "1.0"
    status: str = "pending_review"  # pending_review | approved | rejected | executed

    # Scope
    languages: list[str] = field(default_factory=list)
    files_to_analyze: int = 0
    estimated_duration_minutes: int = 5

    # Test configuration
    test_framework: str = ""
    test_framework_config: dict = field(default_factory=dict)

    # Test cases (planned)
    test_cases_plan: list[dict] = field(default_factory=list)

    # Scoring
    scoring_dimensions: list[dict] = field(default_factory=list)

    # Code style
    code_style_checks: list[str] = field(default_factory=list)

    # Environment
    environment_config: dict = field(default_factory=dict)

    # Risk & Notes
    risk_notes: list[str] = field(default_factory=list)
    reviewer_notes: str = ""

    # Metadata
    generated_at: str = ""
    reviewed_at: str = ""
    reviewed_by: str = ""

    def to_dict(self) -> dict:
        """Convert plan to dictionary for serialization."""
        return {
            "plan_id": self.plan_id,
            "project_id": self.project_id,
            "plan_version": self.plan_version,
            "status": self.status,
            "languages": self.languages,
            "files_to_analyze": self.files_to_analyze,
            "estimated_duration_minutes": self.estimated_duration_minutes,
            "test_framework": self.test_framework,
            "test_framework_config": self.test_framework_config,
            "test_cases_plan": self.test_cases_plan,
            "scoring_dimensions": self.scoring_dimensions,
            "code_style_checks": self.code_style_checks,
            "environment_config": self.environment_config,
            "risk_notes": self.risk_notes,
            "reviewer_notes": self.reviewer_notes,
            "generated_at": self.generated_at,
            "reviewed_at": self.reviewed_at,
            "reviewed_by": self.reviewed_by,
        }


@dataclass
class PlanReviewRequest:
    """A review decision on an inspection plan."""

    plan_id: str
    approved: bool = False
    reviewer_notes: str = ""
    reviewer_name: str = ""

    # Optional modifications
    modified_test_cases: Optional[list[dict]] = None
    modified_scoring_dimensions: Optional[list[dict]] = None
    modified_code_style_checks: Optional[list[str]] = None


class InspectionPlanGenerator:
    """Generates inspection plans based on code, documents, and project context.

    Uses LLM to create a comprehensive plan covering:
    - Test framework selection
    - Test case generation outline
    - Scoring dimensions and weights
    - Code style checks
    - Environment configuration
    """

    @classmethod
    async def generate(
        cls,
        project_name: str,
        code_samples: str,
        language: str,
        analyzed_documents: list = None,
        existing_test_cases: list = None,
        provider_manager=None,
    ) -> InspectionPlan:
        """Generate an inspection plan from project context.

        Args:
            project_name: Name of the project.
            code_samples: Sample code to analyze.
            language: Detected programming language.
            analyzed_documents: Optional list of AnalyzedDocument results.
            existing_test_cases: Optional user-provided test cases.
            provider_manager: LLM provider manager.

        Returns:
            A complete InspectionPlan.
        """
        from src.llm.base import BaseProvider

        if provider_manager is None:
            from src.llm.provider import get_provider_manager
            provider_manager = get_provider_manager()

        # Build context from analyzed documents
        doc_context = ""
        if analyzed_documents:
            for i, doc in enumerate(analyzed_documents):
                doc_context += f"\n### 文档 {i + 1} (类型: {doc.doc_category})\n"
                if doc.key_requirements:
                    doc_context += f"- 关键需求: {', '.join(doc.key_requirements[:10])}\n"
                if doc.test_criteria:
                    doc_context += f"- 测试标准: {', '.join(doc.test_criteria[:10])}\n"
                if doc.scoring_rules:
                    doc_context += f"- 评分规则: {json.dumps(doc.scoring_rules[:5], ensure_ascii=False)}\n"
                if doc.edge_cases:
                    doc_context += f"- 边界条件: {', '.join(doc.edge_cases[:5])}\n"

        # Build existing test case context
        existing_context = ""
        if existing_test_cases:
            existing_context = f"\n## 用户提供的示例测试用例\n{json.dumps(existing_test_cases, ensure_ascii=False, indent=2)}"

        prompt = f"""你是一个专业的软件测试计划专家。请为以下项目生成一个完整的代码检测计划。

## 项目信息
- 项目名称: {project_name}
- 语言: {language}

{doc_context}

## 代码示例
```{language}
{code_samples}
```
{existing_context}

请生成检测计划（只输出 JSON 格式）：

```json
{{
  "languages": ["{language}"],
  "estimated_duration_minutes": 10,
  "test_framework": "推荐的测试框架",
  "test_framework_config": {{"config_key": "value"}},
  "test_cases_plan": [
    {{
      "id": "TC-001",
      "description": "测试描述",
      "priority": "critical|high|medium|low",
      "category": "happy_path|boundary|null_handling|error_handling|performance",
      "estimated_count": 3
    }}
  ],
  "scoring_dimensions": [
    {{
      "name": "维度名称",
      "weight": 20,
      "scoring_type": "auto|llm",
      "description": "评分标准描述"
    }}
  ],
  "code_style_checks": ["规范检查项"],
  "environment_config": {{
    "base_image": "推荐的 Docker 镜像",
    "dependencies": ["依赖包列表"],
    "build_command": "编译命令",
    "test_command": "测试运行命令"
  }},
  "risk_notes": ["潜在风险"]
}}
```

要求：
1. 测试用例覆盖所有关键需求
2. 评分维度权重总和应为 100
3. 基于文档中提到的测试标准设计评分规则
4. 如果有用户提供的测试用例，参考其风格补充更多
"""
        try:
            response = await provider_manager.chat_with_fallback(
                messages=[BaseProvider.user(prompt)],
                temperature=0.3,
                max_tokens=4096,
            )

            content = response.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            data = json.loads(content)

            import uuid

            return InspectionPlan(
                plan_id=str(uuid.uuid4()),
                languages=data.get("languages", [language]),
                estimated_duration_minutes=data.get("estimated_duration_minutes", 5),
                test_framework=data.get("test_framework", "pytest"),
                test_framework_config=data.get("test_framework_config", {}),
                test_cases_plan=data.get("test_cases_plan", []),
                scoring_dimensions=data.get("scoring_dimensions", []),
                code_style_checks=data.get("code_style_checks", []),
                environment_config=data.get("environment_config", {}),
                risk_notes=data.get("risk_notes", []),
                generated_at=datetime.now(timezone.utc).isoformat(),
                status="pending_review",
            )
        except Exception as e:
            logger.error(f"Plan generation failed: {e}")
            import uuid

            return InspectionPlan(
                plan_id=str(uuid.uuid4()),
                languages=[language],
                status="pending_review",
                generated_at=datetime.now(timezone.utc).isoformat(),
                risk_notes=[f"Plan generation failed: {str(e)}"],
            )