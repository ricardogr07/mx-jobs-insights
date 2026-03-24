# Phase 4 Automation Usage

This page documents the current reviewed Phase 4 automation entrypoint and the GitHub Actions contract around it.

## Current Scope

Phase 4 currently supports:

- one `pipeline` CLI entrypoint that reuses the existing `curate`, `report`, and `site` seams
- fixture-backed local validation for weekly and monthly automation flows
- one GitHub Actions orchestrator for manual dispatch and scheduled publication
- artifact-based GitHub Pages deployment without automation commits back to `main`
- public-safe diagnostic artifacts that exclude curated private data

Phase 4 is GitHub-native only. Cloud deployment, Terraform, BigQuery, and non-GitHub runners remain Phase 5 work.

## Runtime Inputs

The `pipeline` CLI accepts:

- `--cadence {weekly,monthly}`
- `--as-of YYYY-MM-DD` optional
- `--source {auto,sqlite,csv}` default `auto`
- `--upstream-root PATH`
- `--curated-root PATH`
- `--report-root PATH`
- `--docs-root PATH`
- `--locale {en,es,all}` default `all`
- `--dry-run`

For non-dry-run published automation, the same report runtime environment remains required:

- `OPENAI_API_KEY`
- `MX_JOBS_OPENAI_MODEL`
- `MX_JOBS_PUBLIC_KEY_SALT`
- optional override: `MX_JOBS_OPENAI_BASE_URL`

For offline local validation, set `MX_JOBS_OPENAI_BASE_URL=mock://responses` to exercise the full write path without live network calls. Published automation should keep the real OpenAI API base URL or omit the override.

## Local Validation Commands

Dry run over the checked-in upstream workspace fixture:

```powershell
$env:PYTHONPATH='src'
python -m mexico_linkedin_jobs_portfolio.interfaces.cli.main pipeline --cadence weekly --dry-run --upstream-root tests/data/upstream_workspace
```

Fixture-backed weekly full run (the checked-in fixture resolves this closed week to an empty-period report bundle):

```powershell
$env:PYTHONPATH='src'
python -m mexico_linkedin_jobs_portfolio.interfaces.cli.main pipeline --cadence weekly --as-of 2026-03-30 --upstream-root tests/data/upstream_workspace --curated-root artifacts/review-curated-weekly --report-root artifacts/review-reports-weekly --docs-root artifacts/review-docs-weekly
```

Fixture-backed monthly full run (use the mock base URL when outbound network access is unavailable):

```powershell
$env:PYTHONPATH='src'
$env:MX_JOBS_OPENAI_BASE_URL='mock://responses'
python -m mexico_linkedin_jobs_portfolio.interfaces.cli.main pipeline --cadence monthly --as-of 2026-04-01 --upstream-root tests/data/upstream_workspace --curated-root artifacts/review-curated-monthly --report-root artifacts/review-reports-monthly --docs-root artifacts/review-docs-monthly
```

What the non-dry-run pipeline does:

- validates the upstream workspace contract
- writes curated DuckDB and Parquet outputs
- writes the selected weekly or monthly report bundle
- regenerates the public MkDocs source
- runs `python -m mkdocs build --strict`
- writes `artifacts/pipeline/run_summary.json`

## GitHub Actions Contract

The orchestrator workflow is `.github/workflows/publish-portfolio-site.yml`, displayed in GitHub Actions as `Publish Portfolio Site`.

It:

- checks out this repo
- checks out `ricardogr07/LinkedInWebScraper` at ref `data` into `LinkedInWebScraper`
- installs the repo with `python -m pip install -e .[dev]`
- runs the `pipeline` CLI with `--upstream-root LinkedInWebScraper`
- uploads the built `site/` directory as the Pages artifact
- deploys GitHub Pages from that artifact only
- writes a GitHub Actions job summary with cadence, step outcomes, and the public Pages link
- uploads a separate 14-day diagnostic artifact with public-safe run summaries and report metadata

Required GitHub configuration:

- secret: `OPENAI_API_KEY`
- secret: `MX_JOBS_PUBLIC_KEY_SALT`
- variable: `MX_JOBS_OPENAI_MODEL`
- optional variable: `MX_JOBS_OPENAI_BASE_URL`

Manual dispatch inputs:

- `cadence`
- `as_of_date`
- `deploy_pages`

Scheduled defaults:

- weekly: Mondays at `14:00 UTC`
- monthly: day `1` at `15:00 UTC`

## Public And Private Boundary

Phase 4 automation must not publish or upload private curated data.

Allowed automation artifacts:

- GitHub Pages build artifact from the generated `site/` directory
- pipeline, site, and report run summaries
- aggregate report metadata and public-safe report outputs

Forbidden automation artifacts:

- curated DuckDB files
- Parquet sidecars
- private Streamlit drill-down data
- raw upstream private fields outside the approved public/report artifacts

