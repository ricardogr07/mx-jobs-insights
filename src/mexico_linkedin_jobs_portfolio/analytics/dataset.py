"""Curated DuckDB/Parquet readers used by the reporting pipeline."""

from __future__ import annotations

import json
from dataclasses import dataclass

import duckdb

from mexico_linkedin_jobs_portfolio.config import CuratedStorageConfig

_JOIN_QUERY = """
SELECT
    o.job_id,
    o.observed_at,
    COALESCE(e.canonical_title, o.title) AS title,
    o.city,
    o.state,
    o.country,
    o.source_run_id,
    o.remote_type,
    o.seniority_level,
    o.employment_type,
    e.company_name,
    e.job_url,
    e.description_text,
    e.industry,
    e.english_required,
    e.minimum_years_experience,
    e.tech_stack_json
FROM {observations_source} AS o
LEFT JOIN {entities_source} AS e
    ON e.job_id = o.job_id
ORDER BY o.observed_at, o.job_id, COALESCE(o.source_run_id, '')
"""


@dataclass(frozen=True, slots=True)
class JoinedObservationRecord:
    """Joined observation/entity row used for Phase 2 metrics and Phase 3 views."""

    job_id: str
    observed_at: object
    title: str
    city: str
    state: str | None
    country: str
    source_run_id: str | None
    remote_type: str | None
    seniority_level: str | None
    employment_type: str | None
    company_name: str | None
    job_url: str | None
    description_text: str | None
    industry: str | None
    english_required: bool | None
    minimum_years_experience: float | None
    tech_stack: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CuratedDataset:
    """Resolved curated rows plus the storage surface that supplied them."""

    records: tuple[JoinedObservationRecord, ...]
    storage_mode: str


class CuratedDatasetReader:
    """Read the curated canonical data from DuckDB, falling back to Parquet."""

    def load(self, config: CuratedStorageConfig) -> CuratedDataset:
        duckdb_path = config.duckdb_path
        if duckdb_path.is_file():
            return CuratedDataset(
                records=self._load_records(
                    duckdb_path=str(duckdb_path),
                    observations_source="job_observations",
                    entities_source="job_entities",
                ),
                storage_mode="duckdb",
            )

        parquet_root = config.parquet_root
        observations_parquet = parquet_root / "job_observations.parquet"
        entities_parquet = parquet_root / "job_entities.parquet"
        if observations_parquet.is_file() and entities_parquet.is_file():
            return CuratedDataset(
                records=self._load_records(
                    duckdb_path=":memory:",
                    observations_source=f"read_parquet('{observations_parquet.as_posix()}')",
                    entities_source=f"read_parquet('{entities_parquet.as_posix()}')",
                ),
                storage_mode="parquet",
            )

        raise FileNotFoundError(
            "Curated report input not found. Expected either "
            f"{duckdb_path} or Parquet sidecars under {parquet_root}."
        )

    @staticmethod
    def _load_records(
        *, duckdb_path: str, observations_source: str, entities_source: str
    ) -> tuple[JoinedObservationRecord, ...]:
        query = _JOIN_QUERY.format(
            observations_source=observations_source,
            entities_source=entities_source,
        )
        with duckdb.connect(duckdb_path) as connection:
            rows = connection.execute(query).fetchall()

        return tuple(
            JoinedObservationRecord(
                job_id=row[0],
                observed_at=row[1],
                title=row[2],
                city=row[3],
                state=row[4],
                country=row[5],
                source_run_id=row[6],
                remote_type=row[7],
                seniority_level=row[8],
                employment_type=row[9],
                company_name=row[10],
                job_url=row[11],
                description_text=row[12],
                industry=row[13],
                english_required=row[14],
                minimum_years_experience=row[15],
                tech_stack=_parse_tech_stack_json(row[16]),
            )
            for row in rows
        )


def _parse_tech_stack_json(value: str | None) -> tuple[str, ...]:
    if not value:
        return ()
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return ()
    if not isinstance(parsed, list):
        return ()
    return tuple(str(item) for item in parsed if str(item).strip())
