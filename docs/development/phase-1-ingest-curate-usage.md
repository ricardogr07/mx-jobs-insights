# Phase 1 Ingest And Curate Usage

This page documents the current reviewed Phase 1 command surface as it exists
today.

## Current Scope

Phase 1 currently supports:

- validating the upstream workspace contract
- loading SQLite or CSV source data into the canonical observation/entity model
- writing the first curated DuckDB database
- exporting Parquet sidecars for the curated tables
- printing a JSON run summary to stdout

Phase 1 does not yet make `ingest` a non-dry-run write command. The first real
write path is `curate`.

## Prerequisites

From the repo root, use one of these approaches:

1. Install the package in editable mode:

```powershell
python -m pip install -e .[dev]
```

2. Or, for an ad hoc local run from the checkout, set `PYTHONPATH`:

```powershell
$env:PYTHONPATH='src'
```

The examples below assume you are running from `C:\git\mx-jobs-insights`.

## Dry-Run Commands

Validate the SQLite ingestion path:

```powershell
$env:PYTHONPATH='src'
python -m mexico_linkedin_jobs_portfolio.interfaces.cli.main ingest --source sqlite --dry-run --upstream-root tests/data/upstream_workspace
```

Validate the CSV ingestion path:

```powershell
$env:PYTHONPATH='src'
python -m mexico_linkedin_jobs_portfolio.interfaces.cli.main ingest --source csv --dry-run --upstream-root tests/data/upstream_workspace
```

Validate canonical curation wiring without writing outputs:

```powershell
$env:PYTHONPATH='src'
python -m mexico_linkedin_jobs_portfolio.interfaces.cli.main curate --source auto --dry-run --upstream-root tests/data/upstream_workspace
```

## First Non-Dry-Run Curate Path

This is the current reviewed end-to-end write command:

```powershell
$env:PYTHONPATH='src'
python -m mexico_linkedin_jobs_portfolio.interfaces.cli.main curate --source auto --upstream-root tests/data/upstream_workspace --curated-root artifacts/review-curated
```

What this does:

- reads the upstream source workspace
- resolves the source mode
- normalizes records into the Phase 1 canonical model
- writes curated DuckDB state
- exports Parquet sidecars
- prints a JSON run summary

`auto` currently prefers SQLite when both SQLite and CSV sources are present.

## Expected Outputs

With `--curated-root artifacts/review-curated`, the current command writes:

- `artifacts/review-curated/mx_jobs_insights.duckdb`
- `artifacts/review-curated/parquet/source_runs.parquet`
- `artifacts/review-curated/parquet/job_observations.parquet`
- `artifacts/review-curated/parquet/job_entities.parquet`

## Run Summary

The non-dry-run `curate` command currently prints JSON that includes:

- `status`
- `resolved_source_mode`
- `source_run_count`
- `observation_count`
- `entity_count`
- `duckdb_path`
- `parquet_root`
- `workspace_validation`

The reviewed success status for the write path is currently `curation_written`.

## Real Upstream Workspace

When using a local `LinkedInWebScraper` workspace instead of the checked-in
fixtures, point `--upstream-root` at that workspace:

```powershell
$env:PYTHONPATH='src'
python -m mexico_linkedin_jobs_portfolio.interfaces.cli.main curate --source auto --upstream-root ..\LinkedInWebScraper --curated-root artifacts/curated
```

## Current Limitations

- `ingest` remains dry-run-only in Phase 1.
- The strongest reviewed non-dry-run path is `curate --source auto`, which
  resolves to SQLite when both source types exist.
- Public filtering is still out of scope for Phase 1. The curated model can
  still contain richer private fields.
