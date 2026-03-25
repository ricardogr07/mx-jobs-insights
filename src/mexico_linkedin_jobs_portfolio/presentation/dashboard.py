"""Shared Streamlit view-model builders."""

from __future__ import annotations

from pathlib import Path

from mexico_linkedin_jobs_portfolio.analytics import CuratedDatasetReader, build_report_metrics
from mexico_linkedin_jobs_portfolio.config import CuratedStorageConfig
from mexico_linkedin_jobs_portfolio.models import DashboardState, SiteReportEntry
from mexico_linkedin_jobs_portfolio.presentation.catalog import ReportArtifactIndexReader


class DashboardDataLoader:
    """Build the Streamlit view model from report artifacts plus curated storage."""

    def __init__(
        self,
        *,
        index_reader: ReportArtifactIndexReader | None = None,
        dataset_reader: CuratedDatasetReader | None = None,
    ) -> None:
        self.index_reader = index_reader or ReportArtifactIndexReader()
        self.dataset_reader = dataset_reader or CuratedDatasetReader()

    def load(
        self,
        *,
        report_root: Path,
        curated_root: Path,
        cadence: str | None = None,
        period_id: str | None = None,
    ) -> DashboardState:
        report_index = self.index_reader.load(report_root)
        selected_entry = self._select_entry(report_index, cadence=cadence, period_id=period_id)
        if selected_entry is None:
            return DashboardState(
                report_index=report_index,
                selected_entry=None,
                selected_latest_jobs=(),
            )

        dataset = self.dataset_reader.load(CuratedStorageConfig(root=curated_root))
        selected_latest_jobs = build_report_metrics(
            dataset.records,
            selected_entry.metrics.period,
        ).latest_jobs
        return DashboardState(
            report_index=report_index,
            selected_entry=selected_entry,
            selected_latest_jobs=selected_latest_jobs,
        )

    @staticmethod
    def _select_entry(
        report_index,
        *,
        cadence: str | None,
        period_id: str | None,
    ) -> SiteReportEntry | None:
        if cadence and period_id:
            for entry in report_index.entries:
                if entry.cadence == cadence and entry.period_id == period_id:
                    return entry
        if cadence == "weekly":
            return report_index.latest_weekly
        if cadence == "monthly":
            return report_index.latest_monthly
        return report_index.latest_monthly or report_index.latest_weekly
