# Phase 5 Cloud Usage

This page documents the current Phase 5 cloud delivery contract around the existing `pipeline` CLI.

## Current Scope

Phase 5 currently supports:

- one deployment-neutral container image built around the existing `pipeline` CLI
- cloud artifact mirroring for curated, report, site, and diagnostics outputs
- BigQuery as a downstream mirror with explicit private and public dataset boundaries
- Terraform-managed GCP infrastructure for Cloud Run Jobs, Cloud Storage, BigQuery, IAM, and Cloud Scheduler
- cloud validation that reuses the existing local pipeline contract rather than introducing a second orchestration path

GitHub Pages remains the active public site. Cloud outputs mirror the current pipeline artifacts and are used for release validation, retention, and future hosting cutover work.

## Runtime Inputs

The Phase 5 cloud contract expects these environment variables:

- `GOOGLE_CLOUD_PROJECT`
- `MX_JOBS_GCP_REGION`
- `MX_JOBS_GCS_BUCKET`
- `MX_JOBS_BIGQUERY_PRIVATE_DATASET`
- `MX_JOBS_BIGQUERY_PUBLIC_DATASET`
- optional `MX_JOBS_GCS_PREFIX`
- optional `MX_JOBS_UPSTREAM_REPO_URL`
- optional `MX_JOBS_UPSTREAM_REF`

The existing report runtime variables still apply inside the containerized pipeline when a report or published automation run is executed:

- `OPENAI_API_KEY`
- `MX_JOBS_OPENAI_MODEL`
- `MX_JOBS_PUBLIC_KEY_SALT`
- optional `MX_JOBS_OPENAI_BASE_URL`

Developer validation should use local Application Default Credentials. Cloud execution should use workload identity or service-account bindings, not committed keys.

## Local Validation Commands

Container build:

```powershell
python -m pip install -e ".[dev,cloud]"
docker build -t mx-jobs-insights-pipeline .
```

The container runtime installs the cloud and docs extras and can clone the upstream `data` branch into its ephemeral workspace before calling `pipeline`. The default upstream source remains `https://github.com/ricardogr07/LinkedInWebScraper.git` at ref `data`, but both values can be overridden through `MX_JOBS_UPSTREAM_REPO_URL` and `MX_JOBS_UPSTREAM_REF`.

Terraform format and validation:

```powershell
terraform -chdir=infra/terraform fmt -check
terraform -chdir=infra/terraform validate
```

Cloud Run job smoke execution, when the current shell is authenticated against GCP:

```powershell
gcloud run jobs execute mx-jobs-insights-pipeline --region <region>
```

The deployed Cloud Run Job keeps one image and one `pipeline` entrypoint. Weekly and monthly Cloud Scheduler jobs call the same job with cadence-specific argument overrides instead of introducing separate compute paths.

## Terraform Flow

Phase 5 Terraform should be validated in this order:

1. `terraform -chdir=infra/terraform fmt -check`
2. `terraform -chdir=infra/terraform validate`
3. `terraform -chdir=infra/terraform plan`
4. `terraform -chdir=infra/terraform apply` only after review and approval

The minimum infrastructure footprint covered by the plan is:

- Artifact Registry for container images
- Cloud Storage buckets for curated, report, site, and diagnostics mirrors
- BigQuery datasets for private and public mirrored data
- Cloud Run Job for the containerized pipeline
- Cloud Scheduler triggers for weekly and monthly runs
- IAM and service-account bindings for delivery

## Cloud Release Contract

The containerized `pipeline` remains the single orchestration entrypoint.

The cloud release path should:

- build and publish the container image
- deploy or update the Cloud Run Job definition
- wire weekly and monthly Cloud Scheduler triggers
- keep GitHub Pages publication intact until an explicit hosting cutover is approved

The manual GitHub workflow for this path is `.github/workflows/cloud-release.yml`. It expects repo variables for GCP coordinates, repo secrets for `OPENAI_API_KEY` and `MX_JOBS_PUBLIC_KEY_SALT`, and optional repo variables for `MX_JOBS_UPSTREAM_REPO_URL` plus `MX_JOBS_UPSTREAM_REF` when the defaults should be overridden.

## Public And Private Boundary

Allowed cloud outputs:

- curated, report, site, and diagnostics mirrors in GCS
- private BigQuery tables for curated internal data and pipeline summaries
- public BigQuery tables for de-identified rows and aggregate metrics

Forbidden cloud outputs:

- raw OpenAI prompt or response payloads
- raw private drill-down fields beyond the existing public data policy
- committed cloud credentials or service-account keys
- any GCS or BigQuery export that violates the current public data policy
