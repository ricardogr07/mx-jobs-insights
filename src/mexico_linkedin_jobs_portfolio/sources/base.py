"""Protocol definitions for upstream source adapters."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from mexico_linkedin_jobs_portfolio.config import SourceMode, UpstreamWorkspaceConfig
from mexico_linkedin_jobs_portfolio.models import (
    CanonicalEntityRecord,
    CanonicalObservationRecord,
    IngestionRunSummary,
)


@runtime_checkable
class SourceAdapter(Protocol):
    """Define the minimal contract that SQLite and CSV adapters must satisfy."""

    mode: SourceMode

    def is_available(self, workspace: UpstreamWorkspaceConfig) -> bool:
        """Return whether this adapter can read from the provided workspace."""

    def load(
        self,
        workspace: UpstreamWorkspaceConfig,
    ) -> tuple[list[CanonicalObservationRecord], list[CanonicalEntityRecord], IngestionRunSummary]:
        """Load canonical observation and entity records plus a run summary from the workspace."""
