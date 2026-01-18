# RLM Operating Policy for Claude Code

> **This is not agent code. This is an RLM runtime.**

## Operating Mode Declaration

This project operates under the **Recursive Language Model (RLM)** paradigm. Claude Code must adhere strictly to the constraints below. Violations constitute task failure.

---

## Core Principle

**LLMs reason. Code controls.**

- The LLM performs bounded semantic interpretation on small, explicitly-provided chunks
- Python handles all context access, iteration, aggregation, and control flow
- Long context is *external environment state*, not prompt content

---

## Mandatory Constraints

### 1. CONTEXT Loading Prohibition

**PROHIBITED**: Loading raw CONTEXT or large documents into prompts.

```python
# VIOLATION - Never do this
response = llm(f"Analyze this document: {context}")

# VIOLATION - Never do this
prompt = "Here is the full text:\n" + document_text
```

The LLM must never receive more than a bounded slice of context in any single call.

### 2. Context Access via Python Only

All context access MUST use functions from `rlm/context_access.py`:

- `context_head(context, n)` — first n characters
- `context_tail(context, n)` — last n characters
- `context_slice(context, start, end)` — substring extraction
- `context_search(context, pattern, max_hits)` — regex search

**No other context access patterns are permitted.**

```python
# CORRECT - Explicit, bounded access
chunk = context_slice(context, start=1000, end=2000)
result = semantic_subcall("Extract the main claim from this paragraph.", chunk)
```

### 3. Subcall Depth Limit

**Maximum recursion depth: 1**

Semantic subcalls cannot invoke further subcalls. The call graph is flat:

```
Task Entry
    └── semantic_subcall() → LLM reasoning (terminal)
    └── semantic_subcall() → LLM reasoning (terminal)
    └── semantic_subcall() → LLM reasoning (terminal)
```

Nested chains are architecturally prohibited.

### 4. Budget Enforcement

All subcalls pass through `rlm/guards.py`. The following limits are hard constraints:

| Budget Type | Default Limit | Behavior on Violation |
|-------------|---------------|----------------------|
| Cost | $0.50 per task | Immediate termination |
| Tokens | 4000 per subcall | Request rejected |
| Recursion | depth=1 | Architecturally blocked |
| Runtime | 60 seconds | Timeout exception |

These are not suggestions. Guard violations halt execution.

### 5. Final Answers from Python Variables

The final answer MUST be constructed from Python variables, not extracted from LLM output.

```python
# CORRECT - Python aggregates results
findings = []
for chunk in chunks:
    finding = semantic_subcall("Extract key fact.", chunk)
    findings.append(finding)
FINAL_ANSWER = {"findings": findings, "count": len(findings)}

# VIOLATION - LLM produces final answer directly
FINAL_ANSWER = llm("Summarize everything and give me the final answer.")
```

---

## Two-Phase Task Pattern

Every task follows this structure:

### Phase 1: Programmatic Narrowing (Code)
- Search context for relevant regions
- Slice to bounded chunks
- Filter and select what matters

### Phase 2: Semantic Interpretation (LLM)
- Single subcall per chunk
- Bounded input, bounded output
- No further subcalls

```python
def execute_task(context: str) -> dict:
    # Phase 1: Programmatic narrowing
    matches = context_search(context, r"error|exception|failed", max_hits=5)
    chunks = [context_slice(context, m.start - 200, m.end + 200) for m in matches]

    # Phase 2: Semantic interpretation
    analyses = []
    for chunk in chunks[:3]:  # Bounded iteration
        analysis = semantic_subcall(
            "Classify this error: critical, warning, or info. Return JSON.",
            chunk
        )
        analyses.append(analysis)

    # Python constructs final answer
    return {"error_analyses": analyses, "total_examined": len(chunks)}
```

---

## What This Enables

- **Predictable costs**: Budget is known before execution
- **Auditability**: Every context access is explicit and logged
- **Scalability**: Pattern works for gigabytes of context
- **Determinism**: Code controls aggregation, not LLM whims
- **Safety**: Guards cannot be bypassed

---

## Violation Examples

| Pattern | Status | Why |
|---------|--------|-----|
| `llm(context)` | VIOLATION | Raw context in prompt |
| `subcall(subcall(...))` | VIOLATION | Nested depth > 1 |
| `for page in all_pages: llm(page)` | VIOLATION | Unbounded iteration |
| `return llm("give final answer")` | VIOLATION | LLM produces final answer |
| `context[1000:2000]` | VIOLATION | Direct slice, not via accessor |

---

## Summary

When working in this codebase:

1. Never load CONTEXT into prompts
2. Always use `rlm/context_access.py` functions
3. Keep subcall depth at 1
4. Respect all budget limits
5. Construct final answers in Python

**The architecture enforces these constraints. Work with them, not around them.**
