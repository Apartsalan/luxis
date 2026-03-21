---
name: systematic-debugging
description: Use when encountering any bug, test failure, or unexpected behavior, before proposing fixes
---

# Systematic Debugging

## Overview

Random fixes waste time and create new bugs. Quick patches mask underlying issues.

**Core principle:** ALWAYS find root cause before attempting fixes. Symptom fixes are failure.

## The Iron Law

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

If you haven't completed Phase 1, you cannot propose fixes.

## When to Use

Use for ANY technical issue:
- Test failures
- Bugs in production
- Unexpected behavior
- Performance problems
- Build failures
- Integration issues

**Use this ESPECIALLY when:**
- Under time pressure (emergencies make guessing tempting)
- "Just one quick fix" seems obvious
- You've already tried multiple fixes
- Previous fix didn't work
- You don't fully understand the issue

## The Four Phases

You MUST complete each phase before proceeding to the next.

### Phase 1: Root Cause Investigation

**BEFORE attempting ANY fix:**

1. **Read Error Messages Carefully**
   - Don't skip past errors or warnings
   - They often contain the exact solution
   - Read stack traces completely
   - Note line numbers, file paths, error codes

2. **Reproduce Consistently**
   - Can you trigger it reliably?
   - What are the exact steps?
   - Does it happen every time?
   - If not reproducible: gather more data, don't guess

3. **Check Recent Changes**
   - What changed that could cause this?
   - Git diff, recent commits
   - New dependencies, config changes
   - Environmental differences

4. **Gather Evidence in Multi-Component Systems**
   - For EACH component boundary: log what data enters and exits
   - Verify environment/config propagation
   - Run once to gather evidence showing WHERE it breaks
   - THEN analyze evidence to identify failing component

5. **Trace Data Flow**
   - Where does bad value originate?
   - What called this with bad value?
   - Keep tracing up until you find the source
   - Fix at source, not at symptom

### Phase 2: Pattern Analysis

1. **Find Working Examples** — locate similar working code in same codebase
2. **Compare Against References** — read reference implementation COMPLETELY
3. **Identify Differences** — list every difference, however small
4. **Understand Dependencies** — what other components does this need?

### Phase 3: Hypothesis and Testing

1. **Form Single Hypothesis** — state clearly: "I think X is the root cause because Y"
2. **Test Minimally** — make the SMALLEST possible change to test hypothesis
3. **Verify Before Continuing** — didn't work? Form NEW hypothesis, don't stack fixes

### Phase 4: Implementation

1. **Create Failing Test Case** — simplest possible reproduction
2. **Implement Single Fix** — address the root cause, ONE change at a time
3. **Verify Fix** — test passes? No other tests broken?
4. **If 3+ Fixes Failed: STOP** — question the architecture, don't attempt Fix #4

## Luxis-Specific Notes

- **No worktrees** — debug directly on main branch
- **Check stale DB state first** — run `alembic upgrade head` before assuming code is wrong
- **Docker context** — always run commands from repo root, use `MSYS_NO_PATHCONV=1` prefix
- **Financial calculations** — extra careful, use known-correct legal values for verification
- **Async patterns** — check for missing `await`, `selectinload` issues, `MissingGreenlet`
