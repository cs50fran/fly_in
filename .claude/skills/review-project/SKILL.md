---
name: review-project
description: This skill should be used when the user asks to "review the project", "analyze the project", "check the project for errors", "audit the codebase", or wants a full project health report with problems, bugs, and optimizations.
argument-hint: [path]
allowed-tools: [Read, Glob, Grep, Bash, Agent]
---

# Review Project

Perform a full project review by dispatching one sub-agent per top-level folder, then summarize all findings.

## Instructions

### Step 1 — Discover folders

List the top-level folders in the project root (or `$ARGUMENTS` if provided). Exclude hidden directories (`.git`, `.claude`, etc.), virtual environments (`fly_venv`, `venv`, `__pycache__`), and asset/binary folders (`assets`).

For this project the folders to review are:
- `models/`
- `parser/`
- `solver/`
- `turns/`
- `visual/`
- `tests/`

Also include the root-level files (`fly_in.py`, `requirements.txt`, `CLAUDE.md`) as an extra "root" target.

### Step 2 — Launch parallel sub-agents

Launch **one Explore sub-agent per folder** (plus one for root files), all in parallel. Each agent receives this prompt:

> You are a code reviewer. Thoroughly read every `.py` file inside `<FOLDER>/`. For each file report:
> 1. **Errors / Bugs** — logic errors, wrong assumptions, missing edge-case handling, incorrect algorithm behavior.
> 2. **Code quality issues** — dead code, unused imports, unclear naming, missing type hints where they matter.
> 3. **Optimizations** — performance improvements, simpler data structures, better use of existing libraries.
> 4. **Cross-cutting concerns** — anything that looks wrong given the project context (drone pathfinding + simulation + pygame).
>
> Return a structured list. For each finding include: file path, line number (if applicable), severity (error / warning / suggestion), and a one-sentence explanation.

### Step 3 — Synthesize results

After all sub-agents return, produce a final report with the following structure:

```
## Project Review Report

### Errors & Bugs
<list — file:line — description>

### Warnings & Code Quality
<list — file:line — description>

### Optimizations & Suggestions
<list — file:line — description>

### Summary
<2–4 sentence overall assessment>
```

Group findings by severity. Deduplicate overlapping findings from different agents. Prioritize actionable items over style nitpicks.
