# Cloud Deployment

This guide documents the current cloud delivery contract around the existing `pipeline` CLI.

## Scope

The repo currently supports:

- one deployment-neutral container image built around the existing `pipeline` CLI
- cloud artifact mirroring for curated, report, site, and diagnostics outputs
- BigQuery as a downstream mirror with explicit private and public dataset boundaries
- Terraform-managed GCP infrastructure for Cloud Run Jobs, Cloud Storage, BigQuery, IAM, and Cloud Scheduler
- cloud validation that reuses the existing pipeline contract rather than introducing a second orchestration path

GitHub Pages remains the active public site. Cloud outputs mirror the current pipeline artifacts for release validation, retention, and future hosting cutover work.

## Runtime Inputs

Required cloud runtime variables:
- `GOOGLE_CLOUD_PROJECT`
- `MX_JOBS_GCP_REGION`
- `MX_JOBS_GCS_BUCKET`
- `MX_JOBS_BIGQUERY_PRIVATE_DATASET`
- `MX_JOBS_BIGQUERY_PUBLIC_DATASET`

Optional:
- `MX_JOBS_GCS_PREFIX`
- `MX_JOBS_UPSTREAM_REPO_URL`
- `MX_JOBS_UPSTREAM_REF`

The existing report runtime variables still apply inside the containerized pipeline.

## Local Validation

```powershell
python -m pip install -e ".[dev,cloud]"
docker build -t mx-jobs-insights-pipeline .
terraform -chdir=infra/terraform fmt -check
terraform -chdir=infra/terraform validate
gcloud run jobs execute mx-jobs-insights-pipeline --region <region>
```

Developer validation should use local Application Default Credentials. Cloud execution should use workload identity or service-account bindings, not committed keys.

## Release Contract

The release workflow is `.github/workflows/release-cloud-run-job.yml`.

It can:
- build and publish the container image
- optionally validate Terraform
- deploy or update the Cloud Run Job definition
- keep the existing GitHub Pages publication path intact

## Public and Private Boundary

Allowed cloud outputs:
- curated, report, site, and diagnostics mirrors in GCS
- private BigQuery tables for curated internal data and run summaries
- public BigQuery tables for de-identified rows and aggregate metrics

Forbidden cloud outputs:
- raw OpenAI prompt or response payloads
- raw private drill-down fields beyond the existing public data policy
- committed cloud credentials or service-account keys
