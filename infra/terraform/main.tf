locals {
  artifact_registry_repository = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.pipeline.repository_id}"
  cloud_run_image_uri         = "${local.artifact_registry_repository}/${var.cloud_run_job_name}:latest"
  cloud_run_job_run_uri       = "https://run.googleapis.com/v2/projects/${var.project_id}/locations/${var.region}/jobs/${google_cloud_run_v2_job.pipeline.name}:run"
  cloud_run_weekly_args       = concat([
    "--cadence",
    "weekly",
    "--source",
    "auto",
    "--upstream-root",
    var.cloud_run_upstream_root,
    "--curated-root",
    var.cloud_run_curated_root,
    "--report-root",
    var.cloud_run_report_root,
    "--docs-root",
    var.cloud_run_docs_root,
    "--locale",
    var.cloud_run_default_locale,
  ], var.cloud_run_as_of_date == "" ? [] : ["--as-of", var.cloud_run_as_of_date])
  cloud_run_monthly_args      = concat([
    "--cadence",
    "monthly",
    "--source",
    "auto",
    "--upstream-root",
    var.cloud_run_upstream_root,
    "--curated-root",
    var.cloud_run_curated_root,
    "--report-root",
    var.cloud_run_report_root,
    "--docs-root",
    var.cloud_run_docs_root,
    "--locale",
    var.cloud_run_default_locale,
  ], var.cloud_run_as_of_date == "" ? [] : ["--as-of", var.cloud_run_as_of_date])
  cloud_run_weekly_scheduler_body = base64encode(jsonencode({
    overrides = {
      containerOverrides = [
        {
          args = local.cloud_run_weekly_args
        }
      ]
    }
  }))
  cloud_run_monthly_scheduler_body = base64encode(jsonencode({
    overrides = {
      containerOverrides = [
        {
          args = local.cloud_run_monthly_args
        }
      ]
    }
  }))
}

resource "google_project_service" "enabled" {
  for_each = toset([
    "artifactregistry.googleapis.com",
    "bigquery.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "cloudscheduler.googleapis.com",
    "iam.googleapis.com",
    "iamcredentials.googleapis.com",
    "run.googleapis.com",
    "secretmanager.googleapis.com",
    "storage.googleapis.com",
  ])

  project = var.project_id
  service = each.key
}

resource "google_artifact_registry_repository" "pipeline" {
  project       = var.project_id
  location      = var.region
  repository_id = var.artifact_registry_repository_id
  description   = "Pipeline container images for mx-jobs-insights."
  format        = "DOCKER"

  depends_on = [google_project_service.enabled]
}

resource "google_storage_bucket" "mirrors" {
  name                        = var.gcs_bucket_name
  location                    = var.region
  project                     = var.project_id
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  force_destroy               = false

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type = "Delete"
    }
  }

  depends_on = [google_project_service.enabled]
}

resource "google_bigquery_dataset" "private" {
  project                    = var.project_id
  dataset_id                 = var.bigquery_private_dataset_id
  friendly_name              = "MX Jobs Private"
  description                = "Private curated and operational tables for mx-jobs-insights."
  location                   = var.region
  delete_contents_on_destroy = false
}

resource "google_bigquery_dataset" "public" {
  project                    = var.project_id
  dataset_id                 = var.bigquery_public_dataset_id
  friendly_name              = "MX Jobs Public"
  description                = "Public-safe analytical tables for mx-jobs-insights."
  location                   = var.region
  delete_contents_on_destroy = false
}

resource "google_service_account" "release" {
  project      = var.project_id
  account_id   = var.cloud_run_release_service_account_id
  display_name = "mx-jobs-insights release service account"
}

resource "google_service_account" "runtime" {
  project      = var.project_id
  account_id   = var.cloud_run_runtime_service_account_id
  display_name = "mx-jobs-insights Cloud Run Job runtime service account"
}

resource "google_service_account" "scheduler" {
  project      = var.project_id
  account_id   = var.cloud_scheduler_service_account_id
  display_name = "mx-jobs-insights Cloud Scheduler service account"
}

resource "google_iam_workload_identity_pool" "github" {
  provider                  = google
  workload_identity_pool_id  = var.workload_identity_pool_id
  display_name              = "GitHub Actions"
  description               = "Federated identity pool for mx-jobs-insights GitHub releases."
}

