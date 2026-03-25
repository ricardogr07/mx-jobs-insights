from __future__ import annotations

import json
from pathlib import Path

from mexico_linkedin_jobs_portfolio.cloud import BigQueryExporter, CloudArtifactPublisher
from mexico_linkedin_jobs_portfolio.config import CloudEnvironmentConfig
from tests.presentation_fixtures import write_report_fixtures


class RecordingBlob:
    def __init__(self, name: str, uploads: list[tuple[str, str]]) -> None:
        self.name = name
        self.uploads = uploads

    def upload_from_filename(self, filename: str) -> None:
        self.uploads.append((self.name, filename))


class RecordingBucket:
    def __init__(self, uploads: list[tuple[str, str]]) -> None:
        self.uploads = uploads

    def blob(self, blob_name: str) -> RecordingBlob:
        return RecordingBlob(blob_name, self.uploads)


class RecordingStorageClient:
    def __init__(self) -> None:
        self.bucket_name: str | None = None
        self.uploads: list[tuple[str, str]] = []

    def bucket(self, bucket_name: str) -> RecordingBucket:
        self.bucket_name = bucket_name
        return RecordingBucket(self.uploads)


class RecordingLoadJob:
    def result(self) -> None:
        return None


class RecordingBigQueryClient:
    def __init__(self) -> None:
        self.loads: list[tuple[str, list[dict[str, object]]]] = []

    def load_table_from_json(
        self, rows: list[dict[str, object]], destination: str
    ) -> RecordingLoadJob:
        self.loads.append((destination, rows))
        return RecordingLoadJob()


def _cloud_config() -> CloudEnvironmentConfig:
    return CloudEnvironmentConfig(
        project_id="demo-project",
        region="us-central1",
        gcs_bucket="mx-jobs-bucket",
        gcs_prefix="phase5/release",
        bigquery_private_dataset="mx_jobs_private",
        bigquery_public_dataset="mx_jobs_public",
    )


def test_cloud_artifact_publisher_mirrors_curated_report_site_and_diagnostics(
    tmp_path: Path,
) -> None:
    curated_root, report_root = write_report_fixtures(tmp_path)
    site_root = tmp_path / "site"
    site_root.mkdir(parents=True)
    (site_root / "index.html").write_text("<html>site</html>", encoding="utf-8")

    pipeline_summary_path = tmp_path / "artifacts" / "pipeline" / "run_summary.json"
    pipeline_summary_path.parent.mkdir(parents=True, exist_ok=True)
    pipeline_summary_path.write_text(json.dumps({"status": "ok"}), encoding="utf-8")

    storage_client = RecordingStorageClient()
    publisher = CloudArtifactPublisher(storage_client=storage_client)
    result = publisher.publish(
        _cloud_config(),
        curated_root=curated_root,
        report_root=report_root,
        site_output_root=site_root,
        diagnostics_paths=(
            report_root / "monthly" / "2026-03" / "run_summary.json",
            pipeline_summary_path,
        ),
    )

    uploaded_names = [object_name for object_name, _ in storage_client.uploads]

    assert result.status == "gcs_published"
    assert result.uploaded_object_count == len(storage_client.uploads)
    assert storage_client.bucket_name == "mx-jobs-bucket"
    assert any(name.startswith("phase5/release/curated/") for name in uploaded_names)
    assert any(name.startswith("phase5/release/reports/") for name in uploaded_names)
    assert any(name.startswith("phase5/release/site/") for name in uploaded_names)
    assert "phase5/release/diagnostics/reports/monthly/2026-03/run_summary.json" in uploaded_names
    assert "phase5/release/diagnostics/pipeline/run_summary.json" in uploaded_names


def test_bigquery_exporter_mirrors_private_and_public_tables(tmp_path: Path) -> None:
    curated_root, report_root = write_report_fixtures(tmp_path)
    monthly_root = report_root / "monthly" / "2026-03"

    client = RecordingBigQueryClient()
    exporter = BigQueryExporter(bigquery_client=client)
    result = exporter.export(
        _cloud_config(),
        duckdb_path=curated_root / "mx_jobs_insights.duckdb",
        metrics_path=monthly_root / "metrics.json",
        public_csv_path=monthly_root / "public_jobs.csv",
        report_run_summary_path=monthly_root / "run_summary.json",
    )

    destinations = {destination for destination, _ in client.loads}

    assert result.status == "bigquery_exported"
    assert result.private_table_count == 4
    assert result.public_table_count == 2
    assert "demo-project.mx_jobs_private.source_runs" in destinations
    assert "demo-project.mx_jobs_private.job_observations" in destinations
    assert "demo-project.mx_jobs_private.job_entities" in destinations
    assert "demo-project.mx_jobs_private.report_run_summaries" in destinations
    assert "demo-project.mx_jobs_public.public_jobs" in destinations
    assert "demo-project.mx_jobs_public.report_metrics" in destinations
