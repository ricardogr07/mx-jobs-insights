"""Canonical data models shared by ingestion, curation, and later analytics layers."""

from mexico_linkedin_jobs_portfolio.models.ingestion import (
    CanonicalEntityRecord,
    CanonicalObservationRecord,
    CanonicalSourceRunRecord,
    IngestionRunSummary,
    WorkspaceValidationResult,
)

__all__ = [
    "CanonicalEntityRecord",
    "CanonicalObservationRecord",
    "CanonicalSourceRunRecord",
    "IngestionRunSummary",
    "WorkspaceValidationResult",
]
