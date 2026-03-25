"""Shared readers for report artifacts consumed by site and dashboard surfaces."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from mexico_linkedin_jobs_portfolio.models import (
    ReportMetrics,
    ReportRunSummary,
    SiteReportEntry,
    SiteReportIndex,
)

_FORBIDDEN_PUBLIC_COLUMNS = {"company_name", "job_url", "description_text", "job_id"}


class ReportArtifactIndexReader:
    """Read and validate completed report artifacts for site and dashboard consumers."""

    def load(self, report_root: Path) -> SiteReportIndex:
        report_root = report_root.expanduser().resolve(strict=False)
        run_summary_paths = sorted(report_root.glob("*/*/run_summary.json"))

        entries: list[SiteReportEntry] = []
        for run_summary_path in run_summary_paths:
            entry = self._load_entry(run_summary_path)
            if entry is not None:
                entries.append(entry)

        if not entries:
            raise FileNotFoundError(
                f"No completed report artifacts were found under {report_root}."
            )

        ordered_entries = tuple(
            sorted(
                entries,
                key=lambda entry: (
                    entry.period_end,
                    entry.cadence,
                    entry.period_id,
                ),
                reverse=True,
            )
        )
        weekly_entries = tuple(entry for entry in ordered_entries if entry.cadence == "weekly")
        monthly_entries = tuple(entry for entry in ordered_entries if entry.cadence == "monthly")
        return SiteReportIndex(
            entries=ordered_entries,
            weekly_entries=weekly_entries,
            monthly_entries=monthly_entries,
            latest_weekly=weekly_entries[0] if weekly_entries else None,
            latest_monthly=monthly_entries[0] if monthly_entries else None,
        )

    def _load_entry(self, run_summary_path: Path) -> SiteReportEntry | None:
        payload = json.loads(run_summary_path.read_text(encoding="utf-8"))
        summary = ReportRunSummary.from_display_dict(payload)
        if summary.command_name != "report" or summary.status != "report_written":
            return None
        if summary.metrics_path is None or summary.public_csv_path is None:
            raise FileNotFoundError(
                f"Report artifact bundle at {run_summary_path.parent} is missing metrics or public CSV."
            )

        metrics_path = summary.metrics_path
        public_csv_path = summary.public_csv_path
        metrics = ReportMetrics.from_display_dict(
            json.loads(metrics_path.read_text(encoding="utf-8"))
        )
        self._read_public_csv_header(public_csv_path)
        self._read_locale_files(summary)
        return SiteReportEntry(summary=summary, metrics=metrics)

    @staticmethod
    def _read_public_csv_header(public_csv_path: Path) -> None:
        with public_csv_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.reader(handle)
            header = next(reader, [])
        forbidden = _FORBIDDEN_PUBLIC_COLUMNS.intersection(header)
        if forbidden:
            raise ValueError(
                "Public report CSV exposed forbidden columns: " + ", ".join(sorted(forbidden))
            )

    @staticmethod
    def _read_locale_files(summary: ReportRunSummary) -> None:
        markdown_paths = summary.markdown_paths or {}
        html_paths = summary.html_paths or {}
        for locale in summary.locale_coverage:
            markdown_path = markdown_paths.get(locale)
            html_path = html_paths.get(locale)
            if markdown_path is None or html_path is None:
                raise FileNotFoundError(
                    f"Report artifact bundle at {summary.artifact_dir} is missing locale files for {locale}."
                )
            markdown_text = markdown_path.read_text(encoding="utf-8").strip()
            html_text = html_path.read_text(encoding="utf-8").strip()
            if not markdown_text or not html_text:
                raise ValueError(
                    f"Report artifact bundle at {summary.artifact_dir} contains an empty {locale} report."
                )
