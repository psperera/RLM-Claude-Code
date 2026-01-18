#!/usr/bin/env python3
"""
RLM Task Runner

Entry point for executing RLM tasks. Loads context from file,
runs task through the guarded runtime, and prints structured output.

Usage:
    python run.py <context_file> [--task <task_name>] [--debug]

Examples:
    python run.py document.txt
    python run.py logs.txt --task find_errors_in_log
    python run.py data.txt --debug
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Load environment variables from .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional


def main():
    parser = argparse.ArgumentParser(
        description="Execute RLM tasks with guarded LLM subcalls",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py document.txt
  python run.py logs.txt --task find_errors_in_log
  python run.py report.txt --cost 0.25 --timeout 30

Available tasks:
  analyze_document   - Extract title, abstract, key points, conclusion
  find_errors_in_log - Find and classify errors in log files
  extract_entities   - Extract named entities from text
        """,
    )

    parser.add_argument(
        "context_file",
        type=Path,
        help="Path to the context file to process",
    )

    parser.add_argument(
        "--task",
        type=str,
        default="analyze_document",
        choices=["analyze_document", "find_errors_in_log", "extract_entities"],
        help="Task to execute (default: analyze_document)",
    )

    parser.add_argument(
        "--cost",
        type=float,
        default=0.50,
        help="Maximum cost budget in USD (default: 0.50)",
    )

    parser.add_argument(
        "--timeout",
        type=float,
        default=60.0,
        help="Maximum runtime in seconds (default: 60)",
    )

    parser.add_argument(
        "--tokens",
        type=int,
        default=4000,
        help="Maximum tokens per subcall (default: 4000)",
    )

    parser.add_argument(
        "--model",
        type=str,
        default="gpt-4o-mini",
        help="OpenAI model to use (default: gpt-4o-mini)",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug output including tracebacks",
    )

    parser.add_argument(
        "--pretty",
        action="store_true",
        default=True,
        help="Pretty-print JSON output (default: True)",
    )

    parser.add_argument(
        "--compact",
        action="store_true",
        help="Compact JSON output (overrides --pretty)",
    )

    args = parser.parse_args()

    # Validate API key
    if not os.environ.get("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY environment variable not set.", file=sys.stderr)
        print("Set it in .env file or export it in your shell.", file=sys.stderr)
        sys.exit(1)

    # Load context from file
    if not args.context_file.exists():
        print(f"ERROR: Context file not found: {args.context_file}", file=sys.stderr)
        sys.exit(1)

    try:
        context = args.context_file.read_text(encoding="utf-8")
    except Exception as e:
        print(f"ERROR: Failed to read context file: {e}", file=sys.stderr)
        sys.exit(1)

    if not context.strip():
        print("ERROR: Context file is empty.", file=sys.stderr)
        sys.exit(1)

    # Import RLM modules (after environment setup)
    from rlm.runtime import run_task
    from rlm.guards import GuardConfig
    from tasks.example_task import (
        analyze_document,
        find_errors_in_log,
        extract_entities,
    )

    # Map task names to functions
    task_map = {
        "analyze_document": analyze_document,
        "find_errors_in_log": find_errors_in_log,
        "extract_entities": extract_entities,
    }

    task_fn = task_map[args.task]

    # Configure guards
    config = GuardConfig(
        max_cost=args.cost,
        max_runtime_seconds=args.timeout,
        max_tokens_per_subcall=args.tokens,
        model=args.model,
    )

    # Print task info
    if args.debug:
        print(f"Task: {args.task}", file=sys.stderr)
        print(f"Context: {args.context_file} ({len(context)} chars)", file=sys.stderr)
        print(f"Budget: ${config.max_cost:.2f}, {config.max_runtime_seconds}s timeout", file=sys.stderr)
        print("-" * 60, file=sys.stderr)

    # Execute task
    result = run_task(task_fn, context, config)

    # Output
    indent = None if args.compact else 2
    output = json.dumps(result, indent=indent, ensure_ascii=False)

    print("\n" + "=" * 60)
    print("FINAL_ANSWER")
    print("=" * 60)
    print(output)

    # Exit with appropriate code
    if result["status"] == "error":
        sys.exit(1)
    elif result["status"] == "partial":
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
