"""
RLM Runtime Harness

Entry point for executing RLM tasks with proper guard initialization
and error handling. All tasks should be run through this module.

Features:
- Automatic guard initialization
- Graceful handling of budget violations
- Partial result recovery
- Structured output format
"""

from __future__ import annotations

import sys
import traceback
from typing import Any, Callable, TypeVar

from .guards import (
    init_guards,
    finalize_result,
    GuardConfig,
    BudgetExceededError,
    CostLimitError,
    RuntimeLimitError,
    TokenLimitError,
    RecursionDepthError,
)
from .context_access import get_access_log


# Type for task functions
T = TypeVar("T")
TaskFunction = Callable[[str], T]


def run_task(
    task_fn: TaskFunction[T],
    context: str,
    config: GuardConfig | None = None,
) -> dict[str, Any]:
    """
    Execute an RLM task with full guard protection.

    This is the main entry point for running tasks. It handles:
    - Guard initialization
    - Task execution
    - Budget violation recovery
    - Structured output formatting

    Args:
        task_fn: Function that takes context and returns a result
        context: The long context (external state, not loaded into prompts)
        config: Optional guard configuration (uses defaults if not provided)

    Returns:
        Structured output dict with:
        - status: "completed", "partial", or "error"
        - result: The task result (may be partial)
        - error: Error message if status != "completed"
        - budget_summary: Guard state summary
        - access_log_summary: Context access statistics

    Example:
        >>> from tasks.example_task import analyze_document
        >>> result = run_task(analyze_document, document_text)
        >>> print(result["status"])
        'completed'
        >>> print(result["result"])
        {'findings': [...], 'summary': '...'}
    """
    # Clear access log from previous runs
    access_log = get_access_log()
    access_log.clear()

    # Initialize guards
    guard_state = init_guards(config)

    partial_result: Any = None
    error_message: str | None = None
    status: str = "completed"

    try:
        # Execute the task
        result = task_fn(context)

        # Successful completion
        output = finalize_result(result, status="completed")

    except CostLimitError as e:
        status = "partial"
        error_message = f"Cost budget exceeded: ${e.current:.4f} >= ${e.limit:.4f}"
        output = finalize_result(
            partial_result,
            status="partial",
            error=error_message,
        )

    except RuntimeLimitError as e:
        status = "partial"
        error_message = f"Runtime limit exceeded: {e.current:.2f}s >= {e.limit:.2f}s"
        output = finalize_result(
            partial_result,
            status="partial",
            error=error_message,
        )

    except TokenLimitError as e:
        status = "error"
        error_message = f"Token limit exceeded on subcall: {int(e.current)} > {int(e.limit)}"
        output = finalize_result(
            partial_result,
            status="error",
            error=error_message,
        )

    except RecursionDepthError as e:
        status = "error"
        error_message = f"Recursion depth violation: attempted depth={int(e.current)}, max=1"
        output = finalize_result(
            None,
            status="error",
            error=error_message,
        )

    except BudgetExceededError as e:
        # Catch-all for any other budget errors
        status = "error"
        error_message = str(e)
        output = finalize_result(
            partial_result,
            status="error",
            error=error_message,
        )

    except Exception as e:
        # Non-budget errors
        status = "error"
        error_message = f"{type(e).__name__}: {e}"
        output = finalize_result(
            None,
            status="error",
            error=error_message,
        )

        # Include traceback for debugging (optional)
        if "--debug" in sys.argv:
            output["traceback"] = traceback.format_exc()

    # Add context access summary
    output["access_log_summary"] = access_log.summary()

    return output


def run_task_with_accumulator(
    task_fn: Callable[[str, list], Any],
    context: str,
    config: GuardConfig | None = None,
) -> dict[str, Any]:
    """
    Execute a task that accumulates partial results.

    For tasks that process context incrementally, this variant
    passes an accumulator list that the task can append to.
    If a budget violation occurs, the partial results are preserved.

    Args:
        task_fn: Function taking (context, accumulator) and returning final result
        context: The long context
        config: Optional guard configuration

    Returns:
        Structured output with partial results on budget violation

    Example:
        >>> def analyze_sections(context, results):
        ...     for start, end, chunk in context_chunks(context, 2000):
        ...         analysis = semantic_subcall("Analyze this section.", chunk)
        ...         results.append({"pos": start, "analysis": analysis})
        ...     return {"sections": results}
        >>>
        >>> result = run_task_with_accumulator(analyze_sections, document)
        >>> # Even if budget exceeded, results list has partial data
    """
    access_log = get_access_log()
    access_log.clear()

    guard_state = init_guards(config)
    accumulator: list = []

    try:
        result = task_fn(context, accumulator)
        output = finalize_result(result, status="completed")

    except BudgetExceededError as e:
        # Return accumulated partial results
        output = finalize_result(
            {"partial_results": accumulator, "items_processed": len(accumulator)},
            status="partial",
            error=str(e),
        )

    except Exception as e:
        output = finalize_result(
            {"partial_results": accumulator, "items_processed": len(accumulator)},
            status="error",
            error=f"{type(e).__name__}: {e}",
        )

    output["access_log_summary"] = access_log.summary()
    return output


class TaskBuilder:
    """
    Fluent builder for configuring and running tasks.

    Example:
        >>> result = (
        ...     TaskBuilder(analyze_document)
        ...     .with_cost_budget(0.25)
        ...     .with_runtime_limit(30.0)
        ...     .run(document_text)
        ... )
    """

    def __init__(self, task_fn: TaskFunction):
        self.task_fn = task_fn
        self._config_overrides: dict[str, Any] = {}

    def with_cost_budget(self, max_cost: float) -> "TaskBuilder":
        """Set maximum cost in USD."""
        self._config_overrides["max_cost"] = max_cost
        return self

    def with_runtime_limit(self, seconds: float) -> "TaskBuilder":
        """Set maximum runtime in seconds."""
        self._config_overrides["max_runtime_seconds"] = seconds
        return self

    def with_token_limit(self, max_tokens: int) -> "TaskBuilder":
        """Set maximum tokens per subcall."""
        self._config_overrides["max_tokens_per_subcall"] = max_tokens
        return self

    def with_model(self, model: str) -> "TaskBuilder":
        """Set the OpenAI model to use."""
        self._config_overrides["model"] = model
        return self

    def run(self, context: str) -> dict[str, Any]:
        """Execute the task with configured settings."""
        config = GuardConfig(**self._config_overrides) if self._config_overrides else None
        return run_task(self.task_fn, context, config)


def create_task_runner(
    max_cost: float = 0.50,
    max_runtime: float = 60.0,
    max_tokens: int = 4000,
    model: str = "gpt-4o-mini",
) -> Callable[[TaskFunction, str], dict[str, Any]]:
    """
    Create a pre-configured task runner function.

    Useful for creating runners with specific budget constraints.

    Args:
        max_cost: Maximum cost in USD
        max_runtime: Maximum runtime in seconds
        max_tokens: Maximum tokens per subcall
        model: OpenAI model to use

    Returns:
        A function that takes (task_fn, context) and returns results

    Example:
        >>> cheap_runner = create_task_runner(max_cost=0.10)
        >>> result = cheap_runner(my_task, document)
    """
    config = GuardConfig(
        max_cost=max_cost,
        max_runtime_seconds=max_runtime,
        max_tokens_per_subcall=max_tokens,
        model=model,
    )

    def runner(task_fn: TaskFunction, context: str) -> dict[str, Any]:
        return run_task(task_fn, context, config)

    return runner
