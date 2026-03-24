"""Canonical ingestion records and run summaries for the portfolio pipeline."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any

from mexico_linkedin_jobs_portfolio.config import SourceMode


@dataclass(frozen=True, slots=True)
class CanonicalObservationRecord:
    """Observation-grain job record used by the curated analytics model."""

    job_id: str
    observed_at: date
    source_mode: SourceMode
    city: str
    title: str
    state: str | None = None
    country: str = "Mexico"
    reported_date: date | None = None
    source_run_id: str | None = None
    remote_type: str | None = None
    seniority_level: str | None = None
    employment_type: str | None = None


@dataclass(frozen=True, slots=True)
class CanonicalEntityRecord:
    """Latest-known job entity attributes shared across observations."""

    job_id: str
    canonical_title: str
    company_name: str | None = None
    job_url: str | None = None
    description_text: str | None = None
    industry: str | None = None
    english_required: bool | None = None
    minimum_years_experience: float | None = None
    tech_stack: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class CanonicalSourceRunRecord:
    """Canonical source-run projection used by the curated storage shell."""

    source_run_id: str
    source_mode: SourceMode
    observed_at_min: date
    observed_at_max: date
    upstream_root: Path
    observation_count: int
    job_count: int
    city_count: int
    status: str


@dataclass(frozen=True, slots=True)
class WorkspaceValidationResult:
    """Describe whether the local upstream workspace satisfies the documented source contract."""

    requested_source_mode: SourceMode
    upstream_root: Path
    root_exists: bool
    is_directory: bool
    sqlite_available: bool
    exports_available: bool
    latest_exports_available: bool
    dated_export_directories: tuple[str, ...] = ()
    preferred_ref: str = "data"
    preferred_ref_available: bool | None = None
    has_git_metadata: bool = False
    resolved_source_mode: SourceMode | None = None
    errors: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()

    @property
    def available_sources(self) -> tuple[SourceMode, ...]:
        sources: list[SourceMode] = []
        if self.sqlite_available:
            sources.append("sqlite")
        if self.exports_available:
            sources.append("csv")
        return tuple(sources)

    @property
    def is_valid(self) -> bool:
        return not self.errors

    @property
    def status(self) -> str:
        return "workspace_valid" if self.is_valid else "workspace_invalid"

    def to_display_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["upstream_root"] = str(self.upstream_root)
        payload["dated_export_directories"] = list(self.dated_export_directories)
        payload["errors"] = list(self.errors)
        payload["notes"] = list(self.notes)
        payload["available_sources"] = list(self.available_sources)
        payload["is_valid"] = self.is_valid
        payload["status"] = self.status
        return payload


@dataclass(frozen=True, slots=True)
class IngestionRunSummary:
    """Describe the current ingestion or curation run state for review and dry runs."""

    command_name: str
    source_mode: SourceMode
    upstream_root: Path
    dry_run: bool
    resolved_source_mode: SourceMode | None = None
    source_run_count: int = 0
    observation_count: int = 0
    entity_count: int = 0
    duckdb_path: Path | None = None
    parquet_root: Path | None = None
    status: str = "not_run"
    notes: tuple[str, ...] = ()

    def to_display_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["upstream_root"] = str(self.upstream_root)
        payload["duckdb_path"] = str(self.duckdb_path) if self.duckdb_path is not None else None
        payload["notes"] = list(self.notes)
        payload["parquet_root"] = str(self.parquet_root) if self.parquet_root is not None else None
        return payload



