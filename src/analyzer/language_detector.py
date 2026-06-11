"""Programming language detector based on file extensions and content analysis."""

import os
from pathlib import Path


# File extension to language mappings
EXTENSION_LANGUAGE_MAP = {
    # C/C++
    ".c": "c",
    ".cc": "cpp",
    ".cpp": "cpp",
    ".cxx": "cpp",
    ".h": "c_cpp",
    ".hpp": "c_cpp",
    ".hxx": "c_cpp",
    # Python
    ".py": "python",
    ".pyw": "python",
    ".pyx": "python",
    ".pyi": "python",
    # Java
    ".java": "java",
    ".class": "java",
    ".jar": "java",
    # Go
    ".go": "go",
    # Rust
    ".rs": "rust",
    # JavaScript/TypeScript
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".mjs": "javascript",
    # Ruby
    ".rb": "ruby",
    # C#
    ".cs": "csharp",
    # PHP
    ".php": "php",
    # Swift
    ".swift": "swift",
    # Kotlin
    ".kt": "kotlin",
    ".kts": "kotlin",
    # Shell
    ".sh": "shell",
    ".bash": "shell",
}

# Document file extensions
DOCUMENT_EXTENSIONS = {".pdf", ".docx", ".md", ".txt", ".html", ".rst"}


class LanguageDetector:
    """Detects programming languages from files and code content."""

    @staticmethod
    def from_file_extension(file_path: str) -> str | None:
        """Detect language from file extension.

        Args:
            file_path: Path to the source file.

        Returns:
            Language identifier string or None.
        """
        ext = Path(file_path).suffix.lower()
        return EXTENSION_LANGUAGE_MAP.get(ext)

    @staticmethod
    def from_content(code: str) -> str | None:
        """Detect language from code content heuristics.

        Args:
            code: Source code string.

        Returns:
            Language identifier string or None.
        """
        # Check for Python features
        if "def " in code and ("import " in code or "from " in code or "class " in code):
            if "public class" not in code and "package " not in code:
                return "python"

        # Check for Java features
        if "public class" in code or "public static void main" in code:
            return "java"

        # Check for C/C++ features
        if "#include" in code and ("int main" in code or "void main" in code or "std::" in code):
            return "cpp"
        if "#include" in code and "int main" in code:
            return "c"

        # Check for Go features
        if "package main" in code and "func main" in code:
            return "go"

        # Check for Rust features
        if "fn main" in code and ("use " in code or "mod " in code):
            return "rust"

        return None

    @staticmethod
    def is_document(file_path: str) -> bool:
        """Check if a file is a document (PDF, DOCX, MD, etc.).

        Args:
            file_path: Path to the file.

        Returns:
            True if the file is a supported document format.
        """
        ext = Path(file_path).suffix.lower()
        return ext in DOCUMENT_EXTENSIONS

    @staticmethod
    def get_supported_extensions() -> list[str]:
        """Get all supported code file extensions."""
        return list(EXTENSION_LANGUAGE_MAP.keys())

    @staticmethod
    def get_supported_languages() -> list[str]:
        """Get all supported language identifiers."""
        return list(set(EXTENSION_LANGUAGE_MAP.values()))