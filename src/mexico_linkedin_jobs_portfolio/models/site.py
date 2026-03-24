"""Public-site and dashboard models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from mexico_linkedin_jobs_portfolio.config import ReportCadence, ReportLocale
from mexico_linkedin_jobs_portfolio.models.reporting import (
    LatestJobRecord,
    ReportMetrics,
    ReportRunSummary,
)


@dataclass(frozen=True, slots=True)
class SiteReportEntry:
    """One indexed report artifact bundle."""

    summary: ReportRunSummary
    metrics: ReportMetrics

    @property
    def cadence(self) -> ReportCadence:
        return self.summary.cadence

    @property
    def period_id(self) -> str:
        return self.summary.period_id or self.metrics.period.period_id

    @property
    def period_start(self) -> date:
        return self.summary.period_start or self.metrics.period.start_date

    @property
    def period_end(self) -> date:
        return self.summary.period_end or self.metrics.period.end_date

    @property
    def locale_coverage(self) -> tuple[str, ...]:
        return self.summary.locale_coverage

    @property
    def artifact_dir(self) -> Path | None:
        return self.summary.artifact_dir

    def asset_relative_dir(self) -> Path:
        """Return the relative asset directory used by the public site."""

        return Path("assets") / self.cadence / self.period_id


@dataclass(frozen=True, slots=True)
class SiteReportIndex:
    """Indexed report artifacts grouped for public site generation."""

    entries: tuple[SiteReportEntry, ...]
    weekly_entries: tuple[SiteReportEntry, ...]
    monthly_entries: tuple[SiteReportEntry, ...]
    latest_weekly: SiteReportEntry | None
    latest_monthly: SiteReportEntry | None

    @property
    def report_count(self) -> int:
        return len(self.entries)

    @property
    def locale_coverage(self) -> tuple[str, ...]:
        coverage: set[str] = set()
        for entry in self.entries:
            coverage.update(entry.locale_coverage)
        return tuple(sorted(coverage))


@dataclass(frozen=True, slots=True)
class SiteArtifacts:
    """Filesystem outputs emitted by one non-dry-run site generation."""

    landing_path: Path
    weekly_index_path: Path
    monthly_index_path: Path
    downloads_index_path: Path
    methodology_path: Path
    generated_period_pages: tuple[Path, ...]
    copied_assets: tuple[Path, ...]
    run_summary_path: Path

    @property
    def generated_page_count(self) -> int:
        return 5 + len(self.generated_period_pages)

    @property
    def copied_asset_count(self) -> int:
        return len(self.copied_assets)


@dataclass(frozen=True, slots=True)
class SiteRunSummary:
    """CLI-facing summary of one site-generation run."""

    command_name: str
    report_root: Path
    docs_root: Path
    public_root: Path
    locale: ReportLocale
    locale_coverage: tuple[str, ...]
    dry_run: bool
    report_count: int = 0
    latest_weekly_period_id: str | None = None
    latest_monthly_period_id: str | None = None
    generated_page_count: int = 0
    copied_asset_count: int = 0
    run_summary_path: Path | None = None
    status: str = "not_run"
    notes: tuple[str, ...] = ()

    def to_display_dict(self) -> dict[str, Any]:
        """Serialize the site-generation summary for CLI output."""

        return {
            "command_name": self.command_name,
            "report_root": str(self.report_root),
            "docs_root": str(self.docs_root),
            "public_root": str(self.public_root),
            "locale": self.locale,
            "locale_coverage": list(self.locale_coverage),
            "dry_run": self.dry_run,
            "report_count": self.report_count,
            "latest_weekly_period_id": self.latest_weekly_period_id,
            "latest_monthly_period_id": self.latest_monthly_period_id,
            "generated_page_count": self.generated_page_count,
            "copied_asset_count": self.copied_asset_count,
            "run_summary_path": (
                str(self.run_summary_path) if self.run_summary_path is not None else None
            ),
            "status": self.status,
            "notes": list(self.notes),
        }


@dataclass(frozen=True, slots=True)
class DashboardState:
    """Shared Streamlit view model built from curated data and report artifacts."""

    report_index: SiteReportIndex
    selected_entry: SiteReportEntry | None
    selected_latest_jobs: tuple[LatestJobRecord, ...]







