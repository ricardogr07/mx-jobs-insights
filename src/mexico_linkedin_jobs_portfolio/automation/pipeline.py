"""Phase 4 automation orchestration over curate, report, site, and docs validation."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from uuid import uuid4

from mexico_linkedin_jobs_portfolio.analytics import resolve_closed_period
from mexico_linkedin_jobs_portfolio.config import PipelineConfig
from mexico_linkedin_jobs_portfolio.curation import DuckDBCuratedStore, build_curated_batch
from mexico_linkedin_jobs_portfolio.models import (
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
            config_path or (self.project_root / "mkdocs.yml")
        ).expanduser().resolve(strict=False)

    def build(self, docs_root: Path) -> tuple[Path | None, str, tuple[str, ...], int]:
        """Run `mkdocs build --strict` for the provided docs root."""

        if not self.config_path.is_file():
            return None, "mkdocs_config_missing", (f"Missing MkDocs config at {self.config_path}.",), 1

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
        return site_output_root if result.returncode == 0 else None, status, notes, result.returncode

    def _render_config(self, docs_root: Path, site_output_root: Path) -> str:
        """Return a temporary MkDocs config that points at a custom docs root."""

        lines = self.config_path.read_text(encoding="utf-8").splitlines()
        rendered: list[str] = []
        docs_dir_replaced = False
        site_dir_replaced = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("docs_dir:"):
                rendered.append(f"docs_dir: {docs_root.as_posix()}")
                docs_dir_replaced = True
                continue
            if stripped.startswith("site_dir:"):
                rendered.append(f"site_dir: {site_output_root.as_posix()}")
                site_dir_replaced = True
                continue
            rendered.append(line)

        if not docs_dir_replaced:
            rendered.insert(0, f"docs_dir: {docs_root.as_posix()}")
        if not site_dir_replaced:
            insertion_index = 1 if rendered else 0
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
    """Sequence Phase 1-3 primitives into the Phase 4 automation entrypoint."""

    def __init__(
        self,
        *,
        workspace_provider: LocalUpstreamWorkspaceProvider | None = None,
        report_pipeline: ReportPipeline | None = None,
        site_pipeline: SitePipeline | None = None,
        docs_builder: MkDocsBuildRunner | None = None,
    ) -> None:
        self.workspace_provider = workspace_provider or LocalUpstreamWorkspaceProvider()
        self.report_pipeline = report_pipeline or ReportPipeline()
        self.site_pipeline = site_pipeline or SitePipeline()
        self.docs_builder = docs_builder or MkDocsBuildRunner()

    def run(self, config: PipelineConfig) -> tuple[PipelineRunSummary, int]:
        workspace = config.workspace
        validation = self.workspace_provider.validate(workspace)
        period = resolve_closed_period(config.cadence, config.as_of_date)
        notes = list(validation.notes)

        if not validation.is_valid:
            summary = self._build_summary(
                config,
                period=period,
                validation=validation,
                workspace_status=validation.status,
                status="pipeline_workspace_invalid",
                notes=tuple(notes + list(validation.errors)),
            )
            return self._finalize(config, summary, 1)

        observations, entities, adapter_summary = self._load_adapter_records(workspace, validation)
        notes.extend(adapter_summary.notes)
        batch = build_curated_batch(observations, entities, adapter_summary)
        notes.append(
            f"Pipeline resolved {len(batch.source_runs)} source run projection(s) from {validation.resolved_source_mode} input."
        )

        if config.dry_run:
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
                source_run_count=write_result.source_run_count,
                observation_count=write_result.observation_count,
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

        summary = self._build_summary(
            config,
            period=period,
            validation=validation,
            workspace_status=validation.status,
            curate_status="curation_written",
            report_status=report_summary.status,
            site_status=site_summary.status,
            docs_status=docs_status,
            source_run_count=write_result.source_run_count,
            observation_count=report_summary.observation_count,
            job_count=report_summary.job_count,
            public_row_count=report_summary.public_row_count,
            duckdb_path=write_result.duckdb_path,
            report_run_summary_path=report_summary.run_summary_path,
            site_run_summary_path=site_summary.run_summary_path,
            site_output_root=site_output_root,
            publish_ready=True,
            status="pipeline_written",
            notes=tuple(notes),
        )
        return self._finalize(config, summary, 0)

    def _project_docs_root(self) -> Path:
        builder_root = getattr(self.docs_builder, "project_root", Path.cwd())
        return (Path(builder_root).expanduser().resolve(strict=False) / "docs").resolve(strict=False)

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
        source_run_count: int = 0,
        observation_count: int = 0,
        job_count: int = 0,
        public_row_count: int = 0,
        publish_ready: bool = False,
        duckdb_path: Path | None = None,
        report_run_summary_path: Path | None = None,
        site_run_summary_path: Path | None = None,
        site_output_root: Path | None = None,
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
            publish_ready=publish_ready,
            duckdb_path=duckdb_path,
            report_run_summary_path=report_run_summary_path,
            site_run_summary_path=site_run_summary_path,
            site_output_root=site_output_root,
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












