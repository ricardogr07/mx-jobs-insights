# Ingestion and Curation

This guide documents the current ingestion and curation command surface.

## Scope

The repo currently supports:

- validating the upstream workspace contract
- loading SQLite or CSV source data into the canonical observation and entity model
- writing the curated DuckDB database
- exporting Parquet sidecars for the curated tables
- printing a JSON run summary to stdout

`ingest` remains a dry-run inspection surface. Durable writes happen through `curate`.

## Prerequisites

From the repo root, either install the package in editable mode or set `PYTHONPATH`:

```powershell
python -m pip install -e .[dev]
# or
$env:PYTHONPATH='src'
```

## Dry Runs

```powershell
$env:PYTHONPATH='src'
python -m mexico_linkedin_jobs_portfolio.interfaces.cli.main ingest --source sqlite --dry-run --upstream-root tests/data/upstream_workspace
python -m mexico_linkedin_jobs_portfolio.interfaces.cli.main ingest --source csv --dry-run --upstream-root tests/data/upstream_workspace
python -m mexico_linkedin_jobs_portfolio.interfaces.cli.main curate --source auto --dry-run --upstream-root tests/data/upstream_workspace
```

## Curated Write Path

```powershell
$env:PYTHONPATH='src'
python -m mexico_linkedin_jobs_portfolio.interfaces.cli.main curate --source auto --upstream-root tests/data/upstream_workspace --curated-root artifacts/review-curated
```

What it does:
- reads the upstream workspace
- resolves the source mode
- normalizes records into the canonical model
- writes curated DuckDB state
- exports Parquet sidecars
- prints a JSON run summary

`auto` currently prefers SQLite when both SQLite and CSV sources are present.

## Expected Outputs

- `artifacts/review-curated/mx_jobs_insights.duckdb`
- `artifacts/review-curated/parquet/source_runs.parquet`
- `artifacts/review-curated/parquet/job_observations.parquet`
- `artifacts/review-curated/parquet/job_entities.parquet`

## Notes

- point `--upstream-root` at your local `LinkedInWebScraper` workspace for real data runs
- the curated model can retain richer private fields; public filtering happens later in the pipeline
