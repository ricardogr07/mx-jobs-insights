"""Canonical data models shared by ingestion, curation, analytics, and reporting layers."""

from mexico_linkedin_jobs_portfolio.models.ingestion import (
    CanonicalEntityRecord,
    CanonicalObservationRecord,
    CanonicalSourceRunRecord,
    IngestionRunSummary,
    WorkspaceValidationResult,
)
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

__all__ = [
    "CanonicalEntityRecord",
    "CanonicalObservationRecord",
    "CanonicalSourceRunRecord",
    "DimensionCount",
    "GeneratedNarrative",
    "IngestionRunSummary",
    "LatestJobRecord",
    "PeriodWindow",
    "PublicJobRecord",
    "ReportArtifacts",
    "ReportMetrics",
    "ReportRunSummary",
    "WorkspaceValidationResult",
]
