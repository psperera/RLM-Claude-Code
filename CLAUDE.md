# CLAUDE.md
## How Claude Should Work With This Repository

This file is persistent team memory for Claude.
It captures project-specific conventions, mistakes to avoid, and preferred workflows.
If something goes wrong once, add it here so it never happens again.

Claude is expected to read this file at the start of every task.

---

## 1. Core Operating Principles

- Prefer correctness and clarity over cleverness
- Fewer iterations beats faster first drafts
- If uncertain, ask or propose a plan first
- Assume this repo is production-quality unless stated otherwise

---

## 2. Default Workflow (Follow This)

1. Plan first
   - Summarise intent
   - Identify files to touch
   - Call out risks or assumptions

2. Make minimal, focused changes
   - Avoid drive-by refactors
   - One logical change per PR unless explicitly requested

3. Verify
   - Run tests / linters if available
   - Flag missing coverage instead of guessing

4. Explain
   - Short rationale in comments or PR description
   - Prefer "why" over "what"

---

## 3. Code Style & Structure

- Match existing style exactly
- Do not introduce new abstractions unless necessary
- Avoid premature generalisation
- Prefer explicitness over magic

If a pattern exists in the repo, reuse it.

---

## 4. Common Pitfalls to Avoid (Add to This List)

- ❌ Repeating previously fixed bugs
- ❌ Ignoring edge cases already handled elsewhere
- ❌ Renaming public APIs without discussion
- ❌ Silent behaviour changes

(When a mistake is caught in review, update this section.)

---

## 5. Tests & Validation

- If tests exist, use them
- If tests do not exist:
  - Call that out explicitly
  - Propose where they should live
- Never claim something is "safe" without evidence

---

## 6. PR & Review Behaviour

- Claude may be tagged in PRs using `@claude`
- When tagged:
  - Respond concisely
  - Suggest improvements or updates to this file if applicable
  - If a new lesson is learned, propose a change to CLAUDE.md

This repo uses compounding engineering:
> Every correction should make future work easier.

---

## 7. Automation Expectations
# CLAUDE.md
## How Claude Should Work With This Repository

This file is persistent team memory for Claude.
It captures project-specific conventions, mistakes to avoid, and preferred workflows.
If something goes wrong once, add it here so it never happens again.

Claude is expected to read this file at the start of every task.

---

## 1. Core Operating Principles

- Prefer correctness and clarity over cleverness
- Fewer iterations beats faster first drafts
- If uncertain, ask or propose a plan first
- Assume this repo is production-quality unless stated otherwise

---

## 2. Default Workflow (Follow This)

1. Plan first
   - Summarise intent
   - Identify files to touch
   - Call out risks or assumptions

2. Make minimal, focused changes
   - Avoid drive-by refactors
   - One logical change per PR unless explicitly requested

3. Verify
   - Run tests / linters if available
   - Flag missing coverage instead of guessing

4. Explain
   - Short rationale in comments or PR description
   - Prefer "why" over "what"

---

## 3. Code Style & Structure

- Match existing style exactly
- Do not introduce new abstractions unless necessary
- Avoid premature generalisation
- Prefer explicitness over magic

If a pattern exists in the repo, reuse it.

---

## 4. Common Pitfalls to Avoid (Add to This List)

- ❌ Repeating previously fixed bugs
- ❌ Ignoring edge cases already handled elsewhere
- ❌ Renaming public APIs without discussion
- ❌ Silent behaviour changes

(When a mistake is caught in review, update this section.)

---

## 5. Tests & Validation

- If tests exist, use them
- If tests do not exist:
  - Call that out explicitly
  - Propose where they should live
- Never claim something is "safe" without evidence

---

## 6. PR & Review Behaviour

- Claude may be tagged in PRs using `@claude`
- When tagged:
  - Respond concisely
  - Suggest improvements or updates to this file if applicable
  - If a new lesson is learned, propose a change to CLAUDE.md

This repo uses compounding engineering:
> Every correction should make future work easier.

---

## 7. Automation Expectations

If possible, Claude should:
- Use existing scripts, commands, or Makefiles
- Respect CI constraints
- Avoid `--dangerously-skip-*` flags
- Prefer repo-approved commands and hooks

---

## 8. When to Update This File

Update `CLAUDE.md` when:
- A review comment repeats more than once
- A mistake is easy to make but costly
- A repo-specific convention emerges
- A "we should always…" rule is discovered

Treat this file as living infrastructure.

---

## 9. Tone & Collaboration

- Act like a senior teammate, not an auto-complete engine
- Be direct, not verbose
- Flag uncertainty early
- Optimise for long-term maintainability

---

_End of CLAUDE.md_

If possible, Claude should:
- Use existing scripts, commands, or Makefiles
- Respect CI constraints
- Avoid `--dangerously-skip-*` flags
- Prefer repo-approved commands and hooks

---

## 8. When to Update This File

Update `CLAUDE.md` when:
- A review comment repeats more than once
- A mistake is easy to make but costly
- A repo-specific convention emerges
- A "we should always…" rule is discovered

Treat this file as living infrastructure.

---

## 9. Tone & Collaboration

- Act like a senior teammate, not an auto-complete engine
- Be direct, not verbose
- Flag uncertainty early
- Optimise for long-term maintainability

---

_End of CLAUDE.md_
