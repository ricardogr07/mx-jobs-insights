"""Automation orchestration over curate, report, site, docs validation, and optional cloud delivery."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from uuid import uuid4

from mexico_linkedin_jobs_portfolio.analytics import resolve_closed_period
from mexico_linkedin_jobs_portfolio.automation.upstream_sync import GitUpstreamWorkspaceSeeder
from mexico_linkedin_jobs_portfolio.cloud import BigQueryExporter, CloudArtifactPublisher
from mexico_linkedin_jobs_portfolio.config import PipelineConfig
from mexico_linkedin_jobs_portfolio.curation import DuckDBCuratedStore, build_curated_batch
from mexico_linkedin_jobs_portfolio.models import (
    BigQueryExportResult,
    CloudSyncResult,
    IngestionRunSummary,
    PipelineRunSummary,
    WorkspaceValidationResult,
)
from mexico_linkedin_jobs_portfolio.presentation import SitePipeline
from mexico_linkedin_jobs_portfolio.reporting import ReportPipeline
from mexico_linkedin_jobs_portfolio.sources import (
    CsvSourceAdapter,
    LocalUpstreamWorkspaceProvider,
    SQLiteSourceAdapter,
)


class MkDocsBuildRunner:
    """Run strict MkDocs builds against the configured docs root."""

    def __init__(
        self,
        *,
        project_root: Path | None = None,
        config_path: Path | None = None,
    ) -> None:
        self.project_root = (project_root or Path.cwd()).expanduser().resolve(strict=False)
        self.config_path = (
            (config_path or (self.project_root / "mkdocs.yml")).expanduser().resolve(strict=False)
        )

    def build(self, docs_root: Path) -> tuple[Path | None, str, tuple[str, ...], int]:
        if not self.config_path.is_file():
            return (
                None,
                "mkdocs_config_missing",
                (f"Missing MkDocs config at {self.config_path}.",),
                1,
            )

        docs_root = docs_root.expanduser().resolve(strict=False)
        site_output_root = docs_root.parent / "site"
        command = [sys.executable, "-m", "mkdocs", "build", "--strict"]

        if docs_root != (self.project_root / "docs").resolve(strict=False):
            temp_root = self.project_root / "artifacts" / "mkdocs-temp"
            temp_root.mkdir(parents=True, exist_ok=True)
            temp_config_path = temp_root / f"mkdocs.generated.{uuid4().hex}.yml"
            temp_config_path.write_text(
                self._render_config(docs_root, site_output_root),
                encoding="utf-8",
            )
            try:
                result = subprocess.run(
                    [*command, "--config-file", str(temp_config_path)],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    check=False,
                )
            finally:
                temp_config_path.unlink(missing_ok=True)
        else:
            result = subprocess.run(
                command,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=False,
            )

        status = "mkdocs_build_passed" if result.returncode == 0 else "mkdocs_build_failed"
        notes = self._collect_process_notes(result)
        return (
            site_output_root if result.returncode == 0 else None,
            status,
            notes,
            result.returncode,
        )

    def _render_config(self, docs_root: Path, site_output_root: Path) -> str:
        lines = self.config_path.read_text(encoding="utf-8").splitlines()
        rendered: list[str] = []
        docs_dir_replaced = False
        site_dir_replaced = False
        docs_dir_index = -1
        for idx, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("docs_dir:"):
                rendered.append(f"docs_dir: {docs_root.as_posix()}")
                docs_dir_replaced = True
                docs_dir_index = len(rendered) - 1
                continue
            if stripped.startswith("site_dir:"):
                rendered.append(f"site_dir: {site_output_root.as_posix()}")
                site_dir_replaced = True
                continue
            rendered.append(line)

        if not docs_dir_replaced:
            rendered.insert(0, f"docs_dir: {docs_root.as_posix()}")
            docs_dir_index = 0
        if not site_dir_replaced:
            # Insert site_dir after docs_dir, or at position 1 if no docs_dir found
            insertion_index = docs_dir_index + 1 if docs_dir_index >= 0 else 1
            rendered.insert(insertion_index, f"site_dir: {site_output_root.as_posix()}")
        return "\n".join(rendered) + "\n"

    @staticmethod
    def _collect_process_notes(result: subprocess.CompletedProcess[str]) -> tuple[str, ...]:
        notes: list[str] = []
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
        if stdout:
            notes.extend(line for line in stdout.splitlines()[-6:] if line.strip())
        if stderr:
            notes.extend(line for line in stderr.splitlines()[-6:] if line.strip())
        return tuple(notes)


class PipelineOrchestrator:
    """Sequence local pipeline primitives into automation and optional cloud delivery."""

    def __init__(
        self,
        *,
        workspace_provider: LocalUpstreamWorkspaceProvider | None = None,
        report_pipeline: ReportPipeline | None = None,
        site_pipeline: SitePipeline | None = None,
        docs_builder: MkDocsBuildRunner | None = None,
        cloud_storage_publisher: CloudArtifactPublisher | None = None,
        bigquery_exporter: BigQueryExporter | None = None,
        upstream_seeder: GitUpstreamWorkspaceSeeder | None = None,
    ) -> None:
        self.workspace_provider = workspace_provider or LocalUpstreamWorkspaceProvider()
        self.report_pipeline = report_pipeline or ReportPipeline()
        self.site_pipeline = site_pipeline or SitePipeline()
        self.docs_builder = docs_builder or MkDocsBuildRunner()
        self.cloud_storage_publisher = cloud_storage_publisher or CloudArtifactPublisher()
        self.bigquery_exporter = bigquery_exporter or BigQueryExporter()
        self.upstream_seeder = upstream_seeder or GitUpstreamWorkspaceSeeder()

    def run(self, config: PipelineConfig) -> tuple[PipelineRunSummary, int]:
        workspace = config.workspace
        period = resolve_closed_period(config.cadence, config.as_of_date)
        validation = self.workspace_provider.validate(workspace)
        notes: list[str] = []
        cloud_environment = config.cloud_environment
        cloud_requested = cloud_environment.cloud_requested

        if (
            not config.dry_run
            and cloud_requested
            and not validation.is_valid
            and (not validation.root_exists or not validation.is_directory)
        ):
            try:
                _, seeding_notes = self.upstream_seeder.ensure_workspace(
                    workspace,
                    repo_url=config.upstream_repo_url,
                )
                notes.extend(seeding_notes)
                validation = self.workspace_provider.validate(workspace)
            except Exception as exc:
                notes.extend(validation.notes)
                notes.append(f"Managed upstream workspace seeding failed: {exc}")
                summary = self._build_summary(
                    config,
                    period=period,
                    validation=validation,
                    workspace_status="workspace_seed_failed",
                    cloud_requested=cloud_requested,
                    status="pipeline_workspace_seed_failed",
                    notes=tuple(notes + list(validation.errors)),
                )
                return self._finalize(config, summary, 1)

        notes.extend(validation.notes)

        if not validation.is_valid:
            summary = self._build_summary(
                config,
                period=period,
                validation=validation,
                workspace_status=validation.status,
                cloud_requested=cloud_requested,
                status="pipeline_workspace_invalid",
                notes=tuple(notes + list(validation.errors)),
            )
            return self._finalize(config, summary, 1)

        if not config.dry_run and cloud_requested and not cloud_environment.is_configured:
            missing_cloud = list(config.missing_cloud_runtime_env())
            notes.append(
                "Cloud delivery was requested because GCP environment variables were present."
            )
            notes.append(f"Missing cloud runtime env: {', '.join(missing_cloud)}.")
            summary = self._build_summary(
                config,
                period=period,
                validation=validation,
                workspace_status=validation.status,
                cloud_requested=cloud_requested,
                cloud_storage_status="cloud_config_invalid",
                bigquery_status="cloud_config_invalid",
                status="pipeline_cloud_config_invalid",
                notes=tuple(notes),
            )
            return self._finalize(config, summary, 1)

        observations, entities, adapter_summary = self._load_adapter_records(workspace, validation)
        notes.extend(adapter_summary.notes)
        batch = build_curated_batch(observations, entities, adapter_summary)
        notes.append(
            f"Pipeline resolved {len(batch.source_runs)} source run projection(s) from {validation.resolved_source_mode} input."
        )

        if config.dry_run:
            cloud_storage_status = (
                "cloud_sync_planned"
                if cloud_requested and cloud_environment.is_configured
                else "not_requested"
            )
            bigquery_status = (
                "bigquery_export_planned"
                if cloud_requested and cloud_environment.is_configured
                else "not_requested"
            )
            if cloud_storage_status == "cloud_sync_planned":
                notes.append(
                    f"Dry run detected a complete cloud runtime for bucket {cloud_environment.gcs_bucket} and BigQuery datasets {cloud_environment.bigquery_private_dataset}/{cloud_environment.bigquery_public_dataset}."
                )
            notes.append("Dry run validated workspace discovery and canonical batching only.")
            summary = self._build_summary(
                config,
                period=period,
                validation=validation,
                workspace_status=validation.status,
                curate_status="curation_dry_run_ready",
                report_status="report_dry_run_planned",
                site_status="site_dry_run_planned",
                docs_status="mkdocs_build_planned",
                cloud_requested=cloud_requested,
                cloud_storage_status=cloud_storage_status,
                bigquery_status=bigquery_status,
                source_run_count=len(batch.source_runs),
                observation_count=adapter_summary.observation_count,
                status="pipeline_dry_run_ready",
                notes=tuple(notes),
            )
            return summary, 0

        write_result = DuckDBCuratedStore(config.curated_storage).persist_batch(batch)
        notes.append(f"Wrote curated outputs to {write_result.duckdb_path}.")

        report_summary, report_exit_code = self.report_pipeline.run(config.report_config)
        notes.extend(report_summary.notes)
        if report_exit_code != 0:
            summary = self._build_summary(
                config,
                period=period,
                validation=validation,
                workspace_status=validation.status,
                curate_status="curation_written",
                report_status=report_summary.status,
                cloud_requested=cloud_requested,
                source_run_count=write_result.source_run_count,
                observation_count=adapter_summary.observation_count,
                job_count=report_summary.job_count,
                public_row_count=report_summary.public_row_count,
                duckdb_path=write_result.duckdb_path,
                report_run_summary_path=report_summary.run_summary_path,
                status="pipeline_report_failed",
                notes=tuple(notes),
            )
            return self._finalize(config, summary, 1)

        project_docs_root = self._project_docs_root()
        if config.site_config.docs_root_resolved != project_docs_root:
            self._prepare_docs_root(config.site_config.docs_root_resolved)
            notes.append(
                f"Seeded docs workspace from {project_docs_root} into {config.site_config.docs_root_resolved}."
            )

        site_summary, site_exit_code = self.site_pipeline.run(config.site_config)
        notes.extend(site_summary.notes)
        if site_exit_code != 0:
            summary = self._build_summary(
                config,
                period=period,
                validation=validation,
                workspace_status=validation.status,
                curate_status="curation_written",
                report_status=report_summary.status,
                site_status=site_summary.status,
                cloud_requested=cloud_requested,
                source_run_count=write_result.source_run_count,
                observation_count=report_summary.observation_count,
                job_count=report_summary.job_count,
                public_row_count=report_summary.public_row_count,
                duckdb_path=write_result.duckdb_path,
                report_run_summary_path=report_summary.run_summary_path,
                site_run_summary_path=site_summary.run_summary_path,
                status="pipeline_site_failed",
                notes=tuple(notes),
            )
            return self._finalize(config, summary, 1)

        site_output_root, docs_status, docs_notes, docs_exit_code = self.docs_builder.build(
            config.site_config.docs_root_resolved
        )
        notes.extend(docs_notes)
        if docs_exit_code != 0:
            summary = self._build_summary(
                config,
                period=period,
                validation=validation,
                workspace_status=validation.status,
                curate_status="curation_written",
                report_status=report_summary.status,
                site_status=site_summary.status,
                docs_status=docs_status,
                cloud_requested=cloud_requested,
                source_run_count=write_result.source_run_count,
                observation_count=report_summary.observation_count,
                job_count=report_summary.job_count,
                public_row_count=report_summary.public_row_count,
                duckdb_path=write_result.duckdb_path,
                report_run_summary_path=report_summary.run_summary_path,
                site_run_summary_path=site_summary.run_summary_path,
                site_output_root=site_output_root,
                status="pipeline_docs_failed",
                notes=tuple(notes),
            )
            return self._finalize(config, summary, 1)

        cloud_sync: CloudSyncResult | None = None
        bigquery_export: BigQueryExportResult | None = None
        cloud_storage_status = "not_requested"
        bigquery_status = "not_requested"
        cloud_ready = False
        status = "pipeline_written"
        publish_ready = True

        if cloud_requested and cloud_environment.is_configured:
            diagnostics_paths = tuple(
                path
                for path in (
                    report_summary.run_summary_path,
                    site_summary.run_summary_path,
                    config.pipeline_artifacts.run_summary_path,
                )
                if path is not None
            )
            try:
                cloud_sync = self.cloud_storage_publisher.publish(
                    cloud_environment,
                    curated_root=config.curated_storage.resolved_root(),
                    report_root=config.report_config.report_storage.resolved_root(),
                    site_output_root=site_output_root,
                    diagnostics_paths=diagnostics_paths,
                )
                cloud_storage_status = cloud_sync.status
                notes.extend(cloud_sync.notes)
            except Exception as exc:
                notes.append(f"Cloud storage publish failed: {exc}")
                summary = self._build_summary(
                    config,
                    period=period,
                    validation=validation,
                    workspace_status=validation.status,
                    curate_status="curation_written",
                    report_status=report_summary.status,
                    site_status=site_summary.status,
                    docs_status=docs_status,
                    cloud_requested=True,
                    cloud_storage_status="gcs_publish_failed",
                    bigquery_status="not_run",
                    source_run_count=write_result.source_run_count,
                    observation_count=report_summary.observation_count,
                    job_count=report_summary.job_count,
                    public_row_count=report_summary.public_row_count,
                    duckdb_path=write_result.duckdb_path,
                    report_run_summary_path=report_summary.run_summary_path,
                    site_run_summary_path=site_summary.run_summary_path,
                    site_output_root=site_output_root,
                    status="pipeline_cloud_storage_failed",
                    notes=tuple(notes),
                )
                return self._finalize(config, summary, 1)

            try:
                bigquery_export = self.bigquery_exporter.export(
                    cloud_environment,
                    duckdb_path=write_result.duckdb_path,
                    metrics_path=report_summary.metrics_path,
                    public_csv_path=report_summary.public_csv_path,
                    report_run_summary_path=report_summary.run_summary_path,
                )
                bigquery_status = bigquery_export.status
                notes.extend(bigquery_export.notes)
            except Exception as exc:
                notes.append(f"BigQuery export failed: {exc}")
                summary = self._build_summary(
                    config,
                    period=period,
                    validation=validation,
                    workspace_status=validation.status,
                    curate_status="curation_written",
                    report_status=report_summary.status,
                    site_status=site_summary.status,
                    docs_status=docs_status,
                    cloud_requested=True,
                    cloud_storage_status=cloud_storage_status,
                    bigquery_status="bigquery_export_failed",
                    source_run_count=write_result.source_run_count,
                    observation_count=report_summary.observation_count,
                    job_count=report_summary.job_count,
                    public_row_count=report_summary.public_row_count,
                    duckdb_path=write_result.duckdb_path,
                    report_run_summary_path=report_summary.run_summary_path,
                    site_run_summary_path=site_summary.run_summary_path,
                    site_output_root=site_output_root,
                    cloud_sync=cloud_sync,
                    status="pipeline_bigquery_failed",
                    notes=tuple(notes),
                )
                return self._finalize(config, summary, 1)

            cloud_ready = True
            status = "pipeline_cloud_written"

        summary = self._build_summary(
            config,
            period=period,
            validation=validation,
            workspace_status=validation.status,
            curate_status="curation_written",
            report_status=report_summary.status,
            site_status=site_summary.status,
            docs_status=docs_status,
            cloud_requested=cloud_requested,
            cloud_storage_status=cloud_storage_status,
            bigquery_status=bigquery_status,
            source_run_count=write_result.source_run_count,
            observation_count=report_summary.observation_count,
            job_count=report_summary.job_count,
            public_row_count=report_summary.public_row_count,
            duckdb_path=write_result.duckdb_path,
            report_run_summary_path=report_summary.run_summary_path,
            site_run_summary_path=site_summary.run_summary_path,
            site_output_root=site_output_root,
            publish_ready=publish_ready,
            cloud_ready=cloud_ready,
            cloud_sync=cloud_sync,
            bigquery_export=bigquery_export,
            status=status,
            notes=tuple(notes),
        )
        return self._finalize(config, summary, 0)

    def _project_docs_root(self) -> Path:
        builder_root = getattr(self.docs_builder, "project_root", Path.cwd())
        return (Path(builder_root).expanduser().resolve(strict=False) / "docs").resolve(
            strict=False
        )

    def _prepare_docs_root(self, docs_root: Path) -> None:
        project_docs_root = self._project_docs_root()
        docs_root = docs_root.expanduser().resolve(strict=False)
        if docs_root == project_docs_root or not project_docs_root.is_dir():
            return

        docs_root.mkdir(parents=True, exist_ok=True)
        public_root = docs_root / "public"
        if public_root.exists():
            shutil.rmtree(public_root)
        index_path = docs_root / "index.md"
        if index_path.exists():
            index_path.unlink()

        def ignore_root_public(current_dir: str, names: list[str]) -> set[str]:
            if Path(current_dir).resolve(strict=False) == project_docs_root:
                return {name for name in names if name in {"public", "index.md"}}
            return set()

        shutil.copytree(
            project_docs_root,
            docs_root,
            dirs_exist_ok=True,
            ignore=ignore_root_public,
        )

    @staticmethod
    def _load_adapter_records(
        workspace,
        validation: WorkspaceValidationResult,
    ) -> tuple[list, list, IngestionRunSummary]:
        if validation.resolved_source_mode == "sqlite":
            return SQLiteSourceAdapter().load(workspace)
        if validation.resolved_source_mode == "csv":
            return CsvSourceAdapter().load(workspace)
        raise RuntimeError("No resolved source mode is available for pipeline orchestration.")

    @staticmethod
    def _build_summary(
        config: PipelineConfig,
        *,
        period,
        validation: WorkspaceValidationResult,
        workspace_status: str,
        status: str,
        notes: tuple[str, ...],
        curate_status: str = "not_run",
        report_status: str = "not_run",
        site_status: str = "not_run",
        docs_status: str = "not_run",
        cloud_storage_status: str = "not_requested",
        bigquery_status: str = "not_requested",
        source_run_count: int = 0,
        observation_count: int = 0,
        job_count: int = 0,
        public_row_count: int = 0,
        publish_ready: bool = False,
        cloud_ready: bool = False,
        cloud_requested: bool = False,
        duckdb_path: Path | None = None,
        report_run_summary_path: Path | None = None,
        site_run_summary_path: Path | None = None,
        site_output_root: Path | None = None,
        cloud_sync: CloudSyncResult | None = None,
        bigquery_export: BigQueryExportResult | None = None,
    ) -> PipelineRunSummary:
        return PipelineRunSummary(
            command_name="pipeline",
            cadence=config.cadence,
            source_mode=config.source_mode,
            locale=config.locale,
            locale_coverage=config.locale_coverage,
            upstream_root=config.workspace.resolved_root(),
            curated_root=config.curated_storage.resolved_root(),
            report_root=config.report_config.report_storage.resolved_root(),
            docs_root=config.site_config.docs_root_resolved,
            dry_run=config.dry_run,
            resolved_source_mode=validation.resolved_source_mode,
            period_id=period.period_id,
            period_start=period.start_date,
            period_end=period.end_date,
            as_of_date=period.reference_date,
            source_run_count=source_run_count,
            observation_count=observation_count,
            job_count=job_count,
            public_row_count=public_row_count,
            workspace_status=workspace_status,
            curate_status=curate_status,
            report_status=report_status,
            site_status=site_status,
            docs_status=docs_status,
            cloud_storage_status=cloud_storage_status,
            bigquery_status=bigquery_status,
            publish_ready=publish_ready,
            cloud_ready=cloud_ready,
            cloud_requested=cloud_requested,
            duckdb_path=duckdb_path,
            report_run_summary_path=report_run_summary_path,
            site_run_summary_path=site_run_summary_path,
            site_output_root=site_output_root,
            cloud_sync=cloud_sync,
            bigquery_export=bigquery_export,
            status=status,
            notes=notes,
        )

    @staticmethod
    def _finalize(
        config: PipelineConfig, summary: PipelineRunSummary, exit_code: int
    ) -> tuple[PipelineRunSummary, int]:
        if config.dry_run:
            return summary, exit_code

        config.pipeline_artifacts.resolved_root().mkdir(parents=True, exist_ok=True)
        finalized = replace(
            summary,
            pipeline_run_summary_path=config.pipeline_artifacts.run_summary_path,
        )
        config.pipeline_artifacts.run_summary_path.write_text(
            json.dumps(finalized.to_display_dict(), indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return finalized, exit_code
