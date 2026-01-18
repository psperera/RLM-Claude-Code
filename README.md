# RLM: Recursive Language Model Runtime

> **This is not agent code. This is an RLM runtime.**
- Based on https://arxiv.org/pdf/2512.24601
<img width="1695" height="989" alt="image" src="https://github.com/user-attachments/assets/b0ad1102-ff02-4d31-92bb-5cf3632633f5" />
Inspired by https://www.youtube.com/watch?v=huszaaJPjU8

A production-ready project template implementing the Recursive Language Model (RLM) architecture for Claude Code and other LLM-powered systems.

## The Problem

Traditional LLM usage loads entire documents into the prompt context:

```python
# Traditional approach (problematic)
response = llm(f"Analyze this document: {entire_document}")
```

This causes:
- **Token waste**: Irrelevant content consumes budget
- **Unpredictable costs**: No upper bound on spend
- **Quality degradation**: Reasoning suffers as context grows
- **Non-determinism**: Hard to audit or reproduce results

## The RLM Solution

RLM inverts the architecture:

| Traditional | RLM |
|-------------|-----|
| LLM ingests entire context | Context is external state |
| LLM controls iteration | Code controls iteration |
| Unbounded token usage | Hard budget limits |
| LLM aggregates results | Python aggregates results |
| Implicit reasoning | Explicit, auditable steps |

**Core principle**: LLMs reason on bounded chunks. Code handles everything else.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Task Entry                           │
│                    (Python function)                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Phase 1: Programmatic Narrowing                │
│                                                             │
│  context_search() ──► context_slice() ──► bounded chunks    │
│                                                             │
│  Code navigates context. No LLM involved.                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Phase 2: Semantic Interpretation               │
│                                                             │
│  semantic_subcall(prompt, chunk) ──► LLM reasoning          │
│                                                             │
│  • Depth = 1 (no nested calls)                              │
│  • Guards enforce all limits                                │
│  • Each call is bounded and auditable                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Aggregation (Python)                     │
│                                                             │
│  FINAL_ANSWER = {"findings": results, "count": len(results)}│
│                                                             │
│  Python constructs output. Not the LLM.                     │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Setup

```bash
# Clone or create project
cd rlm-claude-code

# Install dependencies
pip install -r requirements.txt

# Configure API key
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### 2. Run Example

```bash
# Analyze a document
python run.py document.txt

# Find errors in logs
python run.py server.log --task find_errors_in_log

# With custom budget
python run.py large_file.txt --cost 0.25 --timeout 30
```

### 3. Output

```json
{
  "status": "completed",
  "result": {
    "analysis": {
      "title": "Extracted Document Title",
      "key_points": [
        {"claim": "Main finding...", "confidence": "high"}
      ],
      "conclusion": "Summary of conclusions..."
    }
  },
  "budget_summary": {
    "total_cost_usd": 0.00234,
    "cost_budget_usd": 0.50,
    "total_calls": 4,
    "elapsed_seconds": 3.21
  }
}
```

## Project Structure

```
rlm-claude-code/
├── claude.md              # Policy file for Claude Code
├── README.md              # This file
├── requirements.txt       # Dependencies
├── .env.example           # API key template
├── run.py                 # Entry point
├── rlm/
│   ├── __init__.py
│   ├── guards.py          # Budget enforcement
│   ├── context_access.py  # Explicit context navigation
│   ├── subcalls.py        # LLM subcall interface
│   └── runtime.py         # Task execution harness
└── tasks/
    ├── __init__.py
    └── example_task.py    # Example tasks
```

## Core Modules

### `rlm/guards.py` — Budget Enforcement

```python
from rlm.guards import GuardConfig, init_guards

config = GuardConfig(
    max_cost=0.50,              # Maximum USD per task
    max_tokens_per_subcall=4000, # Token limit per call
    max_runtime_seconds=60.0,    # Wall-clock timeout
    model="gpt-4o-mini",         # Model to use
)

# Guards are automatically initialized by run_task()
```

**Enforced limits:**
| Limit | Default | On Violation |
|-------|---------|--------------|
| Cost | $0.50 | `CostLimitError` |
| Tokens | 4000/call | `TokenLimitError` |
| Depth | 1 | `RecursionDepthError` |
| Runtime | 60s | `RuntimeLimitError` |

### `rlm/context_access.py` — Context Navigation

```python
from rlm.context_access import (
    context_head,      # First n characters
    context_tail,      # Last n characters
    context_slice,     # Substring extraction
    context_search,    # Regex search with positions
    context_chunks,    # Iterate in bounded pieces
)

# Find relevant sections
matches = context_search(document, r"error|exception", max_hits=5)

# Extract bounded chunks
for match in matches:
    chunk = context_slice(document, match.start - 200, match.end + 200)
    # Process chunk...
```

### `rlm/subcalls.py` — Semantic Subcalls

```python
from rlm.subcalls import (
    semantic_subcall,       # Basic text response
    semantic_subcall_json,  # Parse JSON response
    semantic_subcall_bool,  # Yes/no questions
    semantic_subcall_choice, # Multiple choice
)

# Text response
summary = semantic_subcall(
    "Summarize the main point of this paragraph.",
    chunk
)

