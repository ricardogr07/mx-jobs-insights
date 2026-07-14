"""Tests for the persistence layer: period enumeration and the narrative cache."""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

from mexico_linkedin_jobs_portfolio.analytics import (
    enumerate_closed_periods,
    resolve_closed_period,
)
from mexico_linkedin_jobs_portfolio.models import (
    GeneratedNarrative,
    PeriodWindow,
    ReportMetrics,
)
from mexico_linkedin_jobs_portfolio.reporting.narrative_cache import CachingNarrationClient


def test_enumerate_weekly_reaches_latest_and_is_consecutive() -> None:
    as_of = date(2026, 3, 30)
    first = date(2026, 3, 2)

    periods = enumerate_closed_periods("weekly", first, as_of_date=as_of)
    latest = resolve_closed_period("weekly", as_of)

    assert periods, "expected at least one closed weekly period"
    assert periods[-1].period_id == latest.period_id
    assert periods[-1].end_date == latest.end_date
    assert periods[0].start_date <= first <= periods[0].end_date
    for earlier, later in zip(periods, periods[1:], strict=False):
        assert later.start_date == earlier.start_date + timedelta(days=7)
    for window in periods:
        # The reference date must reproduce the same window through resolve_closed_period,
        # which is how the pipeline selects each period to regenerate.
        assert resolve_closed_period("weekly", window.reference_date).period_id == window.period_id


def test_enumerate_monthly_lists_every_closed_month() -> None:
    periods = enumerate_closed_periods("monthly", date(2026, 1, 20), as_of_date=date(2026, 4, 1))

    assert [window.period_id for window in periods] == ["2026-01", "2026-02", "2026-03"]
    for window in periods:
        assert resolve_closed_period("monthly", window.reference_date).period_id == window.period_id


def _metrics(job_count: int = 5) -> ReportMetrics:
    period = PeriodWindow(
        cadence="weekly",
        period_id="2026-W10",
        label="Week 10, 2026",
        start_date=date(2026, 3, 2),
        end_date=date(2026, 3, 8),
        reference_date=date(2026, 3, 9),
    )
    return ReportMetrics(
        period=period,
        observation_count=job_count,
        job_count=job_count,
        source_run_count=1,
        city_counts=(),
        remote_type_counts=(),
        seniority_counts=(),
        employment_type_counts=(),
        industry_counts=(),
        english_requirement_counts=(),
        experience_bucket_counts=(),
        tech_stack_counts=(),
        top_company_counts=(),
    )


class _CountingClient:
    def __init__(self) -> None:
        self.calls = 0

    def generate_bilingual_narrative(self, metrics: ReportMetrics) -> GeneratedNarrative:
        self.calls += 1
        return GeneratedNarrative(
            model="test",
            en_headline=f"headline-{self.calls}",
            en_bullets=("a", "b", "c"),
            es_headline="titular",
            es_bullets=("x", "y", "z"),
        )


def test_caching_client_reuses_committed_narrative_across_runs(tmp_path: Path) -> None:
    inner = _CountingClient()
    metrics = _metrics()

    first_run = CachingNarrationClient(inner=inner, cache_root=tmp_path)
    generated = first_run.generate_bilingual_narrative(metrics)
    assert inner.calls == 1
    assert (tmp_path / "weekly" / "2026-W10.json").is_file()

    # A fresh client models a later run: the committed cache is reused, no new OpenAI call.
    second_run = CachingNarrationClient(inner=inner, cache_root=tmp_path)
    reused = second_run.generate_bilingual_narrative(metrics)
    assert inner.calls == 1
    assert reused == generated


def test_caching_client_regenerates_when_metrics_change(tmp_path: Path) -> None:
    inner = _CountingClient()
    client = CachingNarrationClient(inner=inner, cache_root=tmp_path)

    client.generate_bilingual_narrative(_metrics(job_count=5))
    client.generate_bilingual_narrative(_metrics(job_count=99))

    assert inner.calls == 2