resource "google_iam_workload_identity_pool_provider" "github" {
  provider                           = google
  workload_identity_pool_id          = google_iam_workload_identity_pool.github.workload_identity_pool_id
  workload_identity_pool_provider_id = var.workload_identity_provider_id
  display_name                       = "GitHub Actions OIDC"
  description                        = "OIDC provider for GitHub Actions release workflows."

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }

  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.actor"      = "assertion.actor"
    "attribute.repository" = "assertion.repository"
    "attribute.ref"        = "assertion.ref"
    "attribute.workflow"   = "assertion.workflow"
  }

  attribute_condition = "assertion.repository == \"${var.github_repository}\""
}

resource "google_service_account_iam_binding" "release_wif" {
  service_account_id = google_service_account.release.name
  role               = "roles/iam.workloadIdentityUser"
  members = [
    "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github.name}/attribute.repository/${var.github_repository}",
  ]
}

resource "google_project_iam_member" "release_artifact_registry_writer" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${google_service_account.release.email}"
}

resource "google_artifact_registry_repository_iam_member" "release_artifact_registry_reader" {
  project    = var.project_id
  location   = var.region
  repository = google_artifact_registry_repository.pipeline.repository_id
  role       = "roles/artifactregistry.reader"
  member     = "serviceAccount:${google_service_account.release.email}"
}

resource "google_project_iam_member" "release_cloud_run_admin" {
  project = var.project_id
  role    = "roles/run.admin"
  member  = "serviceAccount:${google_service_account.release.email}"
}

resource "google_project_iam_member" "release_cloud_scheduler_admin" {
  project = var.project_id
  role    = "roles/cloudscheduler.admin"
  member  = "serviceAccount:${google_service_account.release.email}"
}

resource "google_service_account_iam_member" "release_can_act_as_runtime" {
  service_account_id = google_service_account.runtime.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.release.email}"
}

resource "google_service_account_iam_member" "release_can_act_as_scheduler" {
  service_account_id = google_service_account.scheduler.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.release.email}"
}

resource "google_project_iam_member" "runtime_bigquery_job_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.runtime.email}"
}

resource "google_bigquery_dataset_iam_member" "runtime_private_dataset_editor" {
  project    = var.project_id
  dataset_id = google_bigquery_dataset.private.dataset_id
  role       = "roles/bigquery.dataEditor"
  member     = "serviceAccount:${google_service_account.runtime.email}"
}

resource "google_bigquery_dataset_iam_member" "runtime_public_dataset_editor" {
  project    = var.project_id
  dataset_id = google_bigquery_dataset.public.dataset_id
  role       = "roles/bigquery.dataEditor"
  member     = "serviceAccount:${google_service_account.runtime.email}"
}

resource "google_storage_bucket_iam_member" "runtime_bucket_object_admin" {
  bucket = google_storage_bucket.mirrors.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.runtime.email}"
}

resource "google_cloud_run_v2_job_iam_member" "scheduler_job_invoker" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_job.pipeline.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.scheduler.email}"
}

resource "google_secret_manager_secret" "openai_api_key" {
  project   = var.project_id
  secret_id = var.openai_api_key_secret_id

  replication {
    auto {}
  }

  depends_on = [google_project_service.enabled]
}

resource "google_secret_manager_secret" "public_key_salt" {
  project   = var.project_id
  secret_id = var.public_key_salt_secret_id

  replication {
    auto {}
  }

  depends_on = [google_project_service.enabled]
}

resource "google_secret_manager_secret_iam_member" "runtime_openai_accessor" {
  secret_id = google_secret_manager_secret.openai_api_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.runtime.email}"
}

resource "google_secret_manager_secret_iam_member" "runtime_public_key_salt_accessor" {
  secret_id = google_secret_manager_secret.public_key_salt.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.runtime.email}"
}

