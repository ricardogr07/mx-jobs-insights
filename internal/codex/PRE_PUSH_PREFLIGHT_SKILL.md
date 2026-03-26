# Pre-Push Preflight Skill

**PURPOSE:** Enforce local quality checks before pushing to GitHub to prevent CI failures.

**USE WHEN:** Before running any `git push` command, or when preparing commits for remote.

**INVOKES:** Ruff linter, pytest test suite, MkDocs validation.

---

## What This Skill Does

Ensures all code quality checks pass locally before pushing, preventing failed CI runs that waste time and block other work.

## Pre-Push Checklist

Run these commands in order before `git push`:

### 1. **Ruff Linting** (catches style, unused vars, import issues)
```bash
python -m ruff check src tests
```

**Expected:** `All checks passed!`

**If fails:** Fix the error reported (e.g., unused variables, import formatting)

### 2. **Pytest Test Suite** (validates functionality)
```bash
python -m pytest tests/ -q
```

**Expected:** All tests pass (e.g., `79 passed in 2.34s`)

**If fails:** Run specific failing test to debug:
```bash
python -m pytest tests/test_name.py::test_function -v
```

### 3. **MkDocs Strict Build** (validates documentation)
```bash
python -m mkdocs build --strict
```

**Expected:** `Documentation built in X seconds` with exit code 0

**If fails:** Check for broken links or warnings shown in output

### 4. **Git Status Check** (verify files are committed)
```bash
git status
```

**Expected:** `working tree clean` (no uncommitted changes)

**If fails:** Commit remaining changes first

### Complete Pre-Push Script

```bash
#!/bin/bash
set -e  # Exit on first error

echo "Running Ruff linting..."
python -m ruff check src tests

echo "Running pytest..."
python -m pytest tests/ -q

echo "Building MkDocs..."
python -m mkdocs build --strict

echo "Checking git status..."
git status

echo "✓ All preflight checks passed!"
echo "Safe to push."
```

## Why This Matters

| Check | Catches | CI Cost if Missed |
|-------|---------|-------------------|
| Ruff | Unused vars, imports, style | 5-10 min CI run failure |
| Pytest | Logic errors, broken tests | 5-10 min CI run failure |
| MkDocs | Broken links, doc issues | 2-3 min CI run failure |
| Git | Untracked files | Merge conflicts, lost work |

**Total local preflight time:** ~30-60 seconds  
**Wasted CI time on each failure:** 12-23 minutes + team disruption

## Common Errors Fixed Locally

### Ruff: Unused Variable
```python
for idx, line in enumerate(lines):  # B007 - idx never used
    process(line)
```
**Fix:** Rename to `_idx` to indicate intentional non-use
```python
for _idx, line in enumerate(lines):
    process(line)
```

### Pytest: Test Function Returns Value
```python
def test_something():
    result = compute()
    return result  # ❌ Tests should not return values
```
**Fix:** Use `assert` instead
```python
def test_something():
    result = compute()
    assert result == expected
```

### MkDocs: Broken Link

Don't link to non-documentation files (Python source, config files, etc.). The mkdocs validator will flag these as broken.

**Bad example:**  
Markdown: `[script]` with path `../../scripts/file.py` — This fails validation

**Good solution:** Use backtick code formatting instead
```markdown
`scripts/file.py`     # ✓ No validation on code references
```

This allows referencing files outside docs/ without triggering link checks.

## Integration with Git Hooks (Optional)

To automate preflight before push, add a pre-push hook:

```bash
# Create .git/hooks/pre-push
#!/bin/bash
python -m ruff check src tests || exit 1
python -m pytest tests/ -q || exit 1
python -m mkdocs build --strict >> /dev/null 2>&1 || exit 1
echo "✓ Preflight checks passed"
```

Then make it executable:
```bash
chmod +x .git/hooks/pre-push
```

Now Git will automatically run these checks before allowing a push. To bypass (not recommended):
```bash
git push --no-verify
```

## Failure Recovery

If you accidentally pushed code that failed CI:

1. **Fix the issue locally**
   ```bash
   # Make fixes
   git add -A
   git commit -m "fix: Resolve CI failure"
   ```

2. **Run preflight before re-pushing**
   ```bash
   python -m ruff check src tests
   python -m pytest tests/ -q
   python -m mkdocs build --strict
   git push
   ```

3. **Review CI status** at https://github.com/ricardogr07/mx-jobs-insights/actions

## Related Documentation

- **Ruff Configuration:** `pyproject.toml` (tool.ruff section)
- **Pytest Configuration:** `pyproject.toml` (tool.pytest section)  
- **MkDocs Configuration:** `mkdocs.yml`
- **CI Workflow:** `.github/workflows/ci.yml`

## Workflow Rule

**✅ RULE: Always run preflight before `git push`**

- Run Ruff, pytest, and MkDocs locally first
- Fix all errors before remoting to save CI time
- Use git hooks to automate the checks
- Never use `--no-verify` unless absolutely necessary

---

**Skill Author:** Auto-generated best practices  
**Last Updated:** 2026-03-25  
**Criticality:** HIGH (prevents CI failures)
