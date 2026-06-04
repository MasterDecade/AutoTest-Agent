"""API routes for code analysis."""

from typing import Optional

from fastapi import APIRouter, HTTPException

from src.analyzer.language_detector import LanguageDetector
from src.analyzer.parsers.c_cpp_parser import CAnalyzer, CCPPAnalyzer
from src.analyzer.parsers.java_parser import JavaAnalyzer
from src.analyzer.parsers.python_parser import PythonAnalyzer
from src.analyzer.static_analyzer import AnalysisResult
from src.api.schemas.analysis import AnalysisRequest, AnalysisResponse
from src.llm.provider import get_provider_manager

router = APIRouter(prefix="/api/analysis", tags=["analysis"])

# Analyzer registry
ANALYZERS = {
    "python": PythonAnalyzer(),
    "cpp": CCPPAnalyzer(),
    "c": CAnalyzer(),
    "java": JavaAnalyzer(),
}


def get_analyzer(language: str):
    """Get the appropriate analyzer for a language.

    Args:
        language: Language identifier.

    Returns:
        A StaticAnalyzerBase instance or None.
    """
    return ANALYZERS.get(language)


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_code(request: AnalysisRequest):
    """Analyze source code for issues.

    If language is not specified, it will be auto-detected.
    The analysis can optionally include LLM-enhanced findings.
    """
    # Detect language if not specified
    language = request.language
    if not language:
        language = LanguageDetector.from_content(request.code)
        if not language and request.file_path:
            language = LanguageDetector.from_file_extension(request.file_path)
        if not language:
            raise HTTPException(status_code=400, detail="Unable to detect language. Please specify.")

    # Get analyzer
    analyzer = get_analyzer(language)
    if not analyzer:
        supported = list(ANALYZERS.keys())
        raise HTTPException(
            status_code=400,
            detail=f"Language '{language}' not supported. Supported: {supported}",
        )

    # Perform analysis
    try:
        if request.use_llm:
            result = await analyzer.analyze_with_llm(
                code=request.code,
                file_path=request.file_path or "",
                provider_manager=get_provider_manager(),
            )
        else:
            result = analyzer.analyze(
                code=request.code,
                file_path=request.file_path or "",
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    return AnalysisResponse(**result.to_dict())


@router.get("/languages")
async def list_supported_languages():
    """List all languages supported for code analysis."""
    return {
        "languages": [
            {
                "id": lang,
                "extensions": list(a.supported_extensions),
            }
            for lang, a in ANALYZERS.items()
        ],
        "total": len(ANALYZERS),
    }