resource "google_cloud_run_v2_job" "pipeline" {
  project  = var.project_id
  name     = var.cloud_run_job_name
  location = var.region

  template {
    template {
      service_account = google_service_account.runtime.email
      timeout         = "86400s"
      max_retries     = 0

      containers {
        image = local.cloud_run_image_uri

        command = [
          "python",
          "-m",
          "mexico_linkedin_jobs_portfolio.interfaces.cli.main",
          "pipeline",
        ]

        args = concat([
          "--cadence",
          var.cloud_run_default_cadence,
          "--source",
          "auto",
          "--upstream-root",
          var.cloud_run_upstream_root,
          "--curated-root",
          var.cloud_run_curated_root,
          "--report-root",
          var.cloud_run_report_root,
          "--docs-root",
          var.cloud_run_docs_root,
          "--locale",
          var.cloud_run_default_locale,
        ], var.cloud_run_as_of_date == "" ? [] : ["--as-of", var.cloud_run_as_of_date])

        env {
          name  = "GOOGLE_CLOUD_PROJECT"
          value = var.project_id
        }

        env {
          name  = "MX_JOBS_GCP_REGION"
          value = var.region
        }

        env {
          name  = "MX_JOBS_GCS_BUCKET"
          value = var.gcs_bucket_name
        }

        env {
          name  = "MX_JOBS_BIGQUERY_PRIVATE_DATASET"
          value = google_bigquery_dataset.private.dataset_id
        }

        env {
          name  = "MX_JOBS_BIGQUERY_PUBLIC_DATASET"
          value = google_bigquery_dataset.public.dataset_id
        }

        env {
          name  = "MX_JOBS_GCS_PREFIX"
          value = var.mx_jobs_gcs_prefix
        }

        env {
          name  = "MX_JOBS_OPENAI_MODEL"
          value = var.mx_jobs_openai_model
        }

        env {
          name  = "MX_JOBS_OPENAI_BASE_URL"
          value = var.mx_jobs_openai_base_url
        }

        env {
          name  = "MX_JOBS_UPSTREAM_REPO_URL"
          value = var.cloud_run_upstream_repo_url
        }

        env {
          name  = "MX_JOBS_UPSTREAM_REF"
          value = var.cloud_run_upstream_ref
        }

        env {
          name  = "CLOUD_RUN_DEFAULT_CADENCE"
          value = var.cloud_run_default_cadence
        }

        env {
          name  = "CLOUD_RUN_DEFAULT_LOCALE"
          value = var.cloud_run_default_locale
        }

        env {
          name  = "CLOUD_RUN_UPSTREAM_ROOT"
          value = var.cloud_run_upstream_root
        }

        env {
          name  = "CLOUD_RUN_CURATED_ROOT"
          value = var.cloud_run_curated_root
        }

        env {
          name  = "CLOUD_RUN_REPORT_ROOT"
          value = var.cloud_run_report_root
        }

        env {
          name  = "CLOUD_RUN_DOCS_ROOT"
          value = var.cloud_run_docs_root
        }

        dynamic "env" {
          for_each = var.cloud_run_as_of_date == "" ? [] : [var.cloud_run_as_of_date]
          content {
            name  = "CLOUD_RUN_AS_OF_DATE"
            value = env.value
          }
        }

        env {
          name = "OPENAI_API_KEY"

          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.openai_api_key.secret_id
              version = "latest"
            }
          }
        }

        env {
          name = "MX_JOBS_PUBLIC_KEY_SALT"

          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.public_key_salt.secret_id
              version = "latest"
            }
          }
        }
      }
    }
  }
}

resource "google_cloud_scheduler_job" "weekly" {
  project     = var.project_id
  name        = "${var.cloud_run_job_name}-weekly"
  description = "Paused weekly trigger for mx-jobs-insights Cloud Run Job execution."
  region      = var.region
  schedule    = "0 14 * * 1"
  time_zone   = "UTC"
  paused      = true

  http_target {
    http_method = "POST"
    uri         = local.cloud_run_job_run_uri
    body        = local.cloud_run_weekly_scheduler_body

    oauth_token {
      service_account_email = google_service_account.scheduler.email
      scope                 = "https://www.googleapis.com/auth/cloud-platform"
    }

    headers = {
      "Content-Type" = "application/json"
    }
  }
}

resource "google_cloud_scheduler_job" "monthly" {
  project     = var.project_id
  name        = "${var.cloud_run_job_name}-monthly"
  description = "Paused monthly trigger for mx-jobs-insights Cloud Run Job execution."
  region      = var.region
  schedule    = "0 15 1 * *"
  time_zone   = "UTC"
  paused      = true

  http_target {
    http_method = "POST"
    uri         = local.cloud_run_job_run_uri
    body        = local.cloud_run_monthly_scheduler_body

    oauth_token {
      service_account_email = google_service_account.scheduler.email
      scope                 = "https://www.googleapis.com/auth/cloud-platform"
    }

    headers = {
      "Content-Type" = "application/json"
    }
  }
}
