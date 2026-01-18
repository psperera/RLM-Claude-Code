"""
RLM (Recursive Language Model) Runtime

This package implements the RLM paradigm where:
- LLMs reason on bounded chunks
- Code controls context access and aggregation
- Hard budget limits are enforced

Core modules:
- guards: Budget enforcement and limit tracking
- context_access: Explicit context navigation functions
- subcalls: Clean interface for semantic LLM calls
- runtime: Task execution harness
"""

from .guards import GuardConfig, GuardState, BudgetExceededError
from .context_access import context_head, context_tail, context_slice, context_search
from .subcalls import semantic_subcall
from .runtime import run_task, finalize_result

__all__ = [
    "GuardConfig",
    "GuardState",
    "BudgetExceededError",
    "context_head",
    "context_tail",
    "context_slice",
    "context_search",
    "semantic_subcall",
    "run_task",
    "finalize_result",
]
