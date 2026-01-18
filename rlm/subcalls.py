"""
RLM Subcall Interface

Clean interface for semantic LLM subcalls with guard enforcement.
All LLM interactions MUST go through this module.

Features:
- Single function entry point
- Hardcoded depth=1 (no recursive chains)
- Automatic guard pass-through
- Prevents accidental guard bypass
"""

from __future__ import annotations

import os
import json
from typing import Any

from openai import OpenAI

from .guards import guarded_call, get_guard_state, GuardConfig


# Lazy-loaded client
_client: OpenAI | None = None


def _get_client() -> OpenAI:
    """Get or create OpenAI client."""
    global _client
    if _client is None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY environment variable not set. "
                "Set it in .env or export it in your shell."
            )
        _client = OpenAI(api_key=api_key)
    return _client


def _make_llm_call(prompt: str, context_chunk: str) -> tuple[str, int, int]:
    """
    Internal function that actually calls the OpenAI API.

    Returns (response_text, input_tokens, output_tokens).
    This is passed to guarded_call() which enforces all limits.
    """
    client = _get_client()
    config = get_guard_state().config

    # Construct the message with clear separation
    messages = [
        {
            "role": "system",
            "content": (
                "You are a precise reasoning engine. "
                "Answer ONLY based on the provided context chunk. "
                "Be concise and factual. "
                "If the answer cannot be determined from the context, say so explicitly."
            ),
        },
        {
            "role": "user",
            "content": f"INSTRUCTION: {prompt}\n\nCONTEXT CHUNK:\n{context_chunk}",
        },
    ]

    response = client.chat.completions.create(
        model=config.model,
        messages=messages,
        max_tokens=1000,  # Reasonable output limit
        temperature=0.0,  # Deterministic for reproducibility
    )

    text = response.choices[0].message.content or ""
    input_tokens = response.usage.prompt_tokens if response.usage else 0
    output_tokens = response.usage.completion_tokens if response.usage else 0

    return text, input_tokens, output_tokens


def semantic_subcall(prompt: str, context_chunk: str) -> str:
    """
    Execute a semantic reasoning subcall on a bounded context chunk.

    This is the ONLY way to invoke LLM reasoning in RLM tasks.
    All calls are guarded and depth is hardcoded to 1.

    Args:
        prompt: Clear instruction for what to extract/analyze
        context_chunk: Bounded text slice (from context_access functions)

    Returns:
        LLM response as string

    Raises:
        BudgetExceededError: If any guard limit is exceeded
        RuntimeError: If guards not initialized

    Example:
        >>> chunk = context_slice(document, 1000, 2000)
        >>> result = semantic_subcall(
        ...     "Extract the main claim made in this paragraph. "
        ...     "Return only the claim, nothing else.",
        ...     chunk
        ... )
    """
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("prompt must be a non-empty string")
    if not isinstance(context_chunk, str):
        raise TypeError(f"context_chunk must be str, got {type(context_chunk).__name__}")

    # All enforcement happens in guarded_call
    return guarded_call(_make_llm_call, prompt, context_chunk)


def semantic_subcall_json(
    prompt: str,
    context_chunk: str,
    default: Any = None,
) -> Any:
    """
    Execute a semantic subcall expecting JSON output.

    Convenience wrapper that parses the response as JSON.
    Falls back to default if parsing fails.

    Args:
        prompt: Instruction (should ask for JSON output)
        context_chunk: Bounded text slice
        default: Value to return if JSON parsing fails

    Returns:
        Parsed JSON or default value

    Example:
        >>> chunk = context_slice(document, 1000, 2000)
        >>> result = semantic_subcall_json(
        ...     "Classify the sentiment as {\"sentiment\": \"positive|negative|neutral\", \"confidence\": 0.0-1.0}",
        ...     chunk,
        ...     default={"sentiment": "unknown", "confidence": 0.0}
        ... )
    """
    # Enhance prompt to emphasize JSON output
    json_prompt = (
        f"{prompt}\n\n"
        "IMPORTANT: Respond with valid JSON only. No explanation, no markdown, just JSON."
    )

    response = semantic_subcall(json_prompt, context_chunk)

    # Try to extract JSON from response
    text = response.strip()

    # Handle markdown code blocks
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first and last lines (code fences)
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        if default is not None:
            return default
        raise ValueError(f"Failed to parse JSON from response: {response[:200]}")


def semantic_subcall_bool(
    prompt: str,
    context_chunk: str,
    default: bool = False,
) -> bool:
    """
    Execute a semantic subcall expecting a yes/no answer.

    Convenience wrapper for boolean questions.

    Args:
        prompt: Yes/no question
        context_chunk: Bounded text slice
        default: Value to return if answer unclear

    Returns:
        Boolean result

    Example:
        >>> chunk = context_slice(document, 1000, 2000)
        >>> is_error = semantic_subcall_bool(
        ...     "Does this section describe an error condition?",
        ...     chunk
        ... )
    """
    bool_prompt = f"{prompt}\n\nAnswer with exactly 'yes' or 'no'."

    response = semantic_subcall(bool_prompt, context_chunk).strip().lower()

    if response in ("yes", "true", "1"):
        return True
    elif response in ("no", "false", "0"):
        return False
    else:
        return default


def semantic_subcall_choice(
    prompt: str,
    context_chunk: str,
    choices: list[str],
    default: str | None = None,
) -> str:
    """
    Execute a semantic subcall selecting from predefined choices.

    Args:
        prompt: Question or instruction
        context_chunk: Bounded text slice
        choices: List of valid choices
        default: Value to return if response doesn't match

    Returns:
        One of the choices, or default

    Example:
        >>> chunk = context_slice(document, 1000, 2000)
        >>> severity = semantic_subcall_choice(
        ...     "What is the severity level described?",
        ...     chunk,
        ...     choices=["critical", "warning", "info"],
        ...     default="info"
        ... )
    """
    if not choices:
        raise ValueError("choices must be non-empty")

    choices_str = ", ".join(f"'{c}'" for c in choices)
    choice_prompt = (
        f"{prompt}\n\n"
        f"Choose exactly one of: {choices_str}\n"
        "Respond with only your choice, nothing else."
    )

    response = semantic_subcall(choice_prompt, context_chunk).strip()

    # Try exact match first
    if response in choices:
        return response

    # Try case-insensitive match
    response_lower = response.lower()
    for choice in choices:
        if choice.lower() == response_lower:
            return choice

    # Try substring match (response contains choice)
    for choice in choices:
        if choice.lower() in response_lower:
            return choice

    if default is not None:
        return default

    raise ValueError(f"Response '{response}' not in choices: {choices}")
