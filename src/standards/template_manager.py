"""Scoring template manager — manages custom and default scoring templates."""

import logging
from dataclasses import dataclass, field
from typing import Optional

from src.standards.scoring import ScoringDimensionDef, ScoringEngine

logger = logging.getLogger(__name__)


@dataclass
class ScoringTemplate:
    """A scoring template containing multiple dimensions."""

    template_id: str = ""
    name: str = ""
    description: str = ""
    is_default: bool = False
    dimensions: list[ScoringDimensionDef] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "template_id": self.template_id,
            "name": self.name,
            "description": self.description,
            "is_default": self.is_default,
            "dimensions": [
                {
                    "name": d.name,
                    "key": d.key,
                    "weight": d.weight,
                    "scoring_type": d.scoring_type,
                    "description": d.description,
                    "enabled": d.enabled,
                }
                for d in self.dimensions
            ],
        }


class TemplateManager:
    """Manages scoring templates — create, update, list, delete.

    In-memory storage for now (will migrate to DB in production).
    """

    def __init__(self):
        self._templates: dict[str, ScoringTemplate] = {}
        self._init_defaults()

    def _init_defaults(self):
        """Initialize system default template."""
        import uuid

        default = ScoringTemplate(
            template_id=str(uuid.uuid4()),
            name="系统默认评分模板",
            description="AutoTest-Agent 系统内置的 6 维度默认评分标准",
            is_default=True,
            dimensions=ScoringEngine.default_dimensions(),
        )
        self._templates[default.template_id] = default

    def get_default(self) -> ScoringTemplate:
        """Get the default scoring template."""
        for t in self._templates.values():
            if t.is_default:
                return t
        # Fallback: create one
        self._init_defaults()
        return self.get_default()

    def create(self, name: str, dimensions: list[dict], description: str = "") -> ScoringTemplate:
        """Create a custom scoring template.

        Args:
            name: Template name.
            dimensions: List of dimension dicts (name, key, weight, scoring_type).
            description: Optional description.

        Returns:
            Created ScoringTemplate.
        """
        import uuid

        dims = [
            ScoringDimensionDef(
                name=d.get("name", ""),
                key=d.get("key", f"dim_{i}"),
                weight=d.get("weight", 10),
                scoring_type=d.get("scoring_type", "auto"),
                description=d.get("description", ""),
            )
            for i, d in enumerate(dimensions)
        ]

        template = ScoringTemplate(
            template_id=str(uuid.uuid4()),
            name=name,
            description=description,
            is_default=False,
            dimensions=dims,
        )
        self._templates[template.template_id] = template
        return template

    def get(self, template_id: str) -> Optional[ScoringTemplate]:
        """Get a template by ID."""
        return self._templates.get(template_id)

    def list_all(self) -> list[ScoringTemplate]:
        """List all templates."""
        return list(self._templates.values())

    def delete(self, template_id: str) -> bool:
        """Delete a template (cannot delete default)."""
        template = self._templates.get(template_id)
        if template and not template.is_default:
            del self._templates[template_id]
            return True
        return False


# Global instance
_template_manager: Optional[TemplateManager] = None


def get_template_manager() -> TemplateManager:
    """Get the global template manager singleton."""
    global _template_manager
    if _template_manager is None:
        _template_manager = TemplateManager()
    return _template_manager