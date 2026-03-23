# Phase 2 Report Usage

This page documents the current reviewed Phase 2 `report` command surface as it exists today.

## Current Scope

Phase 2 currently supports:

- reading curated DuckDB state or Parquet sidecars
- resolving closed weekly and monthly periods from `observed_at`
- building aggregate KPI payloads from the curated model
- rendering bilingual Markdown and HTML report artifacts
- writing a de-identified public CSV projection
- generating bilingual narrative output from aggregated metrics only
- printing a JSON run summary to stdout

Phase 2 is backend-only. The Streamlit dashboard, public site generation, and automation layers remain later-phase work.

## Reviewed Validation Notes

- The first reviewed live non-dry-run Phase 2 validation was executed against curated data built from the checked-in fixture workspace under `tests/data/upstream_workspace`.
- That fixture is intentionally small. It currently covers one observed source day and produces a tiny report artifact set so tests and local review stay deterministic.
- For a fuller local report, first run `curate` against your local `LinkedInWebScraper` `data` branch workspace, then point `report` at the resulting `artifacts/curated` directory.
- On some Windows setups, dot-sourcing `configs/local/report-env.ps1` is blocked by PowerShell execution policy. If that happens, load the environment variables another way before running `report`.

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

For non-dry-run report generation, set these environment variables:

- `OPENAI_API_KEY`
- `MX_JOBS_OPENAI_MODEL`
- `MX_JOBS_PUBLIC_KEY_SALT`

`MX_JOBS_OPENAI_BASE_URL` is optional and defaults to `https://api.openai.com/v1`.

## Dry-Run Commands

Validate the closed weekly report path:

```powershell
$env:PYTHONPATH='src'
python -m mexico_linkedin_jobs_portfolio.interfaces.cli.main report --cadence weekly --as-of 2026-03-23 --curated-root artifacts/curated --output-root artifacts/reports --dry-run
```

Validate the closed monthly report path:

```powershell
$env:PYTHONPATH='src'
python -m mexico_linkedin_jobs_portfolio.interfaces.cli.main report --cadence monthly --as-of 2026-04-01 --curated-root artifacts/curated --output-root artifacts/reports --dry-run
```

Use `--locale en`, `--locale es`, or the default `--locale all` to control which locale artifacts are rendered.

## First Non-Dry-Run Report Path

This is the current reviewed end-to-end report write command:

```powershell
$env:PYTHONPATH='src'
$env:OPENAI_API_KEY='...'
$env:MX_JOBS_OPENAI_MODEL='gpt-5.4'
$env:MX_JOBS_PUBLIC_KEY_SALT='...'
python -m mexico_linkedin_jobs_portfolio.interfaces.cli.main report --cadence monthly --as-of 2026-04-01 --curated-root artifacts/curated --output-root artifacts/reports
```

What this does:

- reads the curated DuckDB database or Parquet sidecars
- resolves the requested closed period
- builds the aggregate KPI payload
- generates bilingual narrative text from aggregate metrics only
- writes the de-identified public CSV projection
- exports Markdown and HTML report artifacts
- prints a JSON run summary

## Expected Outputs

With `--output-root artifacts/reports`, the current command writes a period directory such as:

- `artifacts/reports/monthly/2026-03/metrics.json`
- `artifacts/reports/monthly/2026-03/public_jobs.csv`
- `artifacts/reports/monthly/2026-03/report.en.md`
- `artifacts/reports/monthly/2026-03/report.es.md`
- `artifacts/reports/monthly/2026-03/report.en.html`
- `artifacts/reports/monthly/2026-03/report.es.html`
- `artifacts/reports/monthly/2026-03/run_summary.json`

The weekly path uses the same layout under `artifacts/reports/weekly/<period_id>/`.

## Run Summary

The `report` command currently prints JSON that includes:

- `status`
- `cadence`
- `locale`
- `locale_coverage`
- `period_id`
- `period_start`
- `period_end`
- `observation_count`
- `job_count`
- `source_run_count`
- `public_row_count`
- `narration_status`
- `artifact_dir`
- `metrics_path`
- `public_csv_path`
- `run_summary_path`

The reviewed success status for the write path is currently `report_written`.

## Current Limitations

- `report` reads curated DuckDB or Parquet outputs only; it does not read raw source data.
- Non-dry-run report generation fails closed when required OpenAI or public-key environment variables are missing.
- The public CSV is the de-identified row-level export for the selected period; company names remain aggregate-only.
- The current report MVP is backend-only. Public site and dashboard presentation remain later phases.


