"""
RLM Task Definitions

Each task module should export a function that:
- Takes context (str) as input
- Uses only context_access functions to navigate context
- Uses semantic_subcall for bounded LLM reasoning
- Returns a structured result (dict)

Tasks are executed via rlm.runtime.run_task().
"""

from .example_task import analyze_document

__all__ = ["analyze_document"]
