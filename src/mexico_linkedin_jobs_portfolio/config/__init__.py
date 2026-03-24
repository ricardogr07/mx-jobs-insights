"""Configuration models for upstream workspace discovery, curation, reporting, and site generation."""

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
    ReportStorageConfig,
)
from mexico_linkedin_jobs_portfolio.config.site import SITE_LOCALES, SiteArtifactConfig, SiteConfig
from mexico_linkedin_jobs_portfolio.config.upstream import (
    SOURCE_MODES,
    SourceMode,
    UpstreamWorkspaceConfig,
)

__all__ = [
    "CuratedStorageConfig",
    "OPENAI_API_KEY_ENV",
    "OPENAI_BASE_URL_ENV",
    "OPENAI_MODEL_ENV",
    "PUBLIC_KEY_SALT_ENV",
    "REPORT_CADENCES",
    "REPORT_LOCALES",
    "SITE_LOCALES",
    "ReportCadence",
    "ReportConfig",
    "ReportLocale",
    "ReportStorageConfig",
    "SiteArtifactConfig",
    "SiteConfig",
    "SOURCE_MODES",
    "SourceMode",
    "UpstreamWorkspaceConfig",
]
