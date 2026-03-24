# mx-jobs-insights

Bilingual Mexico LinkedIn jobs analytics portfolio powered by curated `LinkedInWebScraper` data.

Public site: <https://ricardogr07.github.io/mx-jobs-insights/>

## What This Repo Does

This repo turns upstream LinkedIn job snapshots into four durable surfaces:

- curated DuckDB and Parquet datasets
- weekly and monthly bilingual report artifacts
- a public MkDocs site with archives and downloads
- local, GitHub Actions, and cloud execution paths around the same `pipeline` entrypoint

## Runtime Surfaces

- `curate`: validate the upstream workspace, normalize canonical records, and write curated storage
- `report`: build closed-period metrics, render bilingual reports, and export the public CSV
- `site`: generate the public MkDocs source from completed report artifacts
- `pipeline`: orchestrate `curate`, `report`, `site`, docs validation, and optional cloud delivery

## Workflows

- `.github/workflows/ci.yml`: quality gate for Ruff, pytest, strict MkDocs, and package build validation
- `.github/workflows/publish-portfolio-site.yml`: publish the public site from a workflow-built Pages artifact
- `.github/workflows/release-cloud-run-job.yml`: build and publish the container image and optionally update the Cloud Run Job definition

## Local Development

Install the local development toolchain:

```powershell
python -m pip install -e ".[dev]"
```

Install optional cloud clients when validating GCS or BigQuery delivery locally:

```powershell
python -m pip install -e ".[dev,cloud]"
```

Load repo-local report and publication settings before non-dry-run `report` or `pipeline` commands:

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

For offline local pipeline and report validation, set `MX_JOBS_OPENAI_BASE_URL=mock://responses` in the current shell before the command.

## Repo Layout

- `src/mexico_linkedin_jobs_portfolio/`: production code
- `tests/`: unit, integration, and workflow contract coverage
- `docs/`: public MkDocs source only
- `internal/`: operator guides, policies, roadmap history, and Codex guidance
- `configs/`: local environment helpers and config scaffolding
- `scripts/`: reproducibility helpers such as fixture regeneration
- `artifacts/`: local generated outputs for curated data, reports, site builds, and diagnostics

## Internal References

- Current roadmap: [PLAN.md](PLAN.md)
- Internal operator and Codex docs: [internal/](internal/)
