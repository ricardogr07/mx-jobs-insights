"""End-to-end public-site generation from Phase 2 report artifacts."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from mexico_linkedin_jobs_portfolio.config import SiteConfig
from mexico_linkedin_jobs_portfolio.models import SiteArtifacts, SiteReportIndex, SiteRunSummary
from mexico_linkedin_jobs_portfolio.presentation.catalog import ReportArtifactIndexReader
from mexico_linkedin_jobs_portfolio.presentation.site_renderers import (
    render_archive_page,
    render_downloads_page,
    render_landing_page,
    render_methodology_page,
    render_period_page,
)


class SitePipeline:
    """Generate dry-run summaries or public MkDocs source pages from report artifacts."""

    def __init__(self, *, index_reader: ReportArtifactIndexReader | None = None) -> None:
        self.index_reader = index_reader or ReportArtifactIndexReader()

    def run(self, config: SiteConfig) -> tuple[SiteRunSummary, int]:
        try:
            report_index = self.index_reader.load(config.report_root_resolved)
        except FileNotFoundError as exc:
            return (
                SiteRunSummary(
                    command_name="site",
                    report_root=config.report_root_resolved,
                    docs_root=config.docs_root_resolved,
                    public_root=config.public_root,
                    locale=config.locale,
                    locale_coverage=config.locale_coverage,
                    dry_run=config.dry_run,
                    status="site_index_empty",
                    notes=(str(exc),),
                ),
                1,
            )

        notes = [
            f"Read {report_index.report_count} completed report bundle(s) from {config.report_root_resolved}.",
            "Site generation uses only Phase 2 report artifacts and public CSV downloads.",
        ]
        if config.dry_run:
            notes.append("Dry run resolved the public site index without writing MkDocs source pages.")
            return self._build_summary(
                config,
                report_index,
                status="site_dry_run_ready",
                notes=tuple(notes),
            ), 0

        artifacts = self._write_site(config, report_index)
        config.site_artifacts.resolved_root().mkdir(parents=True, exist_ok=True)
        summary = self._build_summary(
            config,
            report_index,
            status="site_written",
            notes=tuple(notes + [f"Wrote public site source under {config.docs_root_resolved}."]),
            artifacts=artifacts,
        )
        config.site_artifacts.run_summary_path.write_text(
            json.dumps(summary.to_display_dict(), indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return summary, 0

    def _write_site(self, config: SiteConfig, report_index: SiteReportIndex) -> SiteArtifacts:
        public_root = config.public_root
        weekly_root = public_root / "weekly"
        monthly_root = public_root / "monthly"
        downloads_root = public_root / "downloads"
        asset_root = config.asset_root

        for directory in (public_root, weekly_root, monthly_root, downloads_root, asset_root):
            directory.mkdir(parents=True, exist_ok=True)

        landing_path = config.docs_root_resolved / "index.md"
        weekly_index_path = weekly_root / "index.md"
        monthly_index_path = monthly_root / "index.md"
        downloads_index_path = downloads_root / "index.md"
        methodology_path = public_root / "methodology.md"

        generated_period_pages: list[Path] = []
        copied_assets: list[Path] = []

        landing_path.write_text(
            render_landing_page(
                report_index,
                locale_coverage=config.locale_coverage,
                landing_path=landing_path,
                weekly_index_path=weekly_index_path,
                monthly_index_path=monthly_index_path,
                methodology_path=methodology_path,
                downloads_index_path=downloads_index_path,
                public_root=public_root,
            ),
            encoding="utf-8",
        )
        weekly_index_path.write_text(
            render_archive_page(
                "weekly",
                report_index.weekly_entries,
                locale_coverage=config.locale_coverage,
                page_path=weekly_index_path,
                public_root=public_root,
            ),
            encoding="utf-8",
        )
        monthly_index_path.write_text(
            render_archive_page(
                "monthly",
                report_index.monthly_entries,
                locale_coverage=config.locale_coverage,
                page_path=monthly_index_path,
                public_root=public_root,
            ),
            encoding="utf-8",
        )
        downloads_index_path.write_text(
            render_downloads_page(
                report_index,
                locale_coverage=config.locale_coverage,
                page_path=downloads_index_path,
                public_root=public_root,
            ),
            encoding="utf-8",
        )
        methodology_path.write_text(
            render_methodology_page(locale_coverage=config.locale_coverage),
            encoding="utf-8",
        )

        for entry in report_index.entries:
            period_page = public_root / entry.cadence / f"{entry.period_id}.md"
            period_page.parent.mkdir(parents=True, exist_ok=True)
            period_page.write_text(
                render_period_page(
                    entry,
                    locale_coverage=config.locale_coverage,
                    page_path=period_page,
                    public_root=public_root,
                ),
                encoding="utf-8",
            )
            generated_period_pages.append(period_page)
            copied_assets.extend(self._copy_entry_assets(entry, config))

        return SiteArtifacts(
            landing_path=landing_path,
            weekly_index_path=weekly_index_path,
            monthly_index_path=monthly_index_path,
            downloads_index_path=downloads_index_path,
            methodology_path=methodology_path,
            generated_period_pages=tuple(generated_period_pages),
            copied_assets=tuple(copied_assets),
            run_summary_path=config.site_artifacts.run_summary_path,
        )

    @staticmethod
    def _copy_entry_assets(entry, config: SiteConfig) -> list[Path]:
        copied: list[Path] = []
        asset_dir = config.public_root / entry.asset_relative_dir()
        asset_dir.mkdir(parents=True, exist_ok=True)

        if entry.summary.public_csv_path is not None:
            csv_target = asset_dir / "public_jobs.csv"
            shutil.copy2(entry.summary.public_csv_path, csv_target)
            copied.append(csv_target)

        html_paths = entry.summary.html_paths or {}
        for locale in config.locale_coverage:
            source = html_paths.get(locale)
            if source is None:
                continue
            target = asset_dir / f"report.{locale}.html"
            shutil.copy2(source, target)
            copied.append(target)

        return copied

    @staticmethod
    def _build_summary(
        config: SiteConfig,
        report_index: SiteReportIndex,
        *,
        status: str,
        notes: tuple[str, ...],
        artifacts: SiteArtifacts | None = None,
    ) -> SiteRunSummary:
        return SiteRunSummary(
            command_name="site",
            report_root=config.report_root_resolved,
            docs_root=config.docs_root_resolved,
            public_root=config.public_root,
            locale=config.locale,
            locale_coverage=config.locale_coverage,
            dry_run=config.dry_run,
            report_count=report_index.report_count,
            latest_weekly_period_id=(
                report_index.latest_weekly.period_id if report_index.latest_weekly is not None else None
            ),
            latest_monthly_period_id=(
                report_index.latest_monthly.period_id if report_index.latest_monthly is not None else None
            ),
            generated_page_count=artifacts.generated_page_count if artifacts is not None else 0,
            copied_asset_count=artifacts.copied_asset_count if artifacts is not None else 0,
            run_summary_path=artifacts.run_summary_path if artifacts is not None else None,
            status=status,
            notes=notes,
        )
