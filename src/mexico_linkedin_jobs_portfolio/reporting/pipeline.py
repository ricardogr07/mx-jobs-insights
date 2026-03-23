"""End-to-end report generation over curated Phase 1 outputs."""

from __future__ import annotations

import json
from pathlib import Path

from mexico_linkedin_jobs_portfolio.analytics import (
    CuratedDatasetReader,
    build_report_metrics,
    resolve_closed_period,
)
from mexico_linkedin_jobs_portfolio.config import ReportConfig
from mexico_linkedin_jobs_portfolio.models import (
    GeneratedNarrative,
    ReportArtifacts,
    ReportMetrics,
    ReportRunSummary,
)
from mexico_linkedin_jobs_portfolio.reporting.openai_narration import (
    NarrationClient,
    OpenAINarrationClient,
)
from mexico_linkedin_jobs_portfolio.reporting.publication import (
    build_public_job_records,
    write_public_csv,
)
from mexico_linkedin_jobs_portfolio.reporting.renderers import render_html, render_markdown


class ReportPipeline:
    """Generate dry-run summaries or full report artifacts for one report request."""

    def __init__(
        self,
        *,
        dataset_reader: CuratedDatasetReader | None = None,
        narration_client: NarrationClient | None = None,
    ) -> None:
        self.dataset_reader = dataset_reader or CuratedDatasetReader()
        self.narration_client = narration_client

    def run(self, config: ReportConfig) -> tuple[ReportRunSummary, int]:
        dataset = self.dataset_reader.load(config.curated_storage)
        period = resolve_closed_period(config.cadence, config.as_of_date)
        metrics_result = build_report_metrics(dataset.records, period)

        notes = [f"Read curated report input from {dataset.storage_mode} storage."]
        if metrics_result.metrics.job_count == 0:
            notes.append("Selected period contains no curated job observations.")

        if config.dry_run:
            notes.append(
                "Dry run computed the aggregate metrics payload without writing artifacts or calling OpenAI."
            )
            return (
                self._build_summary(
                    config,
                    metrics_result.metrics,
                    public_row_count=len(metrics_result.latest_jobs),
                    narration_status="not_requested",
                    status="report_dry_run_ready",
                    notes=tuple(notes),
                ),
                0,
            )

        missing_env = config.missing_runtime_env()
        if missing_env:
            notes.append(
                "Missing required report runtime environment: " + ", ".join(sorted(missing_env))
            )
            return (
                self._build_summary(
                    config,
                    metrics_result.metrics,
                    public_row_count=len(metrics_result.latest_jobs),
                    narration_status="config_invalid",
                    status="report_config_invalid",
                    notes=tuple(notes),
                ),
                1,
            )

        narration_client = self.narration_client or OpenAINarrationClient(
            api_key=config.openai_api_key or "",
            model=config.openai_model or "",
            base_url=config.openai_base_url,
        )
        try:
            narrative = narration_client.generate_bilingual_narrative(metrics_result.metrics)
        except Exception as exc:
            notes.append(str(exc))
            return (
                self._build_summary(
                    config,
                    metrics_result.metrics,
                    public_row_count=len(metrics_result.latest_jobs),
                    narration_status="failed",
                    status="report_narration_failed",
                    notes=tuple(notes),
                ),
                1,
            )

        public_rows = build_public_job_records(
            metrics_result.latest_jobs, config.public_key_salt or ""
        )
        artifacts = self._write_artifacts(config, metrics_result.metrics, narrative, public_rows)
        notes.append(f"Wrote report artifacts to {artifacts.artifact_dir}.")
        summary = self._build_summary(
            config,
            metrics_result.metrics,
            public_row_count=len(public_rows),
            narration_status="generated",
            status="report_written",
            notes=tuple(notes),
            artifacts=artifacts,
        )
        artifacts.run_summary_path.write_text(
            json.dumps(summary.to_display_dict(), indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return summary, 0

    def _write_artifacts(
        self,
        config: ReportConfig,
        metrics: ReportMetrics,
        narrative: GeneratedNarrative,
        public_rows,
    ) -> ReportArtifacts:
        artifact_dir = config.report_storage.period_root(config.cadence, metrics.period.period_id)
        artifact_dir.mkdir(parents=True, exist_ok=True)

        metrics_path = artifact_dir / "metrics.json"
        metrics_path.write_text(
            json.dumps(metrics.to_display_dict(), indent=2, sort_keys=True),
            encoding="utf-8",
        )

        public_csv_path = artifact_dir / "public_jobs.csv"
        write_public_csv(public_rows, public_csv_path)

        markdown_paths: dict[str, Path] = {}
        html_paths: dict[str, Path] = {}
        for locale in config.locale_coverage:
            markdown_path = artifact_dir / f"report.{locale}.md"
            html_path = artifact_dir / f"report.{locale}.html"
            markdown_path.write_text(
                render_markdown(metrics, narrative, locale),
                encoding="utf-8",
            )
            html_path.write_text(render_html(metrics, narrative, locale), encoding="utf-8")
            markdown_paths[locale] = markdown_path
            html_paths[locale] = html_path

        return ReportArtifacts(
            artifact_dir=artifact_dir,
            metrics_path=metrics_path,
            public_csv_path=public_csv_path,
            run_summary_path=artifact_dir / "run_summary.json",
            markdown_paths=markdown_paths,
            html_paths=html_paths,
        )

    @staticmethod
    def _build_summary(
        config: ReportConfig,
        metrics: ReportMetrics,
        *,
        public_row_count: int,
        narration_status: str,
        status: str,
        notes: tuple[str, ...],
        artifacts: ReportArtifacts | None = None,
    ) -> ReportRunSummary:
        return ReportRunSummary(
            command_name="report",
            cadence=config.cadence,
            locale=config.locale,
            locale_coverage=config.locale_coverage,
            curated_root=config.curated_storage.resolved_root(),
            output_root=config.report_storage.resolved_root(),
            dry_run=config.dry_run,
            period_id=metrics.period.period_id,
            period_start=metrics.period.start_date,
            period_end=metrics.period.end_date,
            as_of_date=metrics.period.reference_date,
            observation_count=metrics.observation_count,
            job_count=metrics.job_count,
            source_run_count=metrics.source_run_count,
            public_row_count=public_row_count,
            narration_status=narration_status,
            status=status,
            artifact_dir=artifacts.artifact_dir if artifacts is not None else None,
            metrics_path=artifacts.metrics_path if artifacts is not None else None,
            public_csv_path=artifacts.public_csv_path if artifacts is not None else None,
            run_summary_path=artifacts.run_summary_path if artifacts is not None else None,
            markdown_paths=artifacts.markdown_paths if artifacts is not None else None,
            html_paths=artifacts.html_paths if artifacts is not None else None,
            notes=notes,
        )