# JSON response
data = semantic_subcall_json(
    "Extract {\"sentiment\": \"pos|neg|neutral\", \"confidence\": 0.0-1.0}",
    chunk,
    default={"sentiment": "neutral", "confidence": 0.0}
)

# Boolean response
is_error = semantic_subcall_bool(
    "Does this describe an error condition?",
    chunk
)

# Choice response
severity = semantic_subcall_choice(
    "What is the severity?",
    chunk,
    choices=["critical", "warning", "info"]
)
```

### `rlm/runtime.py` — Task Execution

```python
from rlm.runtime import run_task, TaskBuilder

# Basic execution
result = run_task(my_task_function, context)

# Fluent builder
result = (
    TaskBuilder(my_task_function)
    .with_cost_budget(0.25)
    .with_runtime_limit(30.0)
    .run(context)
)

# Handle all statuses
if result["status"] == "completed":
    print(result["result"])
elif result["status"] == "partial":
    print(f"Partial results: {result['result']}")
    print(f"Stopped because: {result['error']}")
else:
    print(f"Error: {result['error']}")
```

## Writing Tasks

### Task Template

```python
def my_task(context: str) -> dict:
    """
    Task docstring explaining purpose.
    """

    # ===== PHASE 1: Programmatic Narrowing =====
    # Code navigates context, no LLM calls

    matches = context_search(context, r"relevant_pattern", max_hits=10)
    chunks = [
        context_slice(context, m.start - 200, m.end + 200)
        for m in matches
    ]

    # ===== PHASE 2: Semantic Interpretation =====
    # LLM reasons on bounded chunks (depth=1)

    results = []
    for chunk in chunks[:5]:  # Always bound iteration
        analysis = semantic_subcall(
            "Clear instruction for what to extract.",
            chunk
        )
        results.append(analysis)

    # ===== AGGREGATION =====
    # Python constructs final answer

    return {
        "findings": results,
        "count": len(results),
        "metadata": {"chunks_examined": len(chunks)}
    }
```

### Rules

1. **Never load context into prompts**
   ```python
   # WRONG
   llm(f"Analyze: {context}")

   # RIGHT
   chunk = context_slice(context, 0, 1000)
   semantic_subcall("Analyze this section.", chunk)
   ```

2. **Always use context_access functions**
   ```python
   # WRONG
   text = context[100:500]

   # RIGHT
   text = context_slice(context, 100, 500)
   ```

3. **Bound all iterations**
   ```python
   # WRONG
   for match in context_search(context, pattern):
       process(match)

   # RIGHT
   for match in context_search(context, pattern, max_hits=5)[:3]:
       process(match)
   ```

4. **Construct final answers in Python**
   ```python
   # WRONG
   return semantic_subcall("Summarize all findings and give final answer.", ...)

   # RIGHT
   return {"findings": findings, "summary": compute_summary(findings)}
   ```

## Philosophy

### LLMs are Reasoning Engines, Not Orchestrators

In RLM, the LLM's role is narrow and specific:
- Interpret meaning from bounded text
- Extract structured information
- Make semantic judgments

Everything else is code:
- Navigating context
- Deciding what to examine
- Iterating over sections
- Aggregating results
- Formatting output

### Budgets are Hard Constraints

Guards don't warn—they halt. When you hit a limit:
- Execution stops immediately
- Partial results are preserved
- Budget summary shows consumption

This makes costs **predictable** and **bounded**.

### Auditability Over Convenience

Every operation is explicit and logged:
- Context access is tracked
- Each subcall is recorded
- Final results trace back to specific chunks

No magic. No hidden reasoning.

## Claude Code Integration

The `claude.md` file is read by Claude Code as system policy. It:
- Declares RLM operating mode
- Prohibits loading context into prompts
- Requires all context access via Python
- Limits subcall depth to 1
- Mandates Python-constructed final answers

When using Claude Code with this project, the LLM operates within these constraints automatically.

## Configuration

### Environment Variables

```bash
# Required
OPENAI_API_KEY=sk-your-key-here

# Optional (override in code)
RLM_MAX_COST=0.50
RLM_MAX_RUNTIME=60
RLM_MODEL=gpt-4o-mini
```

### Programmatic Configuration

```python
from rlm.guards import GuardConfig
from rlm.runtime import run_task

config = GuardConfig(
    max_cost=1.00,
    max_tokens_per_subcall=8000,
    max_runtime_seconds=120.0,
    model="gpt-4o",
)

result = run_task(my_task, context, config)
```

## Error Handling

| Error | Meaning | Recovery |
|-------|---------|----------|
| `CostLimitError` | Spent too much | Partial results available |
| `RuntimeLimitError` | Took too long | Partial results available |
| `TokenLimitError` | Subcall too large | Reduce chunk size |
| `RecursionDepthError` | Nested subcalls | Flatten task structure |

```python
result = run_task(task, context)

if result["status"] == "partial":
    # Budget exceeded, but we have partial results
    partial = result["result"]
    remaining_budget = result["budget_summary"]["cost_remaining_usd"]
```

## License

MIT License. Use freely.

---

> "The best code is the code that doesn't run."
>
> In RLM, the LLM does less so the system does more—predictably, auditibly, and within budget.
