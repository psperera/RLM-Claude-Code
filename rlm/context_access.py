"""
RLM Context Access Layer

Provides explicit, auditable functions for navigating long context.
These are the ONLY permitted ways to access context in RLM tasks.

Functions:
- context_head: First n characters
- context_tail: Last n characters
- context_slice: Substring extraction
- context_search: Regex search with position results

All access is logged for auditability.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterator


@dataclass(frozen=True)
class SearchMatch:
    """
    A single regex search match with position information.

    Attributes:
        text: The matched text
        start: Start position in the context
        end: End position in the context
        line_number: Approximate line number (1-indexed)
    """
    text: str
    start: int
    end: int
    line_number: int

    def __repr__(self) -> str:
        preview = self.text[:50] + "..." if len(self.text) > 50 else self.text
        return f"SearchMatch(line={self.line_number}, pos={self.start}-{self.end}, text={preview!r})"


class ContextAccessLog:
    """
    Singleton logger for context access auditing.

    Records every context access for debugging and compliance.
    """
    _instance: ContextAccessLog | None = None
    _log: list[dict]

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._log = []
        return cls._instance

    def record(self, operation: str, **kwargs) -> None:
        """Record a context access operation."""
        entry = {"operation": operation, **kwargs}
        self._log.append(entry)

    def get_log(self) -> list[dict]:
        """Return the full access log."""
        return self._log.copy()

    def clear(self) -> None:
        """Clear the access log (call at task start)."""
        self._log = []

    def summary(self) -> dict:
        """Return summary statistics of context access."""
        ops = {}
        total_chars = 0
        for entry in self._log:
            op = entry["operation"]
            ops[op] = ops.get(op, 0) + 1
            if "chars_accessed" in entry:
                total_chars += entry["chars_accessed"]
        return {
            "total_operations": len(self._log),
            "operations_by_type": ops,
            "total_chars_accessed": total_chars,
        }


# Module-level logger instance
_logger = ContextAccessLog()


def get_access_log() -> ContextAccessLog:
    """Get the context access logger."""
    return _logger


def context_head(context: str, n: int) -> str:
    """
    Return the first n characters of context.

    Args:
        context: The full context string
        n: Number of characters to return

    Returns:
        First n characters (or full string if shorter)

    Example:
        >>> chunk = context_head(document, 1000)
        >>> # Process first 1000 chars
    """
    if not isinstance(context, str):
        raise TypeError(f"context must be str, got {type(context).__name__}")
    if not isinstance(n, int) or n < 0:
        raise ValueError(f"n must be non-negative integer, got {n}")

    result = context[:n]

    _logger.record(
        operation="head",
        n=n,
        context_length=len(context),
        chars_accessed=len(result),
    )

    return result


def context_tail(context: str, n: int) -> str:
    """
    Return the last n characters of context.

    Args:
        context: The full context string
        n: Number of characters to return

    Returns:
        Last n characters (or full string if shorter)

    Example:
        >>> chunk = context_tail(document, 1000)
        >>> # Process last 1000 chars (e.g., conclusion)
    """
    if not isinstance(context, str):
        raise TypeError(f"context must be str, got {type(context).__name__}")
    if not isinstance(n, int) or n < 0:
        raise ValueError(f"n must be non-negative integer, got {n}")

    result = context[-n:] if n > 0 else ""

    _logger.record(
        operation="tail",
        n=n,
        context_length=len(context),
        chars_accessed=len(result),
    )

    return result


def context_slice(context: str, start: int, end: int) -> str:
    """
    Return a substring from position start to end.

    Args:
        context: The full context string
        start: Start position (inclusive, 0-indexed)
        end: End position (exclusive)

    Returns:
        Substring context[start:end]

    Example:
        >>> # Extract chars 1000-2000 around a search hit
        >>> chunk = context_slice(document, 1000, 2000)
    """
    if not isinstance(context, str):
        raise TypeError(f"context must be str, got {type(context).__name__}")
    if not isinstance(start, int) or not isinstance(end, int):
        raise ValueError(f"start and end must be integers, got {type(start).__name__}, {type(end).__name__}")

    # Clamp to valid range
    start = max(0, start)
    end = min(len(context), end)

    if start > end:
        start, end = end, start  # Swap if inverted

    result = context[start:end]

    _logger.record(
        operation="slice",
        start=start,
        end=end,
        context_length=len(context),
        chars_accessed=len(result),
    )

    return result


def context_search(
    context: str,
    pattern: str,
    max_hits: int = 10,
    case_sensitive: bool = False,
) -> list[SearchMatch]:
    """
    Search context for regex pattern, returning match positions.

    Args:
        context: The full context string
        pattern: Regex pattern to search for
        max_hits: Maximum number of matches to return (default: 10)
        case_sensitive: Whether search is case-sensitive (default: False)

    Returns:
        List of SearchMatch objects with positions

    Example:
        >>> matches = context_search(document, r"error|exception", max_hits=5)
        >>> for m in matches:
        ...     chunk = context_slice(document, m.start - 200, m.end + 200)
        ...     # Process chunk around each match
    """
    if not isinstance(context, str):
        raise TypeError(f"context must be str, got {type(context).__name__}")
    if not isinstance(pattern, str):
        raise TypeError(f"pattern must be str, got {type(pattern).__name__}")
    if not isinstance(max_hits, int) or max_hits < 1:
        raise ValueError(f"max_hits must be positive integer, got {max_hits}")

    flags = 0 if case_sensitive else re.IGNORECASE

    try:
        compiled = re.compile(pattern, flags)
    except re.error as e:
        raise ValueError(f"Invalid regex pattern: {e}")

    # Pre-compute line starts for line number calculation
    line_starts = [0]
    for i, char in enumerate(context):
        if char == '\n':
            line_starts.append(i + 1)

    def get_line_number(pos: int) -> int:
        """Binary search for line number at position."""
        lo, hi = 0, len(line_starts)
        while lo < hi:
            mid = (lo + hi) // 2
            if line_starts[mid] <= pos:
                lo = mid + 1
            else:
                hi = mid
        return lo  # 1-indexed line number

    matches: list[SearchMatch] = []
    for match in compiled.finditer(context):
        if len(matches) >= max_hits:
            break
        matches.append(SearchMatch(
            text=match.group(),
            start=match.start(),
            end=match.end(),
            line_number=get_line_number(match.start()),
        ))

    _logger.record(
        operation="search",
        pattern=pattern,
        max_hits=max_hits,
        case_sensitive=case_sensitive,
        context_length=len(context),
        matches_found=len(matches),
        chars_accessed=0,  # Search doesn't extract text
    )

    return matches


def context_chunks(
    context: str,
    chunk_size: int,
    overlap: int = 0,
) -> Iterator[tuple[int, int, str]]:
    """
    Yield non-overlapping (or overlapping) chunks of context.

    This is a convenience function for iterating over context
    in bounded pieces. Each yield includes position info.

    Args:
        context: The full context string
        chunk_size: Size of each chunk in characters
        overlap: Number of characters to overlap between chunks

    Yields:
        Tuples of (start_pos, end_pos, chunk_text)

    Example:
        >>> for start, end, chunk in context_chunks(document, 2000, overlap=200):
        ...     result = semantic_subcall("Summarize this section.", chunk)
    """
    if not isinstance(context, str):
        raise TypeError(f"context must be str, got {type(context).__name__}")
    if chunk_size < 1:
        raise ValueError(f"chunk_size must be positive, got {chunk_size}")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError(f"overlap must be in [0, chunk_size), got {overlap}")

    pos = 0
    while pos < len(context):
        end = min(pos + chunk_size, len(context))
        chunk = context[pos:end]

        _logger.record(
            operation="chunk",
            start=pos,
            end=end,
            chunk_size=chunk_size,
            overlap=overlap,
            context_length=len(context),
            chars_accessed=len(chunk),
        )

        yield (pos, end, chunk)

        if end >= len(context):
            break
        pos = end - overlap


def context_around_match(
    context: str,
    match: SearchMatch,
    before: int = 200,
    after: int = 200,
) -> str:
    """
    Extract context around a search match.

    Convenience function combining search results with slicing.

    Args:
        context: The full context string
        match: A SearchMatch from context_search
        before: Characters to include before match
        after: Characters to include after match

    Returns:
        Substring including the match with surrounding context

    Example:
        >>> matches = context_search(document, r"critical error")
        >>> for m in matches:
        ...     chunk = context_around_match(document, m, before=500, after=500)
        ...     analysis = semantic_subcall("Explain this error.", chunk)
    """
    start = max(0, match.start - before)
    end = min(len(context), match.end + after)
    return context_slice(context, start, end)
