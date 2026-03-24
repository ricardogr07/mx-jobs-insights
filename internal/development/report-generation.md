# Report Generation

This guide documents the current `report` command surface.

## Scope

The repo currently supports:

- reading curated DuckDB state or Parquet sidecars
- resolving closed weekly and monthly periods from `observed_at`
- building aggregate KPI payloads from the curated model
- rendering bilingual Markdown and HTML report artifacts
- writing a de-identified public CSV projection
- generating narrative output from aggregated metrics only
- printing a JSON run summary to stdout

## Fixture Note

The checked-in fixture workspace under `tests/data/upstream_workspace` is intentionally small. It exists to keep tests and local review deterministic, not to represent full production volumes.

## Prerequisites

```powershell
python -m pip install -e .[dev]
# or
$env:PYTHONPATH='src'
```

For non-dry-run report generation, set:
- `OPENAI_API_KEY`
- `MX_JOBS_OPENAI_MODEL`
- `MX_JOBS_PUBLIC_KEY_SALT`
- optional `MX_JOBS_OPENAI_BASE_URL`

## Dry Runs

```powershell
$env:PYTHONPATH='src'
python -m mexico_linkedin_jobs_portfolio.interfaces.cli.main report --cadence weekly --as-of 2026-03-23 --curated-root artifacts/curated --output-root artifacts/reports --dry-run
python -m mexico_linkedin_jobs_portfolio.interfaces.cli.main report --cadence monthly --as-of 2026-04-01 --curated-root artifacts/curated --output-root artifacts/reports --dry-run
```

## Write Path

```powershell
$env:PYTHONPATH='src'
$env:OPENAI_API_KEY='...'
$env:MX_JOBS_OPENAI_MODEL='gpt-5.4-nano'
$env:MX_JOBS_PUBLIC_KEY_SALT='...'
python -m mexico_linkedin_jobs_portfolio.interfaces.cli.main report --cadence monthly --as-of 2026-04-01 --curated-root artifacts/curated --output-root artifacts/reports
```

The command writes `metrics.json`, `public_jobs.csv`, bilingual Markdown and HTML, and `run_summary.json` under `artifacts/reports/<cadence>/<period_id>/`.

## Notes

- `report` reads curated outputs only; it does not read raw source data
- non-dry-run report generation fails closed when required runtime variables are missing
- the public CSV is period-scoped and de-identified
