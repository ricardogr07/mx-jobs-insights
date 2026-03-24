# mx-jobs-insights

Bilingual Mexico LinkedIn jobs analytics portfolio powered by curated `LinkedInWebScraper` data.

Public site: <https://ricardogr07.github.io/mx-jobs-insights/>

## Current Status

This repo now has the backend MVP, public-site generation, GitHub-native automation, and the first cloud expansion path in place.

- Roadmap and reviewed phase boundaries: [PLAN.md](PLAN.md)
- Public docs source: [docs/](docs/)
- Internal implementation notes: [docs/development/](docs/development/)

Current CLI surfaces:

- `curate`: read upstream exports and persist curated DuckDB and Parquet outputs
- `report`: generate weekly or monthly bilingual report artifacts plus the public CSV
- `site`: materialize the public-first MkDocs source from report artifacts
- `pipeline`: orchestrate `curate`, `report`, `site`, and strict docs validation for local runs and GitHub Actions

## Workflows

- `.github/workflows/ci.yml`: minimal green gate for Ruff, pytest, `mkdocs build --strict`, and package build validation
- `.github/workflows/publish-portfolio-site.yml`: `Publish Portfolio Site`, the manual and scheduled workflow that checks out the upstream `LinkedInWebScraper` `data` branch, runs `pipeline`, and deploys GitHub Pages from the built artifact
- `.github/workflows/cloud-release.yml`: `Cloud Release`, the manual workflow that builds the containerized `pipeline`, pushes it to Artifact Registry, and can update the Cloud Run Job definition

## Local Development

Install the repo in editable mode with dev tools:

```powershell
python -m pip install -e ".[dev]"
```

Install the optional Phase 5 cloud clients when validating GCS or BigQuery delivery locally:

```powershell
python -m pip install -e ".[dev,cloud]"
```

Set the repo-local runtime environment before non-dry-run `report` or `pipeline` commands:

```powershell
Get-Content .\configs\local\report-env.ps1 | ForEach-Object { Invoke-Expression $_ }
$env:PYTHONPATH = "src"
```

Useful local commands:

```powershell
python -m mexico_linkedin_jobs_portfolio.interfaces.cli.main curate --source auto --upstream-root tests/data/upstream_workspace --curated-root artifacts/review-curated
python -m mexico_linkedin_jobs_portfolio.interfaces.cli.main report --cadence monthly --as-of 2026-04-01 --curated-root artifacts/review-curated --output-root artifacts/review-reports
python -m mexico_linkedin_jobs_portfolio.interfaces.cli.main site --report-root artifacts/review-reports --docs-root artifacts/review-docs
python -m mexico_linkedin_jobs_portfolio.interfaces.cli.main pipeline --cadence monthly --as-of 2026-04-01 --upstream-root tests/data/upstream_workspace
```

For offline local pipeline/report validation, set `MX_JOBS_OPENAI_BASE_URL=mock://responses` in the current shell before the command.

For Phase 5 cloud validation, the same shell can also set:

- `GOOGLE_CLOUD_PROJECT`
- `MX_JOBS_GCP_REGION`
- `MX_JOBS_GCS_BUCKET`
- `MX_JOBS_BIGQUERY_PRIVATE_DATASET`
- `MX_JOBS_BIGQUERY_PUBLIC_DATASET`
- optional `MX_JOBS_GCS_PREFIX`
- optional `MX_JOBS_UPSTREAM_REPO_URL` and `MX_JOBS_UPSTREAM_REF`

## Repo Layout

- `src/mexico_linkedin_jobs_portfolio/`: production code
- `tests/`: unit, integration, and workflow contract coverage
- `docs/`: public MkDocs source plus development notes
- `configs/`: local environment helpers and config scaffolding
- `scripts/`: reproducibility helpers such as fixture regeneration
- `artifacts/`: local generated outputs for curated data, reports, site builds, and diagnostics

