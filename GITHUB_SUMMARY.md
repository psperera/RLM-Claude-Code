# RLM: Recursive Language Model Runtime

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenAI](https://img.shields.io/badge/OpenAI-API-green.svg)](https://openai.com/)

> **This is not agent code. This is an RLM runtime.**

A production-ready implementation of the [Recursive Language Model (RLM)](https://arxiv.org/pdf/2512.24601) architecture for bounded, cost-predictable LLM operations.

---

## The Problem

Traditional LLM usage suffers from fundamental issues at scale:

| Issue | Impact |
|-------|--------|
| Entire documents loaded into context | Token waste, unpredictable costs |
| LLM controls iteration | Non-deterministic behavior |
| No budget enforcement | Runaway API spend |
| Implicit reasoning chains | Impossible to audit |

## The RLM Solution

**Invert the architecture**: LLMs reason on bounded chunks. Code controls everything else.

```
┌─────────────────────────────────────────┐
│         Phase 1: Code Navigates         │
│   context_search() → context_slice()    │
│         No LLM calls here               │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│      Phase 2: LLM Interprets            │
│   semantic_subcall(prompt, chunk)       │
│   Bounded input, depth=1, guarded       │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│      Phase 3: Code Aggregates           │
│   Python constructs final answer        │
│         Not the LLM                     │
└─────────────────────────────────────────┘
```

## Key Features

- **Hard Budget Limits**: Cost ($), tokens, runtime, recursion depth — all enforced
- **Explicit Context Access**: Auditable `context_search()`, `context_slice()` functions
- **Depth=1 Subcalls**: No nested LLM chains, flat call graph
- **Partial Result Recovery**: Budget exceeded? Get what was completed
- **Streamlit GUI**: Claude-styled web interface included

## Quick Start

```bash
# Clone and setup
git clone https://github.com/yourusername/rlm-claude-code.git
cd rlm-claude-code
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Add your OPENAI_API_KEY to .env

# Run CLI
python run.py sample_context.txt

# Or run web UI
streamlit run app.py
```

## Example Output

```json
{
  "status": "completed",
  "result": {
    "title": "Sample Document",
    "key_points": [{"claim": "...", "confidence": "high"}],
    "conclusion": "..."
  },
  "budget_summary": {
    "total_cost_usd": 0.00032,
    "total_calls": 7,
    "elapsed_seconds": 6.2
  }
}
```

## Project Structure

```
rlm-claude-code/
├── claude.md           # Policy file for Claude Code
├── app.py              # Streamlit web UI
├── run.py              # CLI entry point
├── rlm/
│   ├── guards.py       # Budget enforcement
│   ├── context_access.py   # Explicit navigation
│   ├── subcalls.py     # LLM interface (depth=1)
│   └── runtime.py      # Task execution
└── tasks/
    └── example_task.py # Demo tasks
```

## Guard System

| Limit | Default | On Violation |
|-------|---------|--------------|
| Cost | $0.50 | `CostLimitError` |
| Tokens/call | 4000 | `TokenLimitError` |
| Depth | 1 | `RecursionDepthError` |
| Runtime | 60s | `RuntimeLimitError` |

## Writing Tasks

```python
def my_task(context: str) -> dict:
    # Phase 1: Code navigates
    matches = context_search(context, r"error", max_hits=5)

    # Phase 2: LLM interprets (bounded)
    results = []
    for m in matches[:3]:
        chunk = context_slice(context, m.start-200, m.end+200)
        analysis = semantic_subcall("Classify this error.", chunk)
        results.append(analysis)

    # Phase 3: Code aggregates
    return {"errors": results, "count": len(results)}
```

## Web Interface

![RLM GUI](https://via.placeholder.com/800x400?text=Claude-styled+Streamlit+UI)

Features:
- Task selection (Analyze Document, Find Errors, Extract Entities)
- Real-time budget controls
- Metrics display (cost, calls, tokens, time)
- Formatted results with raw JSON view

## Philosophy

> "The best LLM code is the code that doesn't run."

RLM constrains what LLMs do so the system does more — predictably, auditibly, within budget.

## Based On

- [Recursive Language Models (arXiv:2512.24601)](https://arxiv.org/pdf/2512.24601)

## License

MIT
