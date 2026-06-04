"""Java static analyzer — inline analysis for common issues."""

import logging
import re

from src.analyzer.static_analyzer import AnalysisResult, Issue, StaticAnalyzerBase

logger = logging.getLogger(__name__)

JAVA_STYLE_CHECKS = [
    (r"\bSystem\.out\.print", "Use of System.out.print - consider logging framework", "style"),
    (r"\bSystem\.err\.print", "Use of System.err - consider logging framework", "style"),
    (r"catch\s*\(\s*Exception\s+\w+\s*\)", "Catching generic Exception - be specific", "style"),
    (r"\be\.printStackTrace\s*\(", "Printing stack trace to stdout", "style"),
    (r"^\s*//\s*TODO", "TODO comment found", "style"),
    (r"^\s*//\s*FIXME", "FIXME comment found", "style"),
    (r"public\s+static\s+void\s+main", "Main method entry point", "style"),
]

JAVA_ERROR_CHECKS = [
    (r"catch\s*\(\s*Exception\s+\w+\s*\)\s*\{\s*\}", "Empty catch block - exception silently swallowed", "bug"),
    (r"==\s*(?!null)\w+\s*\|\||\s*\w+\s*==", "Potential null comparison issue", "bug"),
    (r"\.equals\(\s*null\s*\)", "equals() called on null", "bug"),
]

JAVA_COMPLEXITY = [
    (r"^\s{12,}(if|for|while|switch)", "Deep nesting (>4 levels)", "complexity"),
    (r"\bif\b.*\bif\b.*\bif\b.*\bif\b", "Deep if nesting", "complexity"),
]


class JavaAnalyzer(StaticAnalyzerBase):
    """Java-specific static code analyzer."""

    language = "java"
    supported_extensions = (".java",)

    def analyze(self, code: str, file_path: str = "", use_llm: bool = False) -> AnalysisResult:
        """Perform regex-based Java code analysis.

        Args:
            code: Java source code.
            file_path: Optional file path.
            use_llm: Not used for basic analysis.

        Returns:
            AnalysisResult with detected issues.
        """
        lines = code.split("\n")
        issues: list[Issue] = []

        for line_num, line in enumerate(lines, start=1):
            for pattern, message, category in JAVA_STYLE_CHECKS:
                if re.search(pattern, line):
                    issues.append(Issue(line=line_num, severity="warning", message=message, rule=category, category="style"))

            for pattern, message, category in JAVA_ERROR_CHECKS:
                if re.search(pattern, line):
                    severity = "error" if category == "bug" else "warning"
                    issues.append(Issue(line=line_num, severity=severity, message=message, rule=category, category=category))

            for pattern, message, category in JAVA_COMPLEXITY:
                if re.search(pattern, line):
                    issues.append(Issue(line=line_num, severity="info", message=message, rule=category, category="complexity"))

        total_lines = len(lines)
        code_lines = sum(1 for l in lines if l.strip() and not l.strip().startswith("//") and not l.strip().startswith("/*"))

        return AnalysisResult(
            language=self.language,
            file_path=file_path,
            summary=f"Java analysis: {len(issues)} issues found",
            issues=issues,
            syntax_score=self.score_from_issues([i for i in issues if i.severity == "error"]),
            style_score=self.score_from_issues([i for i in issues if i.category == "style"]),
            complexity_score=self.score_from_issues([i for i in issues if i.category == "complexity"], max_score=100.0),
            metrics={"total_lines": total_lines, "code_lines": code_lines},
        )