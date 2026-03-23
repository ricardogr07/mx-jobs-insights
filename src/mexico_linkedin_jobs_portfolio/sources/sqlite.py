"""SQLite source adapter for LinkedInWebScraper persisted scrape state."""

from __future__ import annotations

import json
import re
import sqlite3
from datetime import date, datetime
from typing import Any

from mexico_linkedin_jobs_portfolio.config import UpstreamWorkspaceConfig
from mexico_linkedin_jobs_portfolio.models import (
    CanonicalEntityRecord,
    CanonicalObservationRecord,
    IngestionRunSummary,
)
from mexico_linkedin_jobs_portfolio.sources.base import SourceAdapter

_REQUIRED_TABLES = frozenset({"scrape_runs", "jobs", "job_snapshots", "job_enrichments"})
_NUMBER_PATTERN = re.compile(r"\d+(?:\.\d+)?")

_SQLITE_LOAD_QUERY = """
SELECT
    js.run_id,
    js.job_id,
    js.snapshot_order,
    js.title AS snapshot_title,
    js.company AS snapshot_company,
    js.location AS snapshot_location,
    js.remote AS snapshot_remote,
    js.url AS snapshot_url,
    js.row_json,
    js.created_at AS snapshot_created_at,
    sr.position AS run_position,
    sr.location AS run_location,
    sr.started_at AS run_started_at,
    sr.finished_at AS run_finished_at,
    j.title AS job_title,
    j.company AS job_company,
    j.location AS job_location,
    j.url AS job_url,
    j.last_seen_at AS job_last_seen_at,
    je.short_description,
    je.tech_stack,
    je.years_of_experience,
    je.minimum_level_of_studies,
    je.english_requirement,
    je.openai_model,
    je.openai_response_id,
    je.raw_payload_json
FROM job_snapshots AS js
JOIN scrape_runs AS sr
    ON sr.id = js.run_id
LEFT JOIN jobs AS j
    ON j.job_id = js.job_id
LEFT JOIN job_enrichments AS je
    ON je.run_id = js.run_id AND je.job_id = js.job_id
ORDER BY COALESCE(sr.finished_at, sr.started_at, js.created_at), js.run_id, js.snapshot_order, js.job_id
"""


class SQLiteSourceAdapter(SourceAdapter):
    """Read LinkedInWebScraper SQLite state into canonical portfolio records."""

    mode = "sqlite"

    def is_available(self, workspace: UpstreamWorkspaceConfig) -> bool:
        return workspace.sqlite_path.is_file()

    def load(
        self,
        workspace: UpstreamWorkspaceConfig,
    ) -> tuple[list[CanonicalObservationRecord], list[CanonicalEntityRecord], IngestionRunSummary]:
        sqlite_path = workspace.sqlite_path
        if not sqlite_path.is_file():
            raise FileNotFoundError(f"SQLite source not found: {sqlite_path}")

        with sqlite3.connect(sqlite_path) as connection:
            connection.row_factory = sqlite3.Row
            missing_tables = self._missing_tables(connection)
            if missing_tables:
                raise RuntimeError(
                    "SQLite source is missing required tables: " + ", ".join(sorted(missing_tables))
                )
            rows = connection.execute(_SQLITE_LOAD_QUERY).fetchall()

        observations: list[CanonicalObservationRecord] = []
        entities_by_job_id: dict[str, CanonicalEntityRecord] = {}

        for row in rows:
            payload = parse_row_payload(row["row_json"])
            location_text = first_non_empty(
                row["snapshot_location"],
                row["job_location"],
                payload.get("Location"),
                row["run_location"],
            )
            city, state, country = split_location(location_text)
            reported_date = parse_date(payload.get("DatePosted"))
            observed_at = derive_observed_date(
                row["run_finished_at"],
                row["run_started_at"],
                row["snapshot_created_at"],
                reported_date,
            )

            observations.append(
                CanonicalObservationRecord(
                    job_id=row["job_id"],
                    observed_at=observed_at,
                    source_mode="sqlite",
                    city=city,
                    title=first_non_empty(
                        row["snapshot_title"], row["job_title"], payload.get("Title")
                    )
                    or "Unknown title",
                    state=state,
                    country=country,
                    reported_date=reported_date,
                    source_run_id=row["run_id"],
                    remote_type=normalize_text(
                        first_non_empty(row["snapshot_remote"], payload.get("Remote"))
                    ),
                    seniority_level=normalize_text(payload.get("SeniorityLevel")),
                    employment_type=normalize_text(payload.get("EmploymentType")),
                )
            )

            entity = CanonicalEntityRecord(
                job_id=row["job_id"],
                canonical_title=first_non_empty(
                    row["job_title"], row["snapshot_title"], payload.get("Title")
                )
                or "Unknown title",
                company_name=normalize_text(
                    first_non_empty(
                        row["job_company"], row["snapshot_company"], payload.get("Company")
                    )
                ),
                job_url=normalize_text(
                    first_non_empty(row["job_url"], row["snapshot_url"], payload.get("Url"))
                ),
                description_text=normalize_text(
                    first_non_empty(payload.get("Description"), row["short_description"])
                ),
                industry=normalize_text(payload.get("Industries")),
                english_required=parse_boolish(
                    first_non_empty(row["english_requirement"], payload.get("English"))
                ),
                minimum_years_experience=parse_first_float(
                    first_non_empty(
                        payload.get("MinYoE"), row["years_of_experience"], payload.get("YoE")
                    )
                ),
                tech_stack=parse_tech_stack(
                    first_non_empty(row["tech_stack"], payload.get("TechStack"))
                ),
            )
            entities_by_job_id[row["job_id"]] = entity

        notes = [
            f"Loaded {len(observations)} job snapshot rows from SQLite.",
            "Entity projection keeps the latest ordered row per job ID.",
        ]
        if observations:
            notes.append(
                f"Observed date range spans {observations[0].observed_at.isoformat()} to {observations[-1].observed_at.isoformat()}."
            )

        summary = IngestionRunSummary(
            command_name="sqlite_adapter",
            source_mode="sqlite",
            upstream_root=workspace.resolved_root(),
            dry_run=True,
            resolved_source_mode="sqlite",
            observation_count=len(observations),
            entity_count=len(entities_by_job_id),
            status="sqlite_loaded",
            notes=tuple(notes),
        )
        return observations, list(entities_by_job_id.values()), summary

    @staticmethod
    def _missing_tables(connection: sqlite3.Connection) -> set[str]:
        rows = connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
        available = {row[0] for row in rows}
        return set(_REQUIRED_TABLES) - available


