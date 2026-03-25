# CI Pre-Push Verification Checklist

**Rule**: Before pushing to remote, must run the local quality gate and verify all checks pass.

**Status**: CI must be GREEN (all checks passing) before pushing to GitHub.

## Quick Start

Run this command locally before every push to remote:

```bash
python -m tox -e preflight
```

This runs the complete local CI pipeline equivalent to the GitHub Actions workflow.

---

## What the Preflight Check Includes

### 1. **Ruff Lint Check** (Code Quality)
```bash
ruff check .
```
- **Checks for**: Import sorting, unused imports, undefined names, security issues
- **Fixes auto-fixable issues** with: `ruff check --fix .`
- **Status**: MUST PASS ✓

### 2. **Ruff Format Check** (Code Style)
```bash
ruff format --check .
```
- **Checks for**: Consistent spacing, line length, indentation
- **Applies formatting** with: `ruff format .`
- **Status**: MUST PASS ✓

### 3. **MkDocs Strict Build** (Documentation)
```bash
python -m mkdocs build --strict
```
- **Checks for**: Documentation syntax errors and broken links (strict mode)
- **Builds to**: `./site/` directory
- **Status**: MUST PASS ✓

### 4. **Package Build** (Distribution)
```bash
python -m build --no-isolation
```
- **Checks for**: setuptools package integrity
- **Builds to**: `./dist/` directory
- **Status**: MUST PASS ✓

---

## Step-by-Step Pre-Push Workflow

### Step 1: Fix Linting Issues
```bash
# Check what needs fixing
python -m ruff check .

# Auto-fix most issues
python -m ruff check --fix .

# Verify fixes
python -m ruff check .
```

### Step 2: Fix Formatting Issues
```bash
# Check what needs fixing
python -m ruff format --check .

# Apply formatting to all files
python -m ruff format .

# Verify formatting
python -m ruff format --check .
```

### Step 3: Run Full Preflight
```bash
# Run all checks (lint, format, docs, build)
python -m tox -e preflight
```

### Step 4: Review Changes
```bash
# Show what changed
git diff --stat

# Review changes
git diff
```

### Step 5: Stage and Commit
```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "fix(ci): Resolve linting and formatting issues"
```

### Step 6: Push to Remote
```bash
# Only push AFTER preflight passes
git push origin main
```

---

## Common Issues & Solutions

### Issue: `ruff check` fails with import errors
**Solution**: Run `ruff check --fix .` to auto-organize imports

### Issue: `ruff format` fails with line length violations
**Solution**: Run `ruff format .` to auto-reformat lines

### Issue: MkDocs build fails with warnings
**Solution**: Check for undefined page references in `mkdocs.yml` nav configuration

### Issue: Package build fails
**Solution**: Ensure `pyproject.toml` is valid and all dependencies are listed

---

## CI Environments

### Local Development (Before Push)
```bash
python -m tox -e preflight    # Full quality gate
python -m pytest              # Run tests locally
```

### GitHub Actions (On Push)
GitHub automatically runs these jobs when you push:
- ✓ Ruff linting and formatting
- ✓ Pytest test suite
- ✓ MkDocs strict build
- ✓ Package build validation

**Only push when local preflight is GREEN** ✓

---

## Individual Check Commands

If you want to run checks individually:

```bash
# Lint and format only
python -m ruff check . && python -m ruff format .

# Docs only
python -m mkdocs build --strict

# Build only
python -m build --no-isolation

# Tests only
python -m pytest tests/ -v
```

---

## Configuration Files

The CI checks are configured in:
- **`pyproject.toml`**: Ruff linting and formatting rules
- **`tox.toml`**: Local CI environment definitions (`preflight`, `lint`, `docs`, `build`)
- **`mkdocs.yml`**: Documentation site configuration
- **`.github/workflows/ci.yml`**: GitHub Actions CI workflow (GitHub-side)

---

## Automation Tip

Add this as a Git pre-push hook to automate the check:

Create `.git/hooks/pre-push`:
```bash
#!/bin/bash
echo "Running preflight checks before push..."
python -m tox -e preflight
if [ $? -ne 0 ]; then
    echo "❌ Preflight failed! Fix issues before pushing."
    exit 1
fi
echo "✓ Preflight passed! Safe to push."
```

Make it executable:
```bash
chmod +x .git/hooks/pre-push
```

Now Git will automatically run the quality gate before allowing pushes.

---

## Last CI Status

### Latest Preflight Run
- **Date**: March 25, 2026
- **Status**: ✓ PASSING
- **Fixed Issues**: 
  - 28 auto-fixed linting violations
  - 5 manually fixed issues
  - 51 files reformatted
- **Result**: All checks passing ✓

### Before Next Push
1. Run: `python -m tox -e preflight`
2. Confirm: All checks PASS ✓
3. Then: `git push origin main`

---

**Remember**: GREEN CI before every push! 🟢
