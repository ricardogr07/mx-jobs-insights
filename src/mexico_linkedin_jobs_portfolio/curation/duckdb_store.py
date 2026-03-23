"""DuckDB curated storage shell for canonical portfolio records."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import duckdb

from mexico_linkedin_jobs_portfolio.config import CuratedStorageConfig
from mexico_linkedin_jobs_portfolio.models import (
    CanonicalEntityRecord,
    CanonicalObservationRecord,
    CanonicalSourceRunRecord,
    IngestionRunSummary,
)


@dataclass(frozen=True, slots=True)
class CuratedBatch:
    """Canonical batch persisted by the DuckDB curated store."""

    source_runs: tuple[CanonicalSourceRunRecord, ...]
    job_observations: tuple[CanonicalObservationRecord, ...]
    job_entities: tuple[CanonicalEntityRecord, ...]
    summary: IngestionRunSummary


@dataclass(frozen=True, slots=True)
class CuratedWriteResult:
    """Describe the persisted curated outputs produced by one storage write."""

    duckdb_path: Path
    parquet_root: Path
    source_run_count: int
    observation_count: int
    entity_count: int

    def to_display_dict(self) -> dict[str, str | int]:
        return {
            "duckdb_path": str(self.duckdb_path),
            "parquet_root": str(self.parquet_root),
            "source_run_count": self.source_run_count,
            "observation_count": self.observation_count,
            "entity_count": self.entity_count,
        }


class DuckDBCuratedStore:
    """Persist canonical portfolio records to DuckDB and Parquet sidecars."""

    def __init__(self, config: CuratedStorageConfig | None = None) -> None:
        self.config = config or CuratedStorageConfig()

    def persist_batch(self, batch: CuratedBatch) -> CuratedWriteResult:
        root = self.config.resolved_root()
        parquet_root = self.config.parquet_root
        root.mkdir(parents=True, exist_ok=True)
        parquet_root.mkdir(parents=True, exist_ok=True)

        with duckdb.connect(str(self.config.duckdb_path)) as connection:
            self._write_source_runs(connection, batch.source_runs)
            self._write_job_observations(connection, batch.job_observations)
            self._write_job_entities(connection, batch.job_entities)
            self._export_parquet(connection, parquet_root)

        return CuratedWriteResult(
            duckdb_path=self.config.duckdb_path,
            parquet_root=parquet_root,
            source_run_count=len(batch.source_runs),
            observation_count=len(batch.job_observations),
            entity_count=len(batch.job_entities),
        )

    @staticmethod
    def _write_source_runs(
        connection: duckdb.DuckDBPyConnection,
        source_runs: tuple[CanonicalSourceRunRecord, ...],
    ) -> None:
        connection.execute(
            """
            CREATE OR REPLACE TABLE source_runs (
                source_run_id VARCHAR,
                source_mode VARCHAR,
                observed_at_min DATE,
                observed_at_max DATE,
                upstream_root VARCHAR,
                observation_count INTEGER,
                job_count INTEGER,
                city_count INTEGER,
                status VARCHAR
            )
            """
        )
        if source_runs:
            connection.executemany(
                "INSERT INTO source_runs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    (
                        record.source_run_id,
                        record.source_mode,
                        record.observed_at_min,
                        record.observed_at_max,
                        str(record.upstream_root),
                        record.observation_count,
                        record.job_count,
                        record.city_count,
                        record.status,
                    )
                    for record in source_runs
                ],
            )

    @staticmethod
    def _write_job_observations(
        connection: duckdb.DuckDBPyConnection,
        observations: tuple[CanonicalObservationRecord, ...],
    ) -> None:
        connection.execute(
            """
            CREATE OR REPLACE TABLE job_observations (
                job_id VARCHAR,
                observed_at DATE,
                source_mode VARCHAR,
                city VARCHAR,
                title VARCHAR,
                state VARCHAR,
                country VARCHAR,
                reported_date DATE,
                source_run_id VARCHAR,
                remote_type VARCHAR,
                seniority_level VARCHAR,
                employment_type VARCHAR
            )
            """
        )
        if observations:
            connection.executemany(
                "INSERT INTO job_observations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    (
                        record.job_id,
                        record.observed_at,
                        record.source_mode,
                        record.city,
                        record.title,
                        record.state,
                        record.country,
                        record.reported_date,
                        record.source_run_id,
                        record.remote_type,
                        record.seniority_level,
                        record.employment_type,
                    )
                    for record in observations
                ],
            )

    @staticmethod
    def _write_job_entities(
        connection: duckdb.DuckDBPyConnection,
        entities: tuple[CanonicalEntityRecord, ...],
    ) -> None:
        connection.execute(
            """
            CREATE OR REPLACE TABLE job_entities (
                job_id VARCHAR,
                canonical_title VARCHAR,
                company_name VARCHAR,
                job_url VARCHAR,
                description_text VARCHAR,
                industry VARCHAR,
                english_required BOOLEAN,
                minimum_years_experience DOUBLE,
                tech_stack_json VARCHAR
            )
            """
        )
        if entities:
            connection.executemany(
                "INSERT INTO job_entities VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    (
                        record.job_id,
                        record.canonical_title,
                        record.company_name,
                        record.job_url,
                        record.description_text,
                        record.industry,
                        record.english_required,
                        record.minimum_years_experience,
                        json.dumps(list(record.tech_stack)),
                    )
                    for record in entities
                ],
            )

    @staticmethod
    def _export_parquet(connection: duckdb.DuckDBPyConnection, parquet_root: Path) -> None:
        for table_name in ("source_runs", "job_observations", "job_entities"):
            target = (parquet_root / f"{table_name}.parquet").as_posix()
            connection.execute(
                f"COPY {table_name} TO '{target}' (FORMAT PARQUET, OVERWRITE_OR_IGNORE TRUE)"
            )


def build_curated_batch(
    observations: list[CanonicalObservationRecord],
    entities: list[CanonicalEntityRecord],
    summary: IngestionRunSummary,
) -> CuratedBatch:
    """Build the canonical curated batch from adapter outputs."""

    grouped: dict[str, list[CanonicalObservationRecord]] = {}
    for observation in observations:
        source_run_id = observation.source_run_id or f"{summary.source_mode}-unscoped"
        grouped.setdefault(source_run_id, []).append(observation)

    source_runs: list[CanonicalSourceRunRecord] = []
    for source_run_id, records in sorted(grouped.items()):
        observed_dates = sorted(record.observed_at for record in records)
        source_runs.append(
            CanonicalSourceRunRecord(
                source_run_id=source_run_id,
                source_mode=records[0].source_mode,
                observed_at_min=observed_dates[0],
                observed_at_max=observed_dates[-1],
                upstream_root=summary.upstream_root,
                observation_count=len(records),
                job_count=len({record.job_id for record in records}),
                city_count=len({record.city for record in records}),
                status=summary.status,
            )
        )

    return CuratedBatch(
        source_runs=tuple(source_runs),
        job_observations=tuple(observations),
        job_entities=tuple(entities),
        summary=summary,
    )
