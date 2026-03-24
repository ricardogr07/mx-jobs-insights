# Site and Dashboard

This guide documents the current public site generation and local Streamlit surfaces.

## Scope

The repo currently supports:

- resolving completed report artifacts for the public site
- generating the public MkDocs source from report outputs
- copying public-safe HTML and CSV assets into the docs tree
- running a local-first Streamlit dashboard over curated and report artifacts
- keeping public pages and local-private drill-down views separated

## Prerequisites

```powershell
python -m pip install -e .[dev]
# or
$env:PYTHONPATH='src'
```

The `site` command reads completed report artifacts under `artifacts/reports` and writes public MkDocs source under `docs/public` plus a site summary under `artifacts/site`.

The Streamlit app reads curated DuckDB or Parquet outputs plus the same report artifacts. It defaults to public-safe summaries, and any local-only private drill-down should stay clearly labeled in the UI.

## Site Commands

```powershell
$env:PYTHONPATH='src'
python -m mexico_linkedin_jobs_portfolio.interfaces.cli.main site --dry-run
python -m mexico_linkedin_jobs_portfolio.interfaces.cli.main site
```

## Streamlit Command

```powershell
$env:PYTHONPATH='src'
streamlit run src/mexico_linkedin_jobs_portfolio/interfaces/streamlit/app.py
```

Windows fallback:

```powershell
$env:PYTHONPATH='src'
python -m streamlit run src/mexico_linkedin_jobs_portfolio/interfaces/streamlit/app.py
```

## Public Boundary

Public outputs should remain limited to generated Markdown pages, public report HTML snapshots, public CSV downloads, and aggregate report summaries. The local Streamlit app may show private fields such as company, URL, and description text only inside the private drill-down area.
