# Tools and Commands

This page lists the exact local commands and tool statuses that matter during the current bootstrap stage.

## Repo Commands

### `bootstrap`
- Command: `python -m pip install -e .[dev]`
- Purpose: install the local development toolchain for lint, docs, test, and build work.
- Status: `ready`

### `status`
- Command: `git status --short`
- Purpose: inspect the worktree before and after a reviewed step.
- Status: `ready`

### `diff`
- Command: `git diff --stat`
- Purpose: summarize the current step's file-level changes for review.
- Status: `ready`

### `python_check`
- Command: `python --version`
- Purpose: confirm the active Python interpreter before tooling bootstrap lands.
- Status: `ready`

### `test`
- Command: `python -m pytest -q`
- Purpose: run the default offline test suite once tests are added.
- Status: `planned`

### `preflight`
- Command: `python -m tox -e preflight`
- Purpose: run the current local quality gate for lint, docs, and build checks.
- Status: `ready`

### `docs`
- Command: `python -m mkdocs build --strict`
- Purpose: build project docs through MkDocs.
- Status: `ready`

### `build`
- Command: `python -m build --no-isolation`
- Purpose: build the package from the current working tree.
- Status: `ready`

## Local Tool Status

### `git`
- Check: `git status --short`
- Status: `available_now`

### `python`
- Check: `python --version`
- Status: `available_now`

### `gh`
- Check: `gh auth status`
- Status: `blocked_or_misconfigured`
- Current note: the CLI is installed, but the active GitHub token is invalid in this environment.

### `codex`
- Check: `codex --help`
- Status: `blocked_or_misconfigured`
- Current note: direct shell invocation is blocked by PowerShell execution policy in this environment, even though Codex is available through the editor workflow.

## Why The Commands Use Conservative Status Labels
- This repo is still in phase 0.
- Shell tools are marked by current observed behavior, not by ideal setup.
- Test commands remain `planned` until the repo has real tests.
- Bootstrap, docs, build, and preflight are marked `ready` because this step adds the necessary project config files.