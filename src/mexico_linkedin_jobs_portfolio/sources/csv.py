"""CSV source adapter for LinkedInWebScraper exported job files."""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from mexico_linkedin_jobs_portfolio.config import UpstreamWorkspaceConfig
from mexico_linkedin_jobs_portfolio.models import (
    CanonicalEntityRecord,
    CanonicalObservationRecord,
    IngestionRunSummary,
)
from mexico_linkedin_jobs_portfolio.sources.base import SourceAdapter
from mexico_linkedin_jobs_portfolio.sources.sqlite import (
    first_non_empty,
    normalize_text,
    parse_boolish,
    parse_date,
    parse_first_float,
    parse_tech_stack,
    split_location,
)

_REQUIRED_COLUMNS = frozenset({"Title", "Location", "DatePosted", "JobID"})
_DATE_DIR_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")


@dataclass(frozen=True, slots=True)
class CsvSourceFile:
    """Describe one CSV file and the observation date inferred for it."""

    path: Path
    observation_date: date
    relative_label: str
    derived_from_dated_directory: bool


class CsvSourceAdapter(SourceAdapter):
    """Read LinkedInWebScraper CSV exports into canonical portfolio records."""

    mode = "csv"

    def is_available(self, workspace: UpstreamWorkspaceConfig) -> bool:
        return bool(discover_csv_files(workspace))

    def load(
        self,
        workspace: UpstreamWorkspaceConfig,
    ) -> tuple[list[CanonicalObservationRecord], list[CanonicalEntityRecord], IngestionRunSummary]:
        source_files = discover_csv_files(workspace)
        if not source_files:
            raise FileNotFoundError(f"CSV source not found under {workspace.exports_path}")

        observations_by_key: dict[tuple[str, date, str], CanonicalObservationRecord] = {}
        entities_by_job_id: dict[str, CanonicalEntityRecord] = {}
        duplicate_rows = 0
        latest_fallback_files = 0
        rows_loaded = 0

        for source_file in source_files:
            if not source_file.derived_from_dated_directory:
                latest_fallback_files += 1

            with source_file.path.open("r", encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                fieldnames = reader.fieldnames or []
                missing = _REQUIRED_COLUMNS - set(fieldnames)
                if missing:
                    missing_text = ", ".join(sorted(missing))
                    raise RuntimeError(
                        f"CSV source {source_file.path} is missing required columns: {missing_text}"
                    )

                for row_index, row in enumerate(reader, start=1):
                    rows_loaded += 1
                    payload = {key: value for key, value in row.items() if key}
                    job_id = require_value(payload, "JobID", source_file.path, row_index)
                    title = require_value(payload, "Title", source_file.path, row_index)
                    location_text = require_value(payload, "Location", source_file.path, row_index)
                    reported_date_text = require_value(
                        payload, "DatePosted", source_file.path, row_index
                    )

                    city, state, country = split_location(location_text)
                    reported_date = parse_date(reported_date_text)
                    observation_key = (job_id, source_file.observation_date, city)
                    if observation_key in observations_by_key:
                        duplicate_rows += 1
                        continue

                    observations_by_key[observation_key] = CanonicalObservationRecord(
                        job_id=job_id,
                        observed_at=source_file.observation_date,
                        source_mode="csv",
                        city=city,
                        title=title,
                        state=state,
                        country=country,
                        reported_date=reported_date,
                        source_run_id=source_file.relative_label,
                        remote_type=normalize_text(payload.get("Remote")),
                        seniority_level=normalize_text(payload.get("SeniorityLevel")),
                        employment_type=normalize_text(payload.get("EmploymentType")),
                    )

                    entities_by_job_id[job_id] = CanonicalEntityRecord(
                        job_id=job_id,
                        canonical_title=title,
                        company_name=normalize_text(payload.get("Company")),
                        job_url=normalize_text(payload.get("Url")),
                        description_text=normalize_text(
                            first_non_empty(
                                payload.get("Description"), payload.get("ShortDescription")
                            )
                        ),
                        industry=normalize_text(payload.get("Industries")),
                        english_required=parse_boolish(payload.get("English")),
                        minimum_years_experience=parse_first_float(
                            first_non_empty(payload.get("MinYoE"), payload.get("YoE"))
                        ),
                        tech_stack=parse_tech_stack(payload.get("TechStack")),
                    )

        observations = list(observations_by_key.values())
        notes = [
            f"Loaded {rows_loaded} CSV rows across {len(source_files)} files.",
            f"Deduplicated {duplicate_rows} repeated job observations by job/date/city.",
        ]
        if latest_fallback_files:
            notes.append(
                f"Used file modification timestamps for {latest_fallback_files} latest-export file(s) without dated folder context."
            )
        if observations:
            observed_dates = sorted({observation.observed_at for observation in observations})
            notes.append(
                f"Observed date range spans {observed_dates[0].isoformat()} to {observed_dates[-1].isoformat()}."
            )

        summary = IngestionRunSummary(
            command_name="csv_adapter",
            source_mode="csv",
            upstream_root=workspace.resolved_root(),
            dry_run=True,
            resolved_source_mode="csv",
            observation_count=len(observations),
            entity_count=len(entities_by_job_id),
            status="csv_loaded",
            notes=tuple(notes),
        )
        return observations, list(entities_by_job_id.values()), summary


def discover_csv_files(workspace: UpstreamWorkspaceConfig) -> list[CsvSourceFile]:
    """Return the ordered CSV files to ingest from the exports workspace."""

    exports_root = workspace.exports_path
    if not exports_root.is_dir():
        return []

    files: list[CsvSourceFile] = []
    for directory in sorted(exports_root.iterdir()):
        if not directory.is_dir() or not _DATE_DIR_PATTERN.fullmatch(directory.name):
            continue
        observation_date = date.fromisoformat(directory.name)
        for csv_path in sorted(directory.glob("*.csv")):
            files.append(
                CsvSourceFile(
                    path=csv_path,
                    observation_date=observation_date,
                    relative_label=f"exports/{directory.name}/{csv_path.name}",
                    derived_from_dated_directory=True,
                )
            )

    latest_dir = exports_root / "latest"
    if latest_dir.is_dir():
        for csv_path in sorted(latest_dir.glob("*.csv")):
            observed_at = datetime.fromtimestamp(csv_path.stat().st_mtime).date()
            files.append(
                CsvSourceFile(
                    path=csv_path,
                    observation_date=observed_at,
                    relative_label=f"exports/latest/{csv_path.name}",
                    derived_from_dated_directory=False,
                )
            )
    return files


def require_value(row: dict[str, str], column: str, path: Path, row_index: int) -> str:
    """Return a required CSV value or raise a descriptive error."""

    value = normalize_text(row.get(column))
    if value is None:
        raise RuntimeError(f"CSV source {path} has an empty {column!r} value at row {row_index}.")
    return value
