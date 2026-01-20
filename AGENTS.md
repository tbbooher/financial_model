# Agent Instructions

## Prime Directive

**Never vibe code.** Every change must be validated by running tests.

```
Write → Run → Verify → Repeat
```

---

## Task Management (bd)

This project uses **bd** (beads) for issue tracking.

```bash
bd ready                              # Find available work
bd show <id>                          # View issue details  
bd update <id> --status in_progress   # Claim work
bd close <id>                         # Complete work
bd sync                               # Sync with git
```

**Workflow:**
1. Run `bd ready` to find the next task
2. Claim it with `bd update <id> --status in_progress`
3. Implement with write→run→verify loops
4. Run `bd close <id>` when tests pass
5. Commit and push

---

## Before Starting Any Work

1. **Verify repo is clean:** `git status`
2. **Run full test suite:** `pytest` (establish baseline)
3. **Check for available tasks:** `bd ready`

Do NOT touch application code until you have a green baseline.

---

## The Development Loop

For every change:

1. Make a **small, scoped edit**
2. Run the **relevant test subset** immediately
3. If **green** → commit and continue
4. If **red** → fix before doing anything else
5. Run **full test suite** after completing each task

**Commit early, commit often.** Rollback must always be trivial.

---

## Hard Rules

- **No unvalidated changes** — If you can't test it, don't ship it
- **Fix failures immediately** — Never proceed with a red test suite
- **One task at a time** — Finish and close before starting another
- **Always push** — Work isn't done until `git push` succeeds

---

## Session Completion (Landing the Plane)

Before ending any session:

1. **Close finished work:** `bd close <id>` for completed tasks
2. **File issues for remaining work:** Create beads for follow-up items
3. **Ensure tests pass:** Run full test suite
4. **Commit and push:**
   ```bash
   git add -A
   git commit -m "descriptive message"
   bd sync
   git push
   ```
5. **Verify:** `git status` must show "up to date with origin"

**Work is NOT complete until `git push` succeeds.**

---

## Project Commands

```bash
# Testing
pytest                    # Run all tests
pytest tests/unit/        # Run unit tests only
pytest -x                 # Stop on first failure
pytest -k "test_name"     # Run specific test

# Quality
flake8 app/               # Lint check
black app/ --check        # Format check

# Run
python run.py             # Start dev server
```

---

## When Stuck

1. Read the error message carefully
2. Check relevant test file for expected behavior
3. Search codebase for similar patterns: `grep -r "pattern" app/`
4. Check `TODO.md` for known issues
5. If blocked, file an issue with `bd` and move to next task
