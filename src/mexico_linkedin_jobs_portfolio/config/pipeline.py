"""Configuration models for Phase 4 automation orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

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
    SOURCE_MODES,
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
        """Return the normalized pipeline-artifact root."""

        return self.root.expanduser().resolve(strict=False)

    @property
    def run_summary_path(self) -> Path:
        """Return the canonical pipeline run-summary path."""

        return self.resolved_root() / "run_summary.json"


@dataclass(frozen=True, slots=True)
class PipelineConfig:
    """Describe one Phase 4 pipeline orchestration request."""

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

    @property
    def workspace(self) -> UpstreamWorkspaceConfig:
        """Return the upstream workspace config used by the pipeline."""

        return UpstreamWorkspaceConfig(root=self.upstream_root, source_mode=self.source_mode)

    @property
    def curated_storage(self) -> CuratedStorageConfig:
        """Return the curated storage config used by the pipeline."""

        return CuratedStorageConfig(root=self.curated_root)

    @property
    def report_config(self) -> ReportConfig:
        """Return the report-generation request derived from the pipeline config."""

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
        """Return the site-generation request derived from the pipeline config."""

        return SiteConfig(
            report_root=self.report_root,
            docs_root=self.docs_root,
            locale=self.locale,
            dry_run=self.dry_run,
        )

    @property
    def pipeline_artifacts(self) -> PipelineArtifactConfig:
        """Return the configured pipeline-artifact root."""

        return PipelineArtifactConfig()

    @property
    def locale_coverage(self) -> tuple[str, ...]:
        """Return the locales that should be rendered for this request."""

        if self.locale == "all":
            return ("en", "es")
        return (self.locale,)

    def missing_runtime_env(self) -> tuple[str, ...]:
        """Return missing environment-backed values for a non-dry-run pipeline."""

        missing: list[str] = []
        if not self.openai_api_key:
            missing.append(OPENAI_API_KEY_ENV)
        if not self.openai_model:
            missing.append(OPENAI_MODEL_ENV)
        if not self.public_key_salt:
            missing.append(PUBLIC_KEY_SALT_ENV)
        return tuple(missing)

    def to_display_dict(self) -> dict[str, str | list[str] | None | bool]:
        """Serialize the pipeline request for CLI or workflow output."""

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
            "missing_runtime_env": list(self.missing_runtime_env()) if not self.dry_run else [],
            "source_choices": list(SOURCE_MODES),
            "cadence_choices": list(PIPELINE_CADENCES),
            "locale_choices": list(PIPELINE_LOCALES),
            "openai_env_names": [
                OPENAI_API_KEY_ENV,
                OPENAI_MODEL_ENV,
                PUBLIC_KEY_SALT_ENV,
                OPENAI_BASE_URL_ENV,
            ],
        }
