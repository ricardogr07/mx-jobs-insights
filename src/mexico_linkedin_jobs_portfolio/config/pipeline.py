"""Configuration models for automation orchestration and optional cloud delivery."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

from mexico_linkedin_jobs_portfolio.config.cloud import (
    BIGQUERY_PRIVATE_DATASET_ENV,
    BIGQUERY_PUBLIC_DATASET_ENV,
    GCP_REGION_ENV,
    GCS_BUCKET_ENV,
    GCS_PREFIX_ENV,
    GOOGLE_CLOUD_PROJECT_ENV,
    CloudEnvironmentConfig,
)
from mexico_linkedin_jobs_portfolio.config.curated import CuratedStorageConfig
from mexico_linkedin_jobs_portfolio.config.reporting import (
    OPENAI_API_KEY_ENV,
    OPENAI_BASE_URL_ENV,
    OPENAI_MODEL_ENV,
    PUBLIC_KEY_SALT_ENV,
    REPORT_CADENCES,
    REPORT_LOCALES,
    ReportCadence,
    ReportConfig,
    ReportLocale,
)
from mexico_linkedin_jobs_portfolio.config.site import SiteConfig
from mexico_linkedin_jobs_portfolio.config.upstream import (
    DEFAULT_UPSTREAM_REPO_URL,
    SOURCE_MODES,
    UPSTREAM_REF_ENV,
    UPSTREAM_REPO_URL_ENV,
    SourceMode,
    UpstreamWorkspaceConfig,
)

PIPELINE_CADENCES: tuple[ReportCadence, ...] = REPORT_CADENCES
PIPELINE_LOCALES: tuple[ReportLocale, ...] = REPORT_LOCALES


@dataclass(frozen=True, slots=True)
class PipelineArtifactConfig:
    """Describe where the pipeline orchestration summary should be written."""

    root: Path = Path("artifacts/pipeline")

    def resolved_root(self) -> Path:
        return self.root.expanduser().resolve(strict=False)

    @property
    def run_summary_path(self) -> Path:
        return self.resolved_root() / "run_summary.json"


@dataclass(frozen=True, slots=True)
class PipelineConfig:
    """Describe one pipeline orchestration request across local, GitHub, and cloud."""

    cadence: ReportCadence
    source_mode: SourceMode = "auto"
    upstream_root: Path = Path("../LinkedInWebScraper")
    curated_root: Path = CuratedStorageConfig().root
    report_root: Path = Path("artifacts/reports")
    docs_root: Path = Path("docs")
    locale: ReportLocale = "all"
    as_of_date: date | None = None
    dry_run: bool = True
    openai_api_key: str | None = None
    openai_model: str | None = None
    public_key_salt: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    upstream_repo_url: str = DEFAULT_UPSTREAM_REPO_URL
    upstream_ref: str | None = None
    google_cloud_project: str | None = None
    gcp_region: str | None = None
    gcs_bucket: str | None = None
    gcs_prefix: str | None = None
    bigquery_private_dataset: str | None = None
    bigquery_public_dataset: str | None = None

    @property
    def workspace(self) -> UpstreamWorkspaceConfig:
        return UpstreamWorkspaceConfig(
            root=self.upstream_root,
            source_mode=self.source_mode,
            preferred_ref=self.upstream_ref or UpstreamWorkspaceConfig().preferred_ref,
        )

    @property
    def curated_storage(self) -> CuratedStorageConfig:
        return CuratedStorageConfig(root=self.curated_root)

    @property
    def report_config(self) -> ReportConfig:
        return ReportConfig(
            cadence=self.cadence,
            locale=self.locale,
            as_of_date=self.as_of_date,
            curated_root=self.curated_root,
            output_root=self.report_root,
            dry_run=self.dry_run,
            openai_api_key=self.openai_api_key,
            openai_model=self.openai_model,
            public_key_salt=self.public_key_salt,
            openai_base_url=self.openai_base_url,
        )

    @property
    def site_config(self) -> SiteConfig:
        return SiteConfig(
            report_root=self.report_root,
            docs_root=self.docs_root,
            locale=self.locale,
            dry_run=self.dry_run,
        )

    @property
    def cloud_environment(self) -> CloudEnvironmentConfig:
        return CloudEnvironmentConfig(
            project_id=self.google_cloud_project,
            region=self.gcp_region,
            gcs_bucket=self.gcs_bucket,
            gcs_prefix=self.gcs_prefix,
            bigquery_private_dataset=self.bigquery_private_dataset,
            bigquery_public_dataset=self.bigquery_public_dataset,
        )

    @property
    def pipeline_artifacts(self) -> PipelineArtifactConfig:
        return PipelineArtifactConfig()

    @property
    def locale_coverage(self) -> tuple[str, ...]:
        if self.locale == "all":
            return ("en", "es")
        return (self.locale,)

    def missing_runtime_env(self) -> tuple[str, ...]:
        missing: list[str] = []
        if not self.openai_api_key:
            missing.append(OPENAI_API_KEY_ENV)
        if not self.openai_model:
            missing.append(OPENAI_MODEL_ENV)
        if not self.public_key_salt:
            missing.append(PUBLIC_KEY_SALT_ENV)
        return tuple(missing)

    def missing_cloud_runtime_env(self) -> tuple[str, ...]:
        if not self.cloud_environment.cloud_requested:
            return ()
        return self.cloud_environment.missing_runtime_env()

    def to_display_dict(self) -> dict[str, object]:
        return {
            "cadence": self.cadence,
            "source_mode": self.source_mode,
            "locale": self.locale,
            "locale_coverage": list(self.locale_coverage),
            "as_of_date": self.as_of_date.isoformat() if self.as_of_date is not None else None,
            "upstream_root": str(self.workspace.resolved_root()),
            "curated_root": str(self.curated_storage.resolved_root()),
            "report_root": str(self.report_config.report_storage.resolved_root()),
            "docs_root": str(self.site_config.docs_root_resolved),
            "dry_run": self.dry_run,
            "openai_base_url": self.openai_base_url,
            "upstream_repo_url": self.upstream_repo_url,
            "upstream_ref": self.workspace.preferred_ref,
            "missing_runtime_env": list(self.missing_runtime_env()) if not self.dry_run else [],
            "missing_cloud_runtime_env": (
                list(self.missing_cloud_runtime_env())
                if self.cloud_environment.cloud_requested and not self.dry_run
                else []
            ),
            "source_choices": list(SOURCE_MODES),
            "cadence_choices": list(PIPELINE_CADENCES),
            "locale_choices": list(PIPELINE_LOCALES),
            "openai_env_names": [
                OPENAI_API_KEY_ENV,
                OPENAI_MODEL_ENV,
                PUBLIC_KEY_SALT_ENV,
                OPENAI_BASE_URL_ENV,
            ],
            "cloud_environment": self.cloud_environment.to_display_dict(),
            "cloud_env_names": [
                GOOGLE_CLOUD_PROJECT_ENV,
                GCP_REGION_ENV,
                GCS_BUCKET_ENV,
                GCS_PREFIX_ENV,
                BIGQUERY_PRIVATE_DATASET_ENV,
                BIGQUERY_PUBLIC_DATASET_ENV,
                UPSTREAM_REPO_URL_ENV,
                UPSTREAM_REF_ENV,
            ],
        }

