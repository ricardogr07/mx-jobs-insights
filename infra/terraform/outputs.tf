output "artifact_registry_repository" {
  value       = google_artifact_registry_repository.pipeline.name
  description = "Artifact Registry repository name."
}

output "artifact_registry_repository_uri" {
  value       = local.artifact_registry_repository
  description = "Docker image registry URI for the pipeline container."
}

output "gcs_bucket_name" {
  value       = google_storage_bucket.mirrors.name
  description = "Bucket used for curated, report, site, and diagnostic mirrors."
}

output "bigquery_private_dataset" {
  value       = google_bigquery_dataset.private.dataset_id
  description = "Private dataset id."
}

output "bigquery_public_dataset" {
  value       = google_bigquery_dataset.public.dataset_id
  description = "Public dataset id."
}

output "cloud_run_job_name" {
  value       = google_cloud_run_v2_job.pipeline.name
  description = "Cloud Run Job name."
}

output "release_service_account_email" {
  value       = google_service_account.release.email
  description = "GitHub Actions release service account email."
}

output "runtime_service_account_email" {
  value       = google_service_account.runtime.email
  description = "Cloud Run runtime service account email."
}

output "workload_identity_provider" {
  value       = google_iam_workload_identity_pool_provider.github.name
  description = "Workload Identity Provider resource name for GitHub Actions."
}
