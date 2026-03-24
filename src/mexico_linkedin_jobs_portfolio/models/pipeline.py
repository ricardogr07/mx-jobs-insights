"""Phase 4 automation pipeline models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from mexico_linkedin_jobs_portfolio.config import ReportCadence, ReportLocale, SourceMode


@dataclass(frozen=True, slots=True)
class PipelineRunSummary:
    """CLI-facing summary of one Phase 4 automation pipeline run."""

    command_name: str
    cadence: ReportCadence
    source_mode: SourceMode
    locale: ReportLocale
    locale_coverage: tuple[str, ...]
    upstream_root: Path
    curated_root: Path
    report_root: Path
    docs_root: Path
    dry_run: bool
    resolved_source_mode: SourceMode | None = None
    period_id: str | None = None
    period_start: date | None = None
    period_end: date | None = None
    as_of_date: date | None = None
    source_run_count: int = 0
    observation_count: int = 0
    job_count: int = 0
    public_row_count: int = 0
    workspace_status: str = "not_run"
    curate_status: str = "not_run"
    report_status: str = "not_run"
    site_status: str = "not_run"
    docs_status: str = "not_run"
    publish_ready: bool = False
    duckdb_path: Path | None = None
    report_run_summary_path: Path | None = None
    site_run_summary_path: Path | None = None
    pipeline_run_summary_path: Path | None = None
    site_output_root: Path | None = None
    status: str = "planned_shell"
    notes: tuple[str, ...] = ()

    def to_display_dict(self) -> dict[str, Any]:
        """Serialize the pipeline summary for CLI JSON output."""

        return {
            "command_name": self.command_name,
            "cadence": self.cadence,
            "source_mode": self.source_mode,
            "resolved_source_mode": self.resolved_source_mode,
            "locale": self.locale,
            "locale_coverage": list(self.locale_coverage),
            "upstream_root": str(self.upstream_root),
            "curated_root": str(self.curated_root),
            "report_root": str(self.report_root),
            "docs_root": str(self.docs_root),
            "dry_run": self.dry_run,
            "period_id": self.period_id,
            "period_start": self.period_start.isoformat() if self.period_start is not None else None,
            "period_end": self.period_end.isoformat() if self.period_end is not None else None,
            "as_of_date": self.as_of_date.isoformat() if self.as_of_date is not None else None,
            "source_run_count": self.source_run_count,
            "observation_count": self.observation_count,
            "job_count": self.job_count,
            "public_row_count": self.public_row_count,
            "workspace_status": self.workspace_status,
            "curate_status": self.curate_status,
            "report_status": self.report_status,
            "site_status": self.site_status,
            "docs_status": self.docs_status,
            "publish_ready": self.publish_ready,
            "duckdb_path": str(self.duckdb_path) if self.duckdb_path is not None else None,
            "report_run_summary_path": (
                str(self.report_run_summary_path)
                if self.report_run_summary_path is not None
                else None
            ),
            "site_run_summary_path": (
                str(self.site_run_summary_path) if self.site_run_summary_path is not None else None
            ),
            "pipeline_run_summary_path": (
                str(self.pipeline_run_summary_path)
                if self.pipeline_run_summary_path is not None
                else None
            ),
            "site_output_root": (
                str(self.site_output_root) if self.site_output_root is not None else None
            ),
            "status": self.status,
            "notes": list(self.notes),
        }