def parse_row_payload(raw_payload: str | None) -> dict[str, Any]:
    if not raw_payload:
        return {}
    try:
        payload = json.loads(raw_payload)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def first_non_empty(*values: Any) -> str | None:
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return None


def normalize_text(value: Any) -> str | None:
    text = first_non_empty(value)
    return text if text is not None else None


def parse_datetime(value: Any) -> datetime | None:
    text = normalize_text(value)
    if text is None:
        return None
    candidate = text.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(candidate)
    except ValueError:
        pass
    if " " in candidate:
        try:
            return datetime.fromisoformat(candidate.replace(" ", "T", 1))
        except ValueError:
            return None
    return None


def parse_date(value: Any) -> date | None:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    parsed_datetime = parse_datetime(value)
    if parsed_datetime is not None:
        return parsed_datetime.date()
    text = normalize_text(value)
    if text is None:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def derive_observed_date(
    finished_at: Any,
    started_at: Any,
    created_at: Any,
    reported_date: date | None,
) -> date:
    for candidate in (finished_at, started_at, created_at):
        parsed = parse_date(candidate)
        if parsed is not None:
            return parsed
    if reported_date is not None:
        return reported_date
    raise RuntimeError("Could not derive an observation date from the SQLite snapshot data.")


def split_location(location_text: str | None) -> tuple[str, str | None, str]:
    text = normalize_text(location_text)
    if text is None:
        return ("Unknown", None, "Mexico")

    parts = [part.strip() for part in text.split(",") if part.strip()]
    if len(parts) >= 3:
        return (parts[0], ", ".join(parts[1:-1]) or None, parts[-1])
    if len(parts) == 2:
        if parts[1].casefold() in {"mexico", "méxico"}:
            return (parts[0], None, "Mexico")
        return (parts[0], parts[1], "Mexico")
    return (parts[0], None, "Mexico")


def parse_boolish(value: Any) -> bool | None:
    text = normalize_text(value)
    if text is None:
        return None
    lowered = text.casefold()
    if lowered in {"yes", "true", "1", "required"}:
        return True
    if lowered in {"no", "false", "0", "not required"}:
        return False
    return None


def parse_first_float(value: Any) -> float | None:
    text = normalize_text(value)
    if text is None:
        return None
    match = _NUMBER_PATTERN.search(text)
    return float(match.group(0)) if match else None


def parse_tech_stack(value: Any) -> tuple[str, ...]:
    text = normalize_text(value)
    if text is None:
        return ()
    if text.startswith("["):
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, list):
            tokens = [normalize_text(item) for item in parsed]
            return tuple(token for token in tokens if token)
    normalized = text.replace(";", ",")
    tokens = [part.strip() for part in normalized.split(",") if part.strip()]
    return tuple(tokens)
