"""Configuration models for Phase 5 cloud delivery and release contracts."""

from __future__ import annotations

from dataclasses import dataclass

GOOGLE_CLOUD_PROJECT_ENV = "GOOGLE_CLOUD_PROJECT"
GCP_REGION_ENV = "MX_JOBS_GCP_REGION"
GCS_BUCKET_ENV = "MX_JOBS_GCS_BUCKET"
GCS_PREFIX_ENV = "MX_JOBS_GCS_PREFIX"
BIGQUERY_PRIVATE_DATASET_ENV = "MX_JOBS_BIGQUERY_PRIVATE_DATASET"
BIGQUERY_PUBLIC_DATASET_ENV = "MX_JOBS_BIGQUERY_PUBLIC_DATASET"


@dataclass(frozen=True, slots=True)
class CloudEnvironmentConfig:
    """Describe the optional Phase 5 cloud runtime derived from environment variables."""

    project_id: str | None = None
    region: str | None = None
    gcs_bucket: str | None = None
    gcs_prefix: str | None = None
    bigquery_private_dataset: str | None = None
    bigquery_public_dataset: str | None = None

    @property
    def cloud_requested(self) -> bool:
        """Return whether any Phase 5 cloud runtime values are present."""

        return any(
            value
            for value in (
                self.project_id,
                self.region,
                self.gcs_bucket,
                self.gcs_prefix,
                self.bigquery_private_dataset,
                self.bigquery_public_dataset,
            )
        )

    @property
    def is_configured(self) -> bool:
        """Return whether the full Phase 5 cloud runtime is available."""

        return not self.missing_runtime_env()

    def missing_runtime_env(self) -> tuple[str, ...]:
        """Return missing cloud runtime environment names."""

        missing: list[str] = []
        if not self.project_id:
            missing.append(GOOGLE_CLOUD_PROJECT_ENV)
        if not self.region:
            missing.append(GCP_REGION_ENV)
        if not self.gcs_bucket:
            missing.append(GCS_BUCKET_ENV)
        if not self.bigquery_private_dataset:
            missing.append(BIGQUERY_PRIVATE_DATASET_ENV)
        if not self.bigquery_public_dataset:
            missing.append(BIGQUERY_PUBLIC_DATASET_ENV)
        return tuple(missing)

    @property
    def normalized_gcs_prefix(self) -> str:
        """Return the normalized optional GCS object prefix without surrounding slashes."""

        if not self.gcs_prefix:
            return ""
        return self.gcs_prefix.strip().strip("/")

    @property
    def bucket_uri(self) -> str | None:
        """Return the bucket URI prefix for display and summaries."""

        if not self.gcs_bucket:
            return None
        if not self.normalized_gcs_prefix:
            return f"gs://{self.gcs_bucket}"
        return f"gs://{self.gcs_bucket}/{self.normalized_gcs_prefix}"

    def to_display_dict(self) -> dict[str, object]:
        """Serialize the cloud runtime contract for CLI and workflow output."""

        return {
            "cloud_requested": self.cloud_requested,
            "is_configured": self.is_configured if self.cloud_requested else False,
            "project_id": self.project_id,
            "region": self.region,
            "gcs_bucket": self.gcs_bucket,
            "gcs_prefix": self.normalized_gcs_prefix or None,
            "bucket_uri": self.bucket_uri,
            "bigquery_private_dataset": self.bigquery_private_dataset,
            "bigquery_public_dataset": self.bigquery_public_dataset,
            "required_env_names": [
                GOOGLE_CLOUD_PROJECT_ENV,
                GCP_REGION_ENV,
                GCS_BUCKET_ENV,
                BIGQUERY_PRIVATE_DATASET_ENV,
                BIGQUERY_PUBLIC_DATASET_ENV,
            ],
            "optional_env_names": [GCS_PREFIX_ENV],
            "missing_runtime_env": list(self.missing_runtime_env()) if self.cloud_requested else [],
        }
