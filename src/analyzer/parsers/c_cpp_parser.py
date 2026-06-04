"""C/C++ static analyzer — inline analysis for common issues."""

import logging
import re

from src.analyzer.static_analyzer import AnalysisResult, Issue, StaticAnalyzerBase

logger = logging.getLogger(__name__)

C_CPP_STYLE_CHECKS = [
    (r"^[^#]*\bgets\s*\(", "Use of unsafe gets() - use fgets() instead", "style"),
    (r"^[^#]*\bstrcpy\s*\(", "Use of unsafe strcpy() - consider strncpy()", "style"),
    (r"^[^#]*\bstrcat\s*\(", "Use of unsafe strcat() - consider strncat()", "style"),
    (r"^[^#]*\bsprintf\s*\(", "Use of unsafe sprintf() - consider snprintf()", "style"),
    (r"\b(malloc|calloc|realloc)\s*\(", "Manual memory allocation detected", "style"),
    (r"\b(new|delete)\b(?![a-zA-Z])", "Manual new/delete - consider smart pointers in C++", "style"),
]

C_CPP_ERROR_CHECKS = [
    (r"\bfree\s*\([^)]*\)\s*(?=.*free\s*\()", "Potential double-free detected", "bug"),
    (r"^\s*#include\s*[<\"]\s*[>\"]\s*$", "Empty include directive", "bug"),
    (r"\b(nullptr|NULL)\s*\)(?!=)/\s*\d", "Potential NULL pointer dereference", "bug"),
    (r"for\s*\(\s*;\s*;\s*\)", "Infinite loop (for(;;))", "complexity"),
    (r"goto\s+\w+", "Usage of goto statement", "style"),
]

C_CPP_COMPLEXITY = [
    (r"\bif\b.*\bif\b.*\bif\b.*\bif\b", "Deep if nesting (>3 levels)", "complexity"),
    (r"^\s{12,}(if|for|while|switch)", "Excessive indentation", "complexity"),
]


class CCPPAnalyzer(StaticAnalyzerBase):
    """C/C++-specific static code analyzer."""

    language = "cpp"
    supported_extensions = (".c", ".cc", ".cpp", ".cxx", ".h", ".hpp", ".hxx")

    def analyze(self, code: str, file_path: str = "", use_llm: bool = False) -> AnalysisResult:
        """Perform regex-based C/C++ code analysis.

        Args:
            code: C/C++ source code.
            file_path: Optional file path.
            use_llm: Not used for basic analysis.

        Returns:
            AnalysisResult with detected issues.
        """
        lines = code.split("\n")
        issues: list[Issue] = []

        for line_num, line in enumerate(lines, start=1):
            for pattern, message, category in C_CPP_STYLE_CHECKS:
                if re.search(pattern, line):
                    issues.append(Issue(line=line_num, severity="warning", message=message, rule=category, category="style"))

            for pattern, message, category in C_CPP_ERROR_CHECKS:
                if re.search(pattern, line):
                    severity = "error" if category == "bug" else "warning"
                    issues.append(Issue(line=line_num, severity=severity, message=message, rule=category, category=category))

            for pattern, message, category in C_CPP_COMPLEXITY:
                if re.search(pattern, line):
                    issues.append(Issue(line=line_num, severity="info", message=message, rule=category, category="complexity"))

        total_lines = len(lines)
        code_lines = sum(1 for l in lines if l.strip() and not l.strip().startswith("//") and not l.strip().startswith("/*"))

        return AnalysisResult(
            language=self.language,
            file_path=file_path,
            summary=f"C/C++ analysis: {len(issues)} issues found",
            issues=issues,
            syntax_score=self.score_from_issues([i for i in issues if i.severity == "error"]),
            style_score=self.score_from_issues([i for i in issues if i.category == "style"]),
            complexity_score=self.score_from_issues([i for i in issues if i.category == "complexity"], max_score=100.0),
            metrics={"total_lines": total_lines, "code_lines": code_lines},
        )


class CAnalyzer(CCPPAnalyzer):
    """C-specific analyzer (inherits from C/C++)."""
    language = "c"
    supported_extensions = (".c", ".h")