"""
RLM Guard System

Enforces hard budget limits on all LLM subcalls:
- Cost budget: Maximum spend per task
- Token budget: Maximum tokens per subcall
- Recursion limit: depth=1 only
- Runtime limit: Maximum wall-clock time

Guards cannot be bypassed. Violations raise exceptions.
"""

from __future__ import annotations

import time
import threading
from dataclasses import dataclass, field
from typing import Any, Callable
from contextlib import contextmanager


class BudgetExceededError(Exception):
    """Raised when any budget limit is exceeded."""

    def __init__(self, budget_type: str, limit: float, current: float, message: str = ""):
        self.budget_type = budget_type
        self.limit = limit
        self.current = current
        self.message = message or f"{budget_type} budget exceeded: {current:.4f} >= {limit:.4f}"
        super().__init__(self.message)


class RecursionDepthError(BudgetExceededError):
    """Raised when subcall depth exceeds 1."""

    def __init__(self, attempted_depth: int):
        super().__init__(
            budget_type="recursion",
            limit=1,
            current=attempted_depth,
            message=f"Recursion depth violation: attempted depth={attempted_depth}, max=1"
        )


class TokenLimitError(BudgetExceededError):
    """Raised when a single subcall exceeds token limit."""

    def __init__(self, requested: int, limit: int):
        super().__init__(
            budget_type="tokens",
            limit=limit,
            current=requested,
            message=f"Token limit exceeded: {requested} > {limit} per subcall"
        )


class RuntimeLimitError(BudgetExceededError):
    """Raised when wall-clock time exceeds limit."""

    def __init__(self, elapsed: float, limit: float):
        super().__init__(
            budget_type="runtime",
            limit=limit,
            current=elapsed,
            message=f"Runtime limit exceeded: {elapsed:.2f}s > {limit:.2f}s"
        )


class CostLimitError(BudgetExceededError):
    """Raised when cumulative cost exceeds budget."""

    def __init__(self, current: float, limit: float):
        super().__init__(
            budget_type="cost",
            limit=limit,
            current=current,
            message=f"Cost budget exceeded: ${current:.4f} >= ${limit:.4f}"
        )


@dataclass
class GuardConfig:
    """
    Configuration for RLM guard limits.

    Attributes:
        max_cost: Maximum total cost in USD (default: $0.50)
        max_tokens_per_subcall: Maximum tokens per single subcall (default: 4000)
        max_recursion_depth: Maximum subcall depth (fixed at 1)
        max_runtime_seconds: Maximum wall-clock time (default: 60s)
        model: OpenAI model to use (default: gpt-4o-mini)
        cost_per_1k_input: Cost per 1000 input tokens
        cost_per_1k_output: Cost per 1000 output tokens
    """
    max_cost: float = 0.50
    max_tokens_per_subcall: int = 4000
    max_recursion_depth: int = 1  # Fixed, not configurable
    max_runtime_seconds: float = 60.0
    model: str = "gpt-4o-mini"
    cost_per_1k_input: float = 0.00015  # gpt-4o-mini pricing
    cost_per_1k_output: float = 0.0006

    def __post_init__(self):
        # Recursion depth is architecturally fixed at 1
        if self.max_recursion_depth != 1:
            raise ValueError("max_recursion_depth must be 1 (architectural constraint)")


@dataclass
class GuardState:
    """
    Mutable state tracking for budget consumption.

    Thread-safe accumulator for cost, calls, and timing.
    """
    config: GuardConfig
    total_cost: float = 0.0
    total_calls: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    start_time: float = field(default_factory=time.time)
    current_depth: int = 0
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def check_runtime(self) -> None:
        """Check if runtime limit exceeded. Raises RuntimeLimitError if so."""
        elapsed = time.time() - self.start_time
        if elapsed > self.config.max_runtime_seconds:
            raise RuntimeLimitError(elapsed, self.config.max_runtime_seconds)

    def check_cost(self) -> None:
        """Check if cost budget exceeded. Raises CostLimitError if so."""
        if self.total_cost >= self.config.max_cost:
            raise CostLimitError(self.total_cost, self.config.max_cost)

    def check_depth(self) -> None:
        """Check if recursion depth exceeded. Raises RecursionDepthError if so."""
        if self.current_depth >= self.config.max_recursion_depth:
            raise RecursionDepthError(self.current_depth + 1)

    def estimate_tokens(self, text: str) -> int:
        """Rough token estimate: ~4 chars per token for English."""
        return max(1, len(text) // 4)

    def check_token_limit(self, prompt: str, context_chunk: str) -> None:
        """Check if request would exceed per-subcall token limit."""
        estimated = self.estimate_tokens(prompt) + self.estimate_tokens(context_chunk)
        if estimated > self.config.max_tokens_per_subcall:
            raise TokenLimitError(estimated, self.config.max_tokens_per_subcall)

    def record_usage(self, input_tokens: int, output_tokens: int) -> None:
        """Record token usage and update cost accumulator."""
        with self._lock:
            self.total_input_tokens += input_tokens
            self.total_output_tokens += output_tokens
            self.total_calls += 1

            cost = (
                (input_tokens / 1000) * self.config.cost_per_1k_input +
                (output_tokens / 1000) * self.config.cost_per_1k_output
            )
            self.total_cost += cost

    @contextmanager
    def subcall_context(self):
        """
        Context manager for subcall depth tracking.

        Ensures depth is incremented on entry and decremented on exit,
        even if an exception occurs.
        """
        with self._lock:
            self.current_depth += 1
        try:
            yield
        finally:
            with self._lock:
                self.current_depth -= 1

    def get_summary(self) -> dict[str, Any]:
        """Return summary of budget consumption."""
        elapsed = time.time() - self.start_time
        return {
            "total_cost_usd": round(self.total_cost, 6),
            "cost_budget_usd": self.config.max_cost,
            "cost_remaining_usd": round(self.config.max_cost - self.total_cost, 6),
            "total_calls": self.total_calls,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "elapsed_seconds": round(elapsed, 2),
            "runtime_limit_seconds": self.config.max_runtime_seconds,
        }


# Global guard state - initialized per task run
_guard_state: GuardState | None = None


def init_guards(config: GuardConfig | None = None) -> GuardState:
    """
    Initialize guard state for a new task.

    Must be called before any subcalls. Returns the guard state
    for inspection/testing purposes.
    """
    global _guard_state
    _guard_state = GuardState(config=config or GuardConfig())
    return _guard_state


def get_guard_state() -> GuardState:
    """
    Get current guard state.

    Raises RuntimeError if guards not initialized.
    """
    if _guard_state is None:
        raise RuntimeError("Guards not initialized. Call init_guards() first.")
    return _guard_state


def guarded_call(
    llm_function: Callable[[str, str], tuple[str, int, int]],
    prompt: str,
    context_chunk: str,
) -> str:
    """
    Execute an LLM call with full guard enforcement.

    Args:
        llm_function: Function that takes (prompt, context_chunk) and returns
                     (response_text, input_tokens, output_tokens)
        prompt: The instruction/question for the LLM
        context_chunk: The bounded context slice to reason about

    Returns:
        The LLM response text

    Raises:
        BudgetExceededError: If any budget limit is exceeded
        RuntimeError: If guards not initialized
    """
    state = get_guard_state()

    # Pre-flight checks
    state.check_runtime()
    state.check_cost()
    state.check_depth()
    state.check_token_limit(prompt, context_chunk)

    # Execute with depth tracking
    with state.subcall_context():
        # Re-check runtime in case of slow queue
        state.check_runtime()

        response, input_tokens, output_tokens = llm_function(prompt, context_chunk)

        # Record usage
        state.record_usage(input_tokens, output_tokens)

        # Post-flight cost check
        state.check_cost()

    return response


def finalize_result(
    result: Any,
    status: str = "completed",
    error: str | None = None,
) -> dict[str, Any]:
    """
    Finalize task result with guard summary.

    Always call this to return results, ensuring budget
    information is included in output.

    Args:
        result: The task result (any JSON-serializable value)
        status: One of "completed", "partial", "error"
        error: Error message if status is "error" or "partial"

    Returns:
        Structured output with result and budget summary
    """
    state = get_guard_state()

    return {
        "status": status,
        "result": result,
        "error": error,
        "budget_summary": state.get_summary(),
    }
