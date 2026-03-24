# Tools and Commands

This page lists the live operational commands for the repo.

## Bootstrap and Validation

### `bootstrap`
- Command: `python -m pip install -e .[dev]`
- Purpose: install the local development toolchain for lint, docs, test, and build work.
- Status: `ready`

### `bootstrap_cloud`
- Command: `python -m pip install -e .[dev,cloud]`
- Purpose: install the local development toolchain plus optional Google Cloud clients.
- Status: `ready`

### `status`
- Command: `git status --short`
- Purpose: inspect the worktree before and after a reviewed step.
- Status: `ready`

### `diff`
- Command: `git diff --stat`
- Purpose: summarize file-level changes for review.
- Status: `ready`

### `test`
- Command: `python -m pytest -q`
- Purpose: run the default offline test suite.
- Status: `ready`

### `preflight`
- Command: `python -m tox -e preflight`
- Purpose: run the local quality gate.
- Status: `ready`

### `docs`
- Command: `python -m mkdocs build --strict`
- Purpose: build the public documentation site.
- Status: `ready`

### `build`
- Command: `python -m build --no-isolation`
- Purpose: build the package from the current working tree.
- Status: `ready`

### `GitHub Actions CI workflow`
- Command: `.github/workflows/ci.yml`
- Purpose: run Ruff, pytest, strict MkDocs, and package build validation on GitHub.
- Status: `ready`

## Ingestion and Curation

### `workspace_validate`
- Command: `python -m mexico_linkedin_jobs_portfolio.interfaces.cli.main ingest --source auto --dry-run --upstream-root ../LinkedInWebScraper`
- Purpose: validate the sibling upstream workspace shape and source resolution contract.
- Status: `ready`

### `ingest_dry_run_sqlite`
- Command: `python -m mexico_linkedin_jobs_portfolio.interfaces.cli.main ingest --source sqlite --dry-run`
- Purpose: validate the SQLite ingestion path and summary output without writing curated artifacts.
- Status: `ready`

### `ingest_dry_run_csv`
- Command: `python -m mexico_linkedin_jobs_portfolio.interfaces.cli.main ingest --source csv --dry-run`
- Purpose: validate the CSV ingestion path and summary output without writing curated artifacts.
- Status: `ready`

### `curate_dry_run_auto`
- Command: `python -m mexico_linkedin_jobs_portfolio.interfaces.cli.main curate --source auto --dry-run`
- Purpose: validate source resolution, canonical batching, and curation summaries without writing outputs.
- Status: `ready`

### `curate_write_auto`
- Command: `python -m mexico_linkedin_jobs_portfolio.interfaces.cli.main curate --source auto`
- Purpose: write curated DuckDB state and Parquet sidecars.
- Status: `ready`

### `fixtures_regen`
- Command: `python scripts/make_sample_data.py`
- Purpose: regenerate the checked-in test workspace fixture under `tests/data/upstream_workspace`.
- Status: `ready`

## Reporting

### `report_dry_run_weekly`
- Command: `python -m mexico_linkedin_jobs_portfolio.interfaces.cli.main report --cadence weekly --as-of 2026-03-23 --curated-root artifacts/curated --output-root artifacts/reports --dry-run`
- Purpose: validate closed-week period resolution and metrics without writing artifacts.
- Status: `ready`

### `report_write_monthly`
- Command: `python -m mexico_linkedin_jobs_portfolio.interfaces.cli.main report --cadence monthly --as-of 2026-04-01 --curated-root artifacts/curated --output-root artifacts/reports`
- Purpose: write the monthly report bundle, public CSV, and narration when runtime env is configured.
- Status: `ready`

### `report runtime`
- Required for non-dry-run: `OPENAI_API_KEY`, `MX_JOBS_OPENAI_MODEL`, `MX_JOBS_PUBLIC_KEY_SALT`
- Optional override: `MX_JOBS_OPENAI_BASE_URL`
- Offline override: `MX_JOBS_OPENAI_BASE_URL=mock://responses`

## Public Site and Dashboard

### `site_dry_run`
- Command: `python -m mexico_linkedin_jobs_portfolio.interfaces.cli.main site --dry-run`
- Purpose: resolve the public site index from completed report artifacts without writing pages.
- Status: `ready`

### `site_write`
- Command: `python -m mexico_linkedin_jobs_portfolio.interfaces.cli.main site`
- Purpose: generate the public MkDocs source pages and copy public-safe report assets into the docs tree.
- Status: `ready`

### `streamlit_run_local`
- Command: `streamlit run src/mexico_linkedin_jobs_portfolio/interfaces/streamlit/app.py`
- Windows fallback: `python -m streamlit run src/mexico_linkedin_jobs_portfolio/interfaces/streamlit/app.py`
- Purpose: launch the local-first Streamlit dashboard over curated and report artifacts.
- Status: `ready`

## Automation

### `pipeline_dry_run`
- Command: `python -m mexico_linkedin_jobs_portfolio.interfaces.cli.main pipeline --cadence weekly --dry-run --upstream-root tests/data/upstream_workspace`
- Purpose: validate the full orchestration contract over fixture-backed upstream data without writing durable outputs.
- Status: `ready`

### `pipeline_write_weekly`
- Command: `python -m mexico_linkedin_jobs_portfolio.interfaces.cli.main pipeline --cadence weekly --as-of 2026-03-30 --upstream-root tests/data/upstream_workspace`
- Purpose: run the weekly orchestration path over fixture-backed upstream data.
- Status: `ready`

### `pipeline_write_monthly`
- Command: `python -m mexico_linkedin_jobs_portfolio.interfaces.cli.main pipeline --cadence monthly --as-of 2026-04-01 --upstream-root tests/data/upstream_workspace`
- Purpose: run the monthly orchestration path over fixture-backed upstream data.
- Status: `ready`

### `GitHub Pages publish workflow`
- Command: `.github/workflows/publish-portfolio-site.yml`
- Purpose: run the GitHub-native publish path that builds the site and deploys Pages from an artifact.
- Status: `ready`

## Cloud Delivery

### `container_build_pipeline`
- Command: `docker build -t mx-jobs-insights-pipeline .`
- Purpose: build the deployment-neutral container image around the existing `pipeline` CLI.
- Status: `ready`

### `terraform_fmt_check`
- Command: `terraform -chdir=infra/terraform fmt -check`
- Purpose: verify Terraform formatting.
- Status: `ready`

### `terraform_validate`
- Command: `terraform -chdir=infra/terraform validate`
- Purpose: validate the Terraform configuration.
- Status: `ready`

### `gcloud_run_jobs_execute`
- Command: `gcloud run jobs execute mx-jobs-insights-pipeline --region <region>`
- Purpose: execute the containerized pipeline from Cloud Run Jobs.
- Status: `ready`

### `Cloud Run release workflow`
- Command: `.github/workflows/release-cloud-run-job.yml`
- Purpose: build and push the container image, optionally validate Terraform, and update the Cloud Run Job definition.
- Status: `ready`

### `cloud runtime`
- Required: `GOOGLE_CLOUD_PROJECT`, `MX_JOBS_GCP_REGION`, `MX_JOBS_GCS_BUCKET`, `MX_JOBS_BIGQUERY_PRIVATE_DATASET`, `MX_JOBS_BIGQUERY_PUBLIC_DATASET`
- Optional: `MX_JOBS_GCS_PREFIX`, `MX_JOBS_UPSTREAM_REPO_URL`, `MX_JOBS_UPSTREAM_REF`
- Auth: local ADC for developer validation or workload identity/service-account bindings in cloud
