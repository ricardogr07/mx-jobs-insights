# Tools and Commands

This page lists the exact local commands and tool statuses that matter during the current bootstrap and Phase-1 scaffolding stage.

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
- Status: `ready`

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

### `workspace_validate`
- Command: `python -m mexico_linkedin_jobs_portfolio.interfaces.cli.main ingest --source auto --dry-run --upstream-root ../LinkedInWebScraper`
- Purpose: validate the planned sibling upstream workspace shape and source resolution contract without mutating the source repo.
- Status: `ready`

### `ingest_dry_run_sqlite`
- Command: `python -m mexico_linkedin_jobs_portfolio.interfaces.cli.main ingest --source sqlite --dry-run`
- Purpose: run the planned SQLite ingestion shell in dry-run mode once the Phase-1 CLI exists.
- Status: `ready`

### `ingest_dry_run_csv`
- Command: `python -m mexico_linkedin_jobs_portfolio.interfaces.cli.main ingest --source csv --dry-run`
- Purpose: run the planned CSV ingestion shell in dry-run mode once the Phase-1 CLI exists.
- Status: `ready`

### `curate_dry_run_auto`
- Command: `python -m mexico_linkedin_jobs_portfolio.interfaces.cli.main curate --source auto --dry-run`
- Purpose: validate source resolution, canonical-model wiring, and dry-run curation summaries without writing curated outputs.
- Status: `ready`

### `curate_write_auto`
- Command: `python -m mexico_linkedin_jobs_portfolio.interfaces.cli.main curate --source auto`
- Purpose: run the first non-dry-run curated write path and persist DuckDB state plus Parquet sidecars.
- Status: `ready`

### `fixtures_regen`
- Command: `python scripts/make_sample_data.py`
- Purpose: regenerate the checked-in Phase-1 sample fixtures under `tests/data/upstream_workspace` from a local upstream workspace.
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
- This repo is now past the initial bootstrap and is entering Phase 1.
- Shell tools are marked by current observed behavior, not by ideal setup.
- Test is now `ready` because the offline suite is green, while the current Phase-1 shells cover both dry-run validation and the first curated write path.
- Bootstrap, docs, build, and preflight stay `ready` because the necessary project config files already exist.

## Phase 1 Planned Shells
These commands are planned references for the ingestion and curation scaffolding. They are documented now so subagents and reviewers use the same contract as phase 1 lands, including the standalone workspace-validation step before adapter implementation.

### `workspace_validate`
- Command: `python -m mexico_linkedin_jobs_portfolio.interfaces.cli.main ingest --source auto --dry-run --upstream-root ../LinkedInWebScraper`
- Status: ready
- Purpose: validate the sibling upstream workspace shape and source resolution contract before the SQLite and CSV adapters land.

### `ingest --source sqlite --dry-run`
- Command: `python -m mexico_linkedin_jobs_portfolio.interfaces.cli.main ingest --source sqlite --dry-run`
- Status: ready
- Purpose: validate the SQLite ingestion path and summary output without writing curated artifacts.

### `ingest --source csv --dry-run`
- Command: `python -m mexico_linkedin_jobs_portfolio.interfaces.cli.main ingest --source csv --dry-run`
- Status: ready
- Purpose: validate the CSV ingestion path and summary output without writing curated artifacts.

### `curate --source auto --dry-run`
- Command: `python -m mexico_linkedin_jobs_portfolio.interfaces.cli.main curate --source auto --dry-run`
- Status: ready
- Purpose: validate source resolution, canonical-model wiring, and dry-run curation summaries without writing curated outputs.

### `curate --source auto`
- Command: `python -m mexico_linkedin_jobs_portfolio.interfaces.cli.main curate --source auto`
- Status: ready
- Purpose: validate source resolution, canonical-model wiring, and the first non-dry-run curated write path that persists DuckDB plus Parquet outputs.

### `make_sample_data.py`
- Command: `python scripts/make_sample_data.py`
- Status: ready
- Purpose: regenerate the checked-in deterministic SQLite and CSV fixtures under `tests/data/upstream_workspace`.
