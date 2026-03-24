"""Aggregate KPI builders."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from mexico_linkedin_jobs_portfolio.analytics.dataset import JoinedObservationRecord
from mexico_linkedin_jobs_portfolio.models import (
    DimensionCount,
    LatestJobRecord,
    PeriodWindow,
    ReportMetrics,
)

_UNKNOWN = "Unknown"


@dataclass(frozen=True, slots=True)
class MetricsBuildResult:
    """Aggregate metrics plus the latest-per-job rows for one period."""

    metrics: ReportMetrics
    latest_jobs: tuple[LatestJobRecord, ...]


def build_report_metrics(
    records: tuple[JoinedObservationRecord, ...],
    period: PeriodWindow,
    filter_by_posted_date: bool = False,
) -> MetricsBuildResult:
    """Build one aggregate report payload from the selected reporting period.
    
    If filter_by_posted_date is True, uses reported_date (Posted On) for filtering.
    Otherwise uses observed_at (when the job was scraped).
    """

    date_field = "reported_date" if filter_by_posted_date else "observed_at"
    period_records = tuple(
        record
        for record in records
        if period.start_date <= getattr(record, date_field) <= period.end_date
    )
    latest_jobs = _select_latest_jobs(period_records)

    metrics = ReportMetrics(
        period=period,
        observation_count=len(period_records),
        job_count=len(latest_jobs),
        source_run_count=len(
            {record.source_run_id for record in period_records if record.source_run_id}
        ),
        city_counts=_count_labels((job.city for job in latest_jobs), unknown_label=_UNKNOWN),
        remote_type_counts=_count_labels(
            (job.remote_type for job in latest_jobs),
            unknown_label=_UNKNOWN,
        ),
        seniority_counts=_count_labels(
            (job.seniority_level for job in latest_jobs),
            unknown_label=_UNKNOWN,
        ),
        employment_type_counts=_count_labels(
            (job.employment_type for job in latest_jobs),
            unknown_label=_UNKNOWN,
        ),
        industry_counts=_count_labels(
            (job.industry for job in latest_jobs),
            unknown_label=_UNKNOWN,
        ),
        english_requirement_counts=_count_labels(
            (_english_label(job.english_required) for job in latest_jobs),
            unknown_label=_UNKNOWN,
        ),
        experience_bucket_counts=_count_labels(
            (_experience_bucket(job.minimum_years_experience) for job in latest_jobs),
            unknown_label=_UNKNOWN,
        ),
        tech_stack_counts=_count_labels(
            (token for job in latest_jobs for token in job.tech_stack),
            unknown_label=_UNKNOWN,
            top_n=10,
        ),
        top_company_counts=_count_labels(
            (job.company_name for job in latest_jobs if job.company_name),
            unknown_label=_UNKNOWN,
            top_n=10,
        ),
    )
    return MetricsBuildResult(metrics=metrics, latest_jobs=latest_jobs)


def _select_latest_jobs(records: tuple[JoinedObservationRecord, ...]) -> tuple[LatestJobRecord, ...]:
    grouped: dict[str, list[JoinedObservationRecord]] = {}
    for record in records:
        grouped.setdefault(record.job_id, []).append(record)

    latest_rows: list[LatestJobRecord] = []
    for job_id, job_records in sorted(grouped.items()):
        latest = max(
            job_records,
            key=lambda record: (record.observed_at, record.source_run_id or "", record.title),
        )
        latest_rows.append(
            LatestJobRecord(
                job_id=job_id,
                observed_at=latest.observed_at,
                title=latest.title,
                city=latest.city,
                state=latest.state,
                country=latest.country,
                remote_type=latest.remote_type,
                seniority_level=latest.seniority_level,
                employment_type=latest.employment_type,
                industry=latest.industry,
                english_required=latest.english_required,
                minimum_years_experience=latest.minimum_years_experience,
                tech_stack=latest.tech_stack,
                company_name=latest.company_name,
                job_url=latest.job_url,
                description_text=latest.description_text,
            )
        )

    return tuple(
        sorted(latest_rows, key=lambda record: (-record.observed_at.toordinal(), record.job_id))
    )


def _count_labels(
    values,
    *,
    unknown_label: str,
    top_n: int | None = None,
) -> tuple[DimensionCount, ...]:
    counts: Counter[str] = Counter()
    for value in values:
        label = str(value).strip() if value is not None and str(value).strip() else unknown_label
        counts[label] += 1

    ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0].casefold()))
    if top_n is not None:
        ordered = ordered[:top_n]
    return tuple(DimensionCount(label=label, count=count) for label, count in ordered)


def _english_label(value: bool | None) -> str:
    if value is True:
        return "Required"
    if value is False:
        return "Not required"
    return _UNKNOWN


def _experience_bucket(value: float | None) -> str:
    if value is None:
        return _UNKNOWN
    if value <= 1:
        return "0-1 years"
    if value <= 3:
        return "2-3 years"
    if value <= 5:
        return "4-5 years"
    return "6+ years"

