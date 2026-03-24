"""Canonical data models shared by ingestion, curation, analytics, and reporting layers."""

from mexico_linkedin_jobs_portfolio.models.ingestion import (
    CanonicalEntityRecord,
    CanonicalObservationRecord,
    CanonicalSourceRunRecord,
    IngestionRunSummary,
    WorkspaceValidationResult,
)
from mexico_linkedin_jobs_portfolio.models.pipeline import PipelineRunSummary
from mexico_linkedin_jobs_portfolio.models.reporting import (
    DimensionCount,
    GeneratedNarrative,
    LatestJobRecord,
    PeriodWindow,
    PublicJobRecord,
    ReportArtifacts,
    ReportMetrics,
    ReportRunSummary,
)
from mexico_linkedin_jobs_portfolio.models.site import (
    DashboardState,
    SiteArtifacts,
    SiteReportEntry,
    SiteReportIndex,
    SiteRunSummary,
)

__all__ = [
    "CanonicalEntityRecord",
    "CanonicalObservationRecord",
    "CanonicalSourceRunRecord",
    "DimensionCount",
    "DashboardState",
    "GeneratedNarrative",
    "IngestionRunSummary",
    "LatestJobRecord",
    "PipelineRunSummary",
    "PeriodWindow",
    "PublicJobRecord",
    "ReportArtifacts",
    "ReportMetrics",
    "ReportRunSummary",
    "SiteArtifacts",
    "SiteReportEntry",
    "SiteReportIndex",
    "SiteRunSummary",
    "WorkspaceValidationResult",
]
