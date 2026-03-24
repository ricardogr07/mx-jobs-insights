# GitHub Automation

This guide documents the current `pipeline` entrypoint and the GitHub Actions publication contract around it.

## Scope

The repo currently supports:

- one `pipeline` CLI entrypoint that reuses `curate`, `report`, and `site`
- fixture-backed local validation for weekly and monthly automation flows
- one GitHub Actions orchestrator for manual dispatch and scheduled publication
- artifact-based GitHub Pages deployment without automation commits back to `main`
- public-safe diagnostic artifacts that exclude curated private data

## Runtime Inputs

The `pipeline` CLI accepts:
- `--cadence {weekly,monthly}`
- `--as-of YYYY-MM-DD`
- `--source {auto,sqlite,csv}`
- `--upstream-root`
- `--curated-root`
- `--report-root`
- `--docs-root`
- `--locale {en,es,all}`
- `--dry-run`

Non-dry-run runs require the same report runtime environment used by `report`.

## Local Validation

```powershell
$env:PYTHONPATH='src'
python -m mexico_linkedin_jobs_portfolio.interfaces.cli.main pipeline --cadence weekly --dry-run --upstream-root tests/data/upstream_workspace
python -m mexico_linkedin_jobs_portfolio.interfaces.cli.main pipeline --cadence weekly --as-of 2026-03-30 --upstream-root tests/data/upstream_workspace --curated-root artifacts/review-curated-weekly --report-root artifacts/review-reports-weekly --docs-root artifacts/review-docs-weekly
$env:MX_JOBS_OPENAI_BASE_URL='mock://responses'
python -m mexico_linkedin_jobs_portfolio.interfaces.cli.main pipeline --cadence monthly --as-of 2026-04-01 --upstream-root tests/data/upstream_workspace --curated-root artifacts/review-curated-monthly --report-root artifacts/review-reports-monthly --docs-root artifacts/review-docs-monthly
```

## GitHub Actions Contract

The publication workflow is `.github/workflows/publish-portfolio-site.yml`, displayed in GitHub Actions as `Publish Portfolio Site`.

It:
- checks out this repo plus `ricardogr07/LinkedInWebScraper@data`
- installs the repo with `python -m pip install -e .[dev]`
- runs `pipeline` with `--upstream-root LinkedInWebScraper`
- uploads the built `site/` directory as the Pages artifact
- deploys GitHub Pages from that artifact only
- writes a workflow summary with cadence, step outcomes, and the public Pages link

Required GitHub configuration:
- secret: `OPENAI_API_KEY`
- secret: `MX_JOBS_PUBLIC_KEY_SALT`
- variable: `MX_JOBS_OPENAI_MODEL`
- optional variable: `MX_JOBS_OPENAI_BASE_URL`
