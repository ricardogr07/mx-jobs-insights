"""BigQuery export helpers."""

from __future__ import annotations

import csv
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any, Protocol

import duckdb

from mexico_linkedin_jobs_portfolio.config.cloud import CloudEnvironmentConfig
from mexico_linkedin_jobs_portfolio.models.cloud import BigQueryExportResult, BigQueryTableExport


class LoadJobProtocol(Protocol):
    def result(self) -> Any: ...


class BigQueryClientProtocol(Protocol):
    def load_table_from_json(self, rows: list[dict[str, Any]], destination: str) -> LoadJobProtocol: ...


class BigQueryExporter:
    """Export curated private data and public-safe report artifacts into BigQuery."""

    PRIVATE_CURATED_TABLES: tuple[str, ...] = ("source_runs", "job_observations", "job_entities")

    def __init__(self, bigquery_client: BigQueryClientProtocol | None = None) -> None:
        self.bigquery_client = bigquery_client

    def export(
        self,
        cloud_config: CloudEnvironmentConfig,
        *,
        duckdb_path: Path,
        metrics_path: Path | None,
        public_csv_path: Path | None,
        report_run_summary_path: Path | None,
    ) -> BigQueryExportResult:
        client = self._bigquery_client()
        exported_tables: list[BigQueryTableExport] = []

        for table_name in self.PRIVATE_CURATED_TABLES:
            rows = self._load_duckdb_table(duckdb_path, table_name)
            if not rows:
                continue
            destination = f"{cloud_config.project_id}.{cloud_config.bigquery_private_dataset}.{table_name}"
            client.load_table_from_json(rows, destination).result()
            exported_tables.append(
                BigQueryTableExport(
                    dataset_id=cloud_config.bigquery_private_dataset or "",
                    table_name=table_name,
                    visibility="private",
                    row_count=len(rows),
                )
            )

        report_summary_rows = self._load_single_json_row(report_run_summary_path)
        if report_summary_rows:
            destination = (
                f"{cloud_config.project_id}.{cloud_config.bigquery_private_dataset}.report_run_summaries"
            )
            client.load_table_from_json(report_summary_rows, destination).result()
            exported_tables.append(
                BigQueryTableExport(
                    dataset_id=cloud_config.bigquery_private_dataset or "",
                    table_name="report_run_summaries",
                    visibility="private",
                    row_count=len(report_summary_rows),
                )
            )

        public_jobs_rows = self._load_public_csv_rows(public_csv_path)
        if public_jobs_rows:
            destination = f"{cloud_config.project_id}.{cloud_config.bigquery_public_dataset}.public_jobs"
            client.load_table_from_json(public_jobs_rows, destination).result()
            exported_tables.append(
                BigQueryTableExport(
                    dataset_id=cloud_config.bigquery_public_dataset or "",
                    table_name="public_jobs",
                    visibility="public",
                    row_count=len(public_jobs_rows),
                )
            )

        metrics_rows = self._load_single_json_row(metrics_path)
        if metrics_rows:
            destination = f"{cloud_config.project_id}.{cloud_config.bigquery_public_dataset}.report_metrics"
            client.load_table_from_json(metrics_rows, destination).result()
            exported_tables.append(
                BigQueryTableExport(
                    dataset_id=cloud_config.bigquery_public_dataset or "",
                    table_name="report_metrics",
                    visibility="public",
                    row_count=len(metrics_rows),
                )
            )

        return BigQueryExportResult(
            project_id=cloud_config.project_id or "",
            private_dataset=cloud_config.bigquery_private_dataset or "",
            public_dataset=cloud_config.bigquery_public_dataset or "",
            tables=tuple(exported_tables),
            status="bigquery_exported" if exported_tables else "bigquery_export_skipped",
            notes=(
                f"Exported {len(exported_tables)} BigQuery table load(s) for project {cloud_config.project_id}.",
            )
            if exported_tables
            else ("No BigQuery rows were selected for export.",),
        )

    def _bigquery_client(self) -> BigQueryClientProtocol:
        if self.bigquery_client is not None:
            return self.bigquery_client

        try:
            from google.cloud import bigquery  # type: ignore
        except ImportError as exc:  # pragma: no cover - exercised via fake clients in tests.
            raise RuntimeError(
                "BigQuery export requires google-cloud-bigquery or an injected BigQuery client."
            ) from exc
        return bigquery.Client()

    @staticmethod
    def _load_duckdb_table(duckdb_path: Path, table_name: str) -> list[dict[str, Any]]:
        if not Path(duckdb_path).is_file():
            return []

        with duckdb.connect(str(duckdb_path), read_only=True) as connection:
            result = connection.execute(f"SELECT * FROM {table_name}")
            columns = [description[0] for description in result.description]
            rows = result.fetchall()
        return [
            {
                column: BigQueryExporter._normalize_value(value)
                for column, value in zip(columns, row, strict=True)
            }
            for row in rows
        ]

    @staticmethod
    def _load_single_json_row(path: Path | None) -> list[dict[str, Any]]:
        if path is None or not Path(path).is_file():
            return []
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            return []
        return [{key: BigQueryExporter._normalize_value(value) for key, value in payload.items()}]

    @staticmethod
    def _load_public_csv_rows(path: Path | None) -> list[dict[str, Any]]:
        if path is None or not Path(path).is_file():
            return []
        with Path(path).open("r", encoding="utf-8", newline="") as handle:
            return [{key: value for key, value in row.items()} for row in csv.DictReader(handle)]

    @staticmethod
    def _normalize_value(value: Any) -> Any:
        if isinstance(value, (date, datetime)):
            return value.isoformat()
        if isinstance(value, Path):
            return str(value)
        if isinstance(value, tuple):
            return [BigQueryExporter._normalize_value(item) for item in value]
        if isinstance(value, list):
            return [BigQueryExporter._normalize_value(item) for item in value]
        if isinstance(value, dict):
            return {str(key): BigQueryExporter._normalize_value(item) for key, item in value.items()}
        return value


