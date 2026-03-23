"""Public CSV projection helpers for Phase 2 report artifacts."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

from mexico_linkedin_jobs_portfolio.models import LatestJobRecord, PublicJobRecord

PUBLIC_CSV_FIELDNAMES = [
    "public_job_key",
    "title",
    "as_of_date",
    "city",
    "state",
    "remote_type",
    "seniority_level",
    "employment_type",
    "industry",
    "english_required",
    "min_years_experience",
    "tech_stack",
]


def build_public_job_records(
    latest_jobs: tuple[LatestJobRecord, ...],
    public_key_salt: str,
) -> tuple[PublicJobRecord, ...]:
    """Return the policy-safe public CSV projection for one report period."""

    return tuple(
        PublicJobRecord(
            public_job_key=_build_public_job_key(job.job_id, public_key_salt),
            title=job.title,
            as_of_date=job.observed_at,
            city=job.city,
            state=job.state,
            remote_type=job.remote_type,
            seniority_level=job.seniority_level,
            employment_type=job.employment_type,
            industry=job.industry,
            english_required=job.english_required,
            min_years_experience=job.minimum_years_experience,
            tech_stack=job.tech_stack,
        )
        for job in latest_jobs
    )


def write_public_csv(rows: tuple[PublicJobRecord, ...], path: Path) -> None:
    """Write the de-identified public CSV artifact."""

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=PUBLIC_CSV_FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow(row.to_csv_row())


def _build_public_job_key(job_id: str, public_key_salt: str) -> str:
    digest = hashlib.sha256(f"{public_key_salt}:{job_id}".encode()).hexdigest()
    return digest
