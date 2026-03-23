"""Mexico LinkedIn jobs portfolio package."""

from __future__ import annotations

from collections.abc import Sequence

from mexico_linkedin_jobs_portfolio.config import (
    SOURCE_MODES,
    CuratedStorageConfig,
    SourceMode,
    UpstreamWorkspaceConfig,
)
from mexico_linkedin_jobs_portfolio.curation import (
    CuratedBatch,
    CuratedWriteResult,
    DuckDBCuratedStore,
    build_curated_batch,
)
from mexico_linkedin_jobs_portfolio.models import (
    CanonicalEntityRecord,
    CanonicalObservationRecord,
    CanonicalSourceRunRecord,
    IngestionRunSummary,
    WorkspaceValidationResult,
)
from mexico_linkedin_jobs_portfolio.sources import (
    CsvSourceAdapter,
    LocalUpstreamWorkspaceProvider,
    SourceAdapter,
    SQLiteSourceAdapter,
    UpstreamWorkspaceProvider,
    resolve_source_mode,
)


def run_cli(argv: Sequence[str] | None = None) -> int:
    from mexico_linkedin_jobs_portfolio.interfaces.cli.main import main

    return main(argv)


__all__ = [
    "CanonicalEntityRecord",
    "CanonicalObservationRecord",
    "CanonicalSourceRunRecord",
    "CsvSourceAdapter",
    "CuratedBatch",
    "CuratedStorageConfig",
    "CuratedWriteResult",
    "DuckDBCuratedStore",
    "IngestionRunSummary",
    "LocalUpstreamWorkspaceProvider",
    "SOURCE_MODES",
    "SourceAdapter",
    "SQLiteSourceAdapter",
    "SourceMode",
    "UpstreamWorkspaceConfig",
    "UpstreamWorkspaceProvider",
    "WorkspaceValidationResult",
    "build_curated_batch",
    "resolve_source_mode",
    "run_cli",
]
