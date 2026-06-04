"""Python static analyzer — basic inline analysis + Pylint integration."""

import logging
import re

from src.analyzer.static_analyzer import AnalysisResult, Issue, StaticAnalyzerBase

logger = logging.getLogger(__name__)

# Common Python anti-patterns and style issues
PYTHON_STYLE_CHECKS = [
    (r"\b(print)\s*\(.+\)\s*$", "Use of print() - consider logging instead", "style"),
    (r"except\s*:", "Bare except clause - specify exception type", "style"),
    (r"^\s*pass\s*$", "Empty code block (pass statement)", "style"),
    (r"except\s+\w+\s*:\s*\n\s*raise", "Catching exception to re-raise is redundant", "style"),
    (r"^\s*import\s+\*", "Wildcard import (*) - imports everything from module", "style"),
]

PYTHON_ERROR_CHECKS = [
    (r"\breturn\b(?![^:]*:)\s+.+?\n\s*\n\s*else", "Unreachable code after return", "bug"),
    (r"\bexcept\s+\w+:\s*\n\s*pass", "Exception silently swallowed", "bug"),
    (r"^\s*(?!def|class|if|for|while|with|try|#|\s*$)[a-zA-Z_][\w.]*\(", "Top-level function call - should be in main guard", "style"),
]

COMPLEXITY_PATTERNS = [
    (r"^\s{8,}(if|for|while|with)", "Deep nesting detected (>4 levels)", "complexity"),
]


class PythonAnalyzer(StaticAnalyzerBase):
    """Python-specific static code analyzer."""

    language = "python"
    supported_extensions = (".py", ".pyw", ".pyi")

    def analyze(self, code: str, file_path: str = "", use_llm: bool = False) -> AnalysisResult:
        """Perform regex-based Python code analysis.

        Args:
            code: Python source code.
            file_path: Optional file path.
            use_llm: Not used for basic analysis.

        Returns:
            AnalysisResult with detected issues.
        """
        lines = code.split("\n")
        issues: list[Issue] = []

        # Check line by line
        for line_num, line in enumerate(lines, start=1):
            for pattern, message, category in PYTHON_STYLE_CHECKS:
                if re.search(pattern, line):
                    issues.append(Issue(
                        line=line_num,
                        severity="warning",
                        message=message,
                        rule=category,
                        category="style",
                    ))

            for pattern, message, category in PYTHON_ERROR_CHECKS:
                if re.search(pattern, line, re.MULTILINE):
                    issues.append(Issue(
                        line=line_num,
                        severity="error" if category == "bug" else "warning",
                        message=message,
                        rule=category,
                        category=category,
                    ))

            for pattern, message, category in COMPLEXITY_PATTERNS:
                if re.match(pattern, line):
                    issues.append(Issue(
                        line=line_num,
                        severity="info",
                        message=message,
                        rule=category,
                        category="complexity",
                    ))

        # Basic metrics
        total_lines = len(lines)
        code_lines = sum(1 for l in lines if l.strip() and not l.strip().startswith("#"))
        empty_lines = sum(1 for l in lines if not l.strip())
        comment_lines = sum(1 for l in lines if l.strip().startswith("#"))

        style_issues = [i for i in issues if i.category == "style"]
        syntax_issues = [i for i in issues if i.severity == "error"]

        return AnalysisResult(
            language=self.language,
            file_path=file_path,
            summary=f"Python analysis: {len(issues)} issues found in {code_lines} lines",
            issues=issues,
            syntax_score=self.score_from_issues(syntax_issues),
            style_score=self.score_from_issues(style_issues),
            complexity_score=100.0,  # Simplified
            metrics={
                "total_lines": total_lines,
                "code_lines": code_lines,
                "empty_lines": empty_lines,
                "comment_lines": comment_lines,
                "comment_ratio": round(comment_lines / max(1, total_lines) * 100, 1),
            },
        )

    def analyze_with_pylint(self, code: str, file_path: str = "") -> AnalysisResult:
        """Analyze using Pylint if available.

        Args:
            code: Python source code.
            file_path: Optional file path.

        Returns:
            AnalysisResult with Pylint findings.
        """
        import subprocess
        import tempfile

        result = AnalysisResult(language=self.language, file_path=file_path)

        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
                f.write(code)
                tmp_path = f.name

            proc = subprocess.run(
                ["pylint", "--output-format=json", tmp_path],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if proc.returncode == 0 or proc.stdout:
                import json
                pylint_issues = json.loads(proc.stdout) if proc.stdout else []
                for pi in pylint_issues:
                    result.issues.append(Issue(
                        line=pi.get("line", 0),
                        column=pi.get("column", 0),
                        severity="error" if pi.get("type") in ("error", "fatal") else "warning",
                        message=pi.get("message", ""),
                        rule=pi.get("symbol", ""),
                        category="style",
                    ))

            result.syntax_score = self.score_from_issues(
                [i for i in result.issues if i.severity == "error"]
            )
            result.style_score = self.score_from_issues(result.issues)

        except FileNotFoundError:
            logger.warning("Pylint not installed; skipping external analysis")
        except Exception as e:
            logger.warning(f"Pylint analysis failed: {e}")
        finally:
            import os
            try:
                os.unlink(tmp_path)
            except (OSError, UnboundLocalError):
                pass

        return result