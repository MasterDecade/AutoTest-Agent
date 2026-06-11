"""LLM prompt templates for code analysis, test generation, and result analysis.

Each template function returns a formatted prompt string that can be
sent to any BaseProvider implementation.
"""

from .code_analysis import code_analysis_prompt
from .test_generation import test_generation_prompt
from .result_analysis import result_analysis_prompt

__all__ = [
    "code_analysis_prompt",
    "test_generation_prompt",
    "result_analysis_prompt",
]