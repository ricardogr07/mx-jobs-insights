from __future__ import annotations

import json
import shutil
from dataclasses import replace
from datetime import date
from pathlib import Path
from typing import cast

import pytest

from mexico_linkedin_jobs_portfolio.automation import PipelineOrchestrator
from mexico_linkedin_jobs_portfolio.config import (
    PipelineConfig,
    ReportCadence,
    UpstreamWorkspaceConfig,
)
from mexico_linkedin_jobs_portfolio.models import (
    BigQueryExportResult,
    BigQueryTableExport,
    CloudSyncResult,
    UploadedObject,
)
from mexico_linkedin_jobs_portfolio.reporting import ReportPipeline
from tests.presentation_fixtures import StubNarrationClient
from tests.sample_data import copy_sample_workspace


class RecordingDocsBuilder:
    def __init__(self) -> None:
        self.calls: list[Path] = []
        self.project_root = Path(__file__).resolve().parents[1]

    def build(self, docs_root: Path) -> tuple[Path | None, str, tuple[str, ...], int]:
        self.calls.append(docs_root)
        return (
            docs_root.parent / "site",
            "mkdocs_build_passed",
            ("mkdocs build validated in test.",),
            0,
        )


class RecordingCloudPublisher:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def publish(
        self,
        cloud_config,
        *,
        curated_root: Path,
        report_root: Path,
        site_output_root: Path | None,
        diagnostics_paths: tuple[Path, ...] = (),
    ) -> CloudSyncResult:
        self.calls.append(
            {
                "bucket": cloud_config.gcs_bucket,
                "curated_root": curated_root,
                "report_root": report_root,
                "site_output_root": site_output_root,
                "diagnostics_paths": diagnostics_paths,
            }
        )
        return CloudSyncResult(
            bucket=cloud_config.gcs_bucket or "",
            prefix=cloud_config.normalized_gcs_prefix or None,
            uploads=(
                UploadedObject(
                    category="site",
                    local_path=site_output_root / "index.html"
                    if site_output_root is not None
                    else report_root,
                    object_name=f"{cloud_config.normalized_gcs_prefix}/site/index.html",
                ),
            ),
            status="gcs_published",
            notes=("Uploaded test cloud artifacts.",),
        )


class RecordingBigQueryExporter:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def export(
        self,
        cloud_config,
        *,
        duckdb_path: Path,
        metrics_path: Path | None,
        public_csv_path: Path | None,
        report_run_summary_path: Path | None,
    ) -> BigQueryExportResult:
        self.calls.append(
            {
                "project_id": cloud_config.project_id,
                "duckdb_path": duckdb_path,
                "metrics_path": metrics_path,
                "public_csv_path": public_csv_path,
                "report_run_summary_path": report_run_summary_path,
            }
        )
        return BigQueryExportResult(
            project_id=cloud_config.project_id or "",
            private_dataset=cloud_config.bigquery_private_dataset or "",
            public_dataset=cloud_config.bigquery_public_dataset or "",
            tables=(
                BigQueryTableExport(
                    dataset_id=cloud_config.bigquery_private_dataset or "",
                    table_name="job_observations",
                    visibility="private",
                    row_count=2,
                ),
                BigQueryTableExport(
                    dataset_id=cloud_config.bigquery_public_dataset or "",
                    table_name="public_jobs",
                    visibility="public",
                    row_count=2,
                ),
            ),
            status="bigquery_exported",
            notes=("Exported test BigQuery tables.",),
        )


class CopyingUpstreamSeeder:
    def __init__(self, source_root: Path) -> None:
        self.source_root = source_root
        self.calls: list[tuple[Path, str, str]] = []

    def ensure_workspace(
        self,
        workspace: UpstreamWorkspaceConfig,
        *,
        repo_url: str,
    ) -> tuple[str, tuple[str, ...]]:
        target_root = workspace.resolved_root()
        self.calls.append((target_root, repo_url, workspace.preferred_ref))
        shutil.copytree(self.source_root, target_root, copy_function=shutil.copy2)
        return "workspace_seeded", ("Seeded test upstream workspace for cloud execution.",)


def _safe_finalize(config, summary, exit_code):
    if config.dry_run:
        return summary, exit_code

    finalized = replace(
        summary, pipeline_run_summary_path=config.pipeline_artifacts.run_summary_path
    )
    config.pipeline_artifacts.resolved_root().mkdir(parents=True, exist_ok=True)
    config.pipeline_artifacts.run_summary_path.write_text(
        json.dumps(finalized.to_display_dict(), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return finalized, exit_code


def _build_config(
    tmp_path: Path,
    *,
    cadence: str,
    as_of_date: date,
    dry_run: bool,
    with_cloud: bool = False,
    upstream_root: Path | None = None,
) -> tuple[PipelineConfig, Path]:
    workspace_root = upstream_root or copy_sample_workspace(tmp_path)
    config = PipelineConfig(
        cadence=cast(ReportCadence, cadence),
        upstream_root=workspace_root,
        curated_root=tmp_path / "curated",
        report_root=tmp_path / "reports",
        docs_root=tmp_path / "docs",
        as_of_date=as_of_date,
        dry_run=dry_run,
        openai_api_key="test-key",
        openai_model="gpt-5.4-nano",
        public_key_salt="test-salt",
        google_cloud_project="demo-project" if with_cloud else None,
        gcp_region="us-central1" if with_cloud else None,
        gcs_bucket="mx-jobs-bucket" if with_cloud else None,
        gcs_prefix="phase5/release" if with_cloud else None,
        bigquery_private_dataset="mx_jobs_private" if with_cloud else None,
        bigquery_public_dataset="mx_jobs_public" if with_cloud else None,
    )
    return config, workspace_root


def test_pipeline_dry_run_summarizes_workspace_and_period(tmp_path: Path) -> None:
    config, _ = _build_config(
        tmp_path,
        cadence="weekly",
        as_of_date=date(2026, 3, 23),
        dry_run=True,
    )

    summary, exit_code = PipelineOrchestrator().run(config)

    assert exit_code == 0
    assert summary.status == "pipeline_dry_run_ready"
    assert summary.workspace_status == "workspace_valid"
    assert summary.curate_status == "curation_dry_run_ready"
    assert summary.report_status == "report_dry_run_planned"
    assert summary.site_status == "site_dry_run_planned"
    assert summary.docs_status == "mkdocs_build_planned"
    assert summary.resolved_source_mode == "sqlite"
    assert summary.period_id == "2026-W12"
    assert summary.source_run_count == 1
    assert summary.publish_ready is False
    assert summary.pipeline_run_summary_path is None


def test_pipeline_dry_run_plans_cloud_delivery_when_runtime_is_complete(tmp_path: Path) -> None:
    config, _ = _build_config(
        tmp_path,
        cadence="weekly",
        as_of_date=date(2026, 3, 23),
        dry_run=True,
        with_cloud=True,
    )

    summary, exit_code = PipelineOrchestrator().run(config)

    assert exit_code == 0
    assert summary.status == "pipeline_dry_run_ready"
    assert summary.cloud_requested is True
    assert summary.cloud_storage_status == "cloud_sync_planned"
    assert summary.bigquery_status == "bigquery_export_planned"


@pytest.mark.parametrize(
    (
        "cadence",
        "as_of_date",
        "expected_period_id",
        "expected_observation_count",
        "expected_job_count",
        "expected_public_row_count",
    ),
    [
        ("weekly", date(2026, 3, 30), "2026-W13", 0, 0, 0),
        ("monthly", date(2026, 4, 1), "2026-03", 2, 2, 2),
    ],
)
def test_pipeline_non_dry_run_reuses_fixture_backed_flows(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    cadence: str,
    as_of_date: date,
    expected_period_id: str,
    expected_observation_count: int,
    expected_job_count: int,
    expected_public_row_count: int,
) -> None:
    config, _ = _build_config(
        tmp_path,
        cadence=cadence,
        as_of_date=as_of_date,
        dry_run=False,
    )
    docs_builder = RecordingDocsBuilder()
    orchestrator = PipelineOrchestrator(
        report_pipeline=ReportPipeline(narration_client=StubNarrationClient()),
        docs_builder=docs_builder,
    )
    monkeypatch.setattr(PipelineOrchestrator, "_finalize", staticmethod(_safe_finalize))

    summary, exit_code = orchestrator.run(config)

    assert exit_code == 0
    assert summary.status == "pipeline_written"
    assert summary.publish_ready is True
    assert summary.period_id == expected_period_id
    assert summary.workspace_status == "workspace_valid"
    assert summary.curate_status == "curation_written"
    assert summary.report_status == "report_written"
    assert summary.site_status == "site_written"
    assert summary.docs_status == "mkdocs_build_passed"
    assert summary.resolved_source_mode == "sqlite"
    assert summary.source_run_count == 1
    assert summary.observation_count == expected_observation_count
    assert summary.job_count == expected_job_count
    assert summary.public_row_count == expected_public_row_count
    assert summary.duckdb_path is not None and summary.duckdb_path.is_file()
    assert summary.report_run_summary_path is not None and summary.report_run_summary_path.is_file()
    assert summary.site_run_summary_path is not None and summary.site_run_summary_path.is_file()
    assert (
        summary.pipeline_run_summary_path is not None
        and summary.pipeline_run_summary_path.is_file()
    )
    assert summary.site_output_root is not None
    assert summary.site_output_root.name == "site"
    assert not (config.docs_root / "development").exists()
    assert docs_builder.calls == [config.docs_root]


def test_pipeline_non_dry_run_writes_cloud_delivery_summaries(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config, _ = _build_config(
        tmp_path,
        cadence="monthly",
        as_of_date=date(2026, 4, 1),
        dry_run=False,
        with_cloud=True,
    )
    docs_builder = RecordingDocsBuilder()
    cloud_publisher = RecordingCloudPublisher()
    bigquery_exporter = RecordingBigQueryExporter()
    orchestrator = PipelineOrchestrator(
        report_pipeline=ReportPipeline(narration_client=StubNarrationClient()),
        docs_builder=docs_builder,
        cloud_storage_publisher=cloud_publisher,
        bigquery_exporter=bigquery_exporter,
    )
    monkeypatch.setattr(PipelineOrchestrator, "_finalize", staticmethod(_safe_finalize))

    summary, exit_code = orchestrator.run(config)

    assert exit_code == 0
    assert summary.status == "pipeline_cloud_written"
    assert summary.cloud_requested is True
    assert summary.cloud_ready is True
    assert summary.cloud_storage_status == "gcs_published"
    assert summary.bigquery_status == "bigquery_exported"
    assert summary.cloud_sync is not None
    assert summary.bigquery_export is not None
    assert cloud_publisher.calls
    assert bigquery_exporter.calls


def test_pipeline_non_dry_run_can_seed_missing_upstream_workspace_for_cloud_runs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seed_source = copy_sample_workspace(tmp_path / "seed-source")
    missing_root = tmp_path / "cloud-workspace" / "LinkedInWebScraper"
    config, _ = _build_config(
        tmp_path,
        cadence="monthly",
        as_of_date=date(2026, 4, 1),
        dry_run=False,
        with_cloud=True,
        upstream_root=missing_root,
    )
    docs_builder = RecordingDocsBuilder()
    cloud_publisher = RecordingCloudPublisher()
    bigquery_exporter = RecordingBigQueryExporter()
    upstream_seeder = CopyingUpstreamSeeder(seed_source)
    orchestrator = PipelineOrchestrator(
        report_pipeline=ReportPipeline(narration_client=StubNarrationClient()),
        docs_builder=docs_builder,
        cloud_storage_publisher=cloud_publisher,
        bigquery_exporter=bigquery_exporter,
        upstream_seeder=upstream_seeder,
    )
    monkeypatch.setattr(PipelineOrchestrator, "_finalize", staticmethod(_safe_finalize))

    summary, exit_code = orchestrator.run(config)

    assert exit_code == 0
    assert summary.status == "pipeline_cloud_written"
    assert missing_root.is_dir()
    assert upstream_seeder.calls == [
        (
            missing_root.resolve(strict=False),
            config.upstream_repo_url,
            config.workspace.preferred_ref,
        )
    ]
    assert any("Seeded test upstream workspace" in note for note in summary.notes)


def test_pipeline_non_dry_run_fails_closed_when_report_runtime_env_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    upstream_root = copy_sample_workspace(tmp_path)
    config = PipelineConfig(
        cadence="monthly",
        upstream_root=upstream_root,
        curated_root=tmp_path / "curated",
        report_root=tmp_path / "reports",
        docs_root=tmp_path / "docs",
        as_of_date=date(2026, 4, 1),
        dry_run=False,
    )
    monkeypatch.setattr(PipelineOrchestrator, "_finalize", staticmethod(_safe_finalize))

    summary, exit_code = PipelineOrchestrator().run(config)

    assert exit_code == 1
    assert summary.status == "pipeline_report_failed"
    assert summary.curate_status == "curation_written"
    assert summary.report_status == "report_config_invalid"
    assert summary.site_status == "not_run"
    assert summary.docs_status == "not_run"
    assert summary.publish_ready is False
    assert (
        summary.pipeline_run_summary_path is not None
        and summary.pipeline_run_summary_path.is_file()
    )
    assert "OPENAI_API_KEY" in "\n".join(summary.notes)
    assert "MX_JOBS_OPENAI_MODEL" in "\n".join(summary.notes)
    assert "MX_JOBS_PUBLIC_KEY_SALT" in "\n".join(summary.notes)


def test_pipeline_non_dry_run_fails_closed_when_cloud_runtime_is_incomplete(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    upstream_root = copy_sample_workspace(tmp_path)
    config = PipelineConfig(
        cadence="monthly",
        upstream_root=upstream_root,
        curated_root=tmp_path / "curated",
        report_root=tmp_path / "reports",
        docs_root=tmp_path / "docs",
        as_of_date=date(2026, 4, 1),
        dry_run=False,
        openai_api_key="test-key",
        openai_model="gpt-5.4-nano",
        public_key_salt="test-salt",
        google_cloud_project="demo-project",
    )
    monkeypatch.setattr(PipelineOrchestrator, "_finalize", staticmethod(_safe_finalize))

    summary, exit_code = PipelineOrchestrator().run(config)

    assert exit_code == 1
    assert summary.status == "pipeline_cloud_config_invalid"
    assert summary.cloud_requested is True
    assert summary.cloud_storage_status == "cloud_config_invalid"
    assert summary.bigquery_status == "cloud_config_invalid"
    assert (
        summary.pipeline_run_summary_path is not None
        and summary.pipeline_run_summary_path.is_file()
    )
    assert "MX_JOBS_GCP_REGION" in "\n".join(summary.notes)
    assert "MX_JOBS_GCS_BUCKET" in "\n".join(summary.notes)
    assert "MX_JOBS_BIGQUERY_PRIVATE_DATASET" in "\n".join(summary.notes)
    assert "MX_JOBS_BIGQUERY_PUBLIC_DATASET" in "\n".join(summary.notes)
