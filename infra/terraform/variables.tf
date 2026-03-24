variable "project_id" {
  type        = string
  description = "Google Cloud project that owns the Phase 5 resources."
}

variable "region" {
  type        = string
  description = "Primary Google Cloud region for the Phase 5 footprint."
  default     = "us-central1"
}

variable "github_repository" {
  type        = string
  description = "GitHub repository allowed to impersonate the release service account through WIF."
  default     = "ricardogr07/mx-jobs-insights"
}

variable "artifact_registry_repository_id" {
  type        = string
  description = "Artifact Registry repository id for pipeline container images."
  default     = "mx-jobs-insights-pipeline"
}

variable "gcs_bucket_name" {
  type        = string
  description = "Bucket that mirrors curated, report, site, and diagnostic artifacts."
}

variable "bigquery_private_dataset_id" {
  type        = string
  description = "Dataset for private curated and operational tables."
  default     = "mx_jobs_private"
}

variable "bigquery_public_dataset_id" {
  type        = string
  description = "Dataset for public-safe analytical tables."
  default     = "mx_jobs_public"
}

variable "cloud_run_job_name" {
  type        = string
  description = "Cloud Run Job name used to execute the pipeline container."
  default     = "mx-jobs-insights-pipeline"
}

variable "cloud_run_runtime_service_account_id" {
  type        = string
  description = "Service account used by the Cloud Run Job at execution time."
  default     = "mx-jobs-insights-runtime"
}

variable "cloud_run_release_service_account_id" {
  type        = string
  description = "Service account impersonated by GitHub Actions for release operations."
  default     = "mx-jobs-insights-release"
}

variable "cloud_scheduler_service_account_id" {
  type        = string
  description = "Service account used by Cloud Scheduler to trigger job executions."
  default     = "mx-jobs-insights-scheduler"
}

variable "workload_identity_pool_id" {
  type        = string
  description = "Workload Identity Pool id for GitHub Actions."
  default     = "github-actions"
}

variable "workload_identity_provider_id" {
  type        = string
  description = "Workload Identity Provider id for GitHub Actions."
  default     = "github-actions-oidc"
}

variable "openai_api_key_secret_id" {
  type        = string
  description = "Secret Manager secret id for OPENAI_API_KEY."
  default     = "openai-api-key"
}

variable "public_key_salt_secret_id" {
  type        = string
  description = "Secret Manager secret id for MX_JOBS_PUBLIC_KEY_SALT."
  default     = "mx-jobs-public-key-salt"
}

variable "cloud_run_default_cadence" {
  type        = string
  description = "Default cadence passed to the Cloud Run Job when it executes."
  default     = "monthly"
}

variable "cloud_run_default_locale" {
  type        = string
  description = "Default locale passed to the Cloud Run Job when it executes."
  default     = "all"
}

variable "cloud_run_upstream_root" {
  type        = string
  description = "Upstream workspace path made available to the Cloud Run Job."
  default     = "/workspace/LinkedInWebScraper"
}

variable "cloud_run_upstream_repo_url" {
  type        = string
  description = "Git repository cloned into the ephemeral upstream workspace when the Cloud Run Job starts."
  default     = "https://github.com/ricardogr07/LinkedInWebScraper.git"
}

variable "cloud_run_upstream_ref" {
  type        = string
  description = "Git ref cloned into the ephemeral upstream workspace when the Cloud Run Job starts."
  default     = "data"
}

variable "cloud_run_curated_root" {
  type        = string
  description = "Curated output root used by the Cloud Run Job."
  default     = "/workspace/artifacts/curated"
}

variable "cloud_run_report_root" {
  type        = string
  description = "Report output root used by the Cloud Run Job."
  default     = "/workspace/artifacts/reports"
}

variable "cloud_run_docs_root" {
  type        = string
  description = "Docs output root used by the Cloud Run Job."
  default     = "/workspace/docs"
}

variable "cloud_run_as_of_date" {
  type        = string
  description = "Optional reference date passed to the Cloud Run Job."
  default     = ""
}

variable "mx_jobs_gcs_prefix" {
  type        = string
  description = "Object prefix used for mirrored cloud artifacts."
  default     = "cloud"
}

variable "mx_jobs_openai_model" {
  type        = string
  description = "OpenAI model name used by the containerized reporting pipeline."
  default     = "gpt-5.4-nano"
}

variable "mx_jobs_openai_base_url" {
  type        = string
  description = "OpenAI base URL used by the containerized reporting pipeline."
  default     = "https://api.openai.com/v1"
}
