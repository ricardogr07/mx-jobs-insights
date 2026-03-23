"""Source adapter contracts for SQLite and CSV ingestion paths."""

from mexico_linkedin_jobs_portfolio.sources.base import SourceAdapter
from mexico_linkedin_jobs_portfolio.sources.csv import CsvSourceAdapter
from mexico_linkedin_jobs_portfolio.sources.sqlite import SQLiteSourceAdapter
from mexico_linkedin_jobs_portfolio.sources.workspace import (
    LocalUpstreamWorkspaceProvider,
    UpstreamWorkspaceProvider,
    resolve_source_mode,
)

__all__ = [
    "CsvSourceAdapter",
    "LocalUpstreamWorkspaceProvider",
    "SourceAdapter",
    "SQLiteSourceAdapter",
    "UpstreamWorkspaceProvider",
    "resolve_source_mode",
]
