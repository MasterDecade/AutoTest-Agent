"""API routes for language configuration management."""

from fastapi import APIRouter, HTTPException

from src.api.schemas.languages import (
    LanguageConfigCreateRequest,
    LanguageConfigResponse,
    LanguageConfigUpdateRequest,
)
from src.analyzer.language_detector import EXTENSION_LANGUAGE_MAP, LanguageDetector

router = APIRouter(prefix="/api/languages", tags=["languages"])

# Pre-built languages (can be extended via DB in future)
BUILTIN_LANGUAGES = {
    "python": {
        "name": "python",
        "display_name": "Python",
        "version": "3.x",
        "dependencies": ["pylint"],
        "docker_image": "python:3.11-slim",
        "test_frameworks": ["pytest", "unittest"],
        "static_analyzers": ["pylint", "ruff", "mypy"],
        "extensions": [".py", ".pyw", ".pyi"],
    },
    "cpp": {
        "name": "cpp",
        "display_name": "C++",
        "version": "17/20",
        "dependencies": ["g++", "make", "cmake", "cppcheck"],
        "docker_image": "gcc:latest",
        "test_frameworks": ["Google Test", "CTest"],
        "static_analyzers": ["cppcheck", "clang-tidy"],
        "extensions": [".cpp", ".cc", ".cxx", ".hpp", ".hxx"],
    },
    "c": {
        "name": "c",
        "display_name": "C",
        "version": "11/17",
        "dependencies": ["gcc", "make", "cmake", "cppcheck"],
        "docker_image": "gcc:latest",
        "test_frameworks": ["Google Test", "CTest"],
        "static_analyzers": ["cppcheck"],
        "extensions": [".c", ".h"],
    },
    "java": {
        "name": "java",
        "display_name": "Java",
        "version": "17",
        "dependencies": ["openjdk-17-jdk", "maven"],
        "docker_image": "openjdk:17-slim",
        "test_frameworks": ["JUnit 5", "TestNG"],
        "static_analyzers": ["checkstyle", "PMD", "SpotBugs"],
        "extensions": [".java"],
    },
}


@router.get("")
async def list_languages():
    """List all supported and configured languages."""
    languages = []
    for lang_id, config in BUILTIN_LANGUAGES.items():
        languages.append({
            "name": config["name"],
            "display_name": config["display_name"],
            "version": config["version"],
            "extensions": config["extensions"],
            "is_builtin": True,
            "is_active": True,
        })
    return {"languages": languages, "total": len(languages)}


@router.get("/{language}", response_model=LanguageConfigResponse)
async def get_language(language: str):
    """Get detailed configuration for a language."""
    config = BUILTIN_LANGUAGES.get(language)
    if not config:
        raise HTTPException(status_code=404, detail=f"Language '{language}' not found")
    return LanguageConfigResponse(
        name=config["name"],
        display_name=config["display_name"],
        version=config["version"],
        docker_image=config["docker_image"],
        test_frameworks=config["test_frameworks"],
        static_analyzers=config["static_analyzers"],
        extensions=config["extensions"],
    )


@router.get("/{language}/extensions")
async def get_language_extensions(language: str):
    """Get file extensions associated with a language."""
    # From detector
    exts = [ext for ext, lang in EXTENSION_LANGUAGE_MAP.items() if lang == language]
    return {"language": language, "extensions": exts}