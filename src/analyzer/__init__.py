"""Code and Document Analyzer Module.

Handles language detection, static code analysis, project document
analysis, and inspection plan generation.
"""

from .document_analyzer import DocumentAnalyzer
from .inspection_plan import InspectionPlanGenerator
from .language_detector import LanguageDetector

__all__ = [
    "DocumentAnalyzer",
    "InspectionPlanGenerator",
    "LanguageDetector",
]