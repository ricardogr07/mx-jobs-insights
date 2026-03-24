# Phase 3 Site And Dashboard Usage

This page documents the current reviewed Phase 3 presentation commands as they exist today.

## Current Scope

Phase 3 currently supports:

- resolving completed report artifacts for the public site
- generating the public MkDocs source from Phase 2 report outputs
- copying public-safe HTML and CSV assets into the docs tree
- running a local-first Streamlit dashboard over curated and report artifacts
- keeping public pages and local-private drill-down views separated

Phase 3 is presentation-focused. GitHub Actions deployment, Pages publishing automation, and cloud hosting remain later-phase work.

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

The Phase 3 site command reads completed Phase 2 report artifacts under `artifacts/reports` and writes public MkDocs source under `docs/public` plus a site summary under `artifacts/site`.

The Streamlit app reads the curated DuckDB/Parquet outputs and the same report artifacts. It defaults to public-safe summaries, and any local-only private drill-down should stay clearly labeled in the UI.

## Site Commands

Resolve the public site index without writing MkDocs source pages:

```powershell
$env:PYTHONPATH='src'
python -m mexico_linkedin_jobs_portfolio.interfaces.cli.main site --dry-run
```

Generate the public MkDocs source and copied public assets:

```powershell
$env:PYTHONPATH='src'
python -m mexico_linkedin_jobs_portfolio.interfaces.cli.main site
```

What this does:

- reads completed report artifacts only
- resolves the latest weekly and monthly report bundles
- writes the public Markdown pages into `docs/public`
- copies the public HTML snapshots and CSV downloads into the public asset tree
- writes a JSON site summary under `artifacts/site/run_summary.json`

## Streamlit Command

Run the local dashboard entrypoint:

```powershell
$env:PYTHONPATH='src'
streamlit run src/mexico_linkedin_jobs_portfolio/interfaces/streamlit/app.py
```

If `streamlit` is not on `PATH` in your Windows user install, use:

```powershell
$env:PYTHONPATH='src'
python -m streamlit run src/mexico_linkedin_jobs_portfolio/interfaces/streamlit/app.py
```

What this does:

- loads the report catalog and curated data through the shared presentation loaders
- defaults to public-safe report summaries and period selection
- exposes local-only drill-down data in a clearly labeled private section
- stays read-only; there is no edit or publish path in the MVP

## Public Boundary

The public site should remain limited to:

- generated Markdown pages
- public report HTML snapshots
- public CSV downloads
- aggregate report summaries and archive links

The local Streamlit app may show private fields such as company, URL, and description text, but only inside the private drill-down area and only in the local app.

