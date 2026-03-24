# mx-jobs-insights

Bilingual Mexico LinkedIn jobs analytics portfolio powered by curated `LinkedInWebScraper` data.

Public site: <https://ricardogr07.github.io/mx-jobs-insights/>

## Current Status

This repo now has the backend MVP, public-site generation, and GitHub-native automation in place.

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

## Local Development

Install the repo in editable mode with dev tools:

```powershell
python -m pip install -e ".[dev]"
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

## Repo Layout

- `src/mexico_linkedin_jobs_portfolio/`: production code
- `tests/`: unit, integration, and workflow contract coverage
- `docs/`: public MkDocs source plus development notes
- `configs/`: local environment helpers and config scaffolding
- `scripts/`: reproducibility helpers such as fixture regeneration
- `artifacts/`: local generated outputs for curated data, reports, site builds, and diagnostics

