"""Tests for the persistence layer: period enumeration and the narrative cache."""

from __future__ import annotations

import json
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
from mexico_linkedin_jobs_portfolio.reporting.narrative_cache import (
    CachingNarrationClient,
    metrics_cache_key,
    narrative_to_dict,
)


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

    first_run = CachingNarrationClient(inner=inner, cache_root=tmp_path, provider="openai")
    generated = first_run.generate_bilingual_narrative(metrics)
    assert inner.calls == 1
    # entries are namespaced by provider, never written to the legacy location
    assert (tmp_path / "openai" / "weekly" / "2026-W10.json").is_file()
    assert not (tmp_path / "weekly" / "2026-W10.json").exists()

    # A fresh client models a later run: the committed cache is reused, no new provider call.
    second_run = CachingNarrationClient(inner=inner, cache_root=tmp_path, provider="openai")
    reused = second_run.generate_bilingual_narrative(metrics)
    assert inner.calls == 1
    assert reused == generated


def test_caching_client_regenerates_when_metrics_change(tmp_path: Path) -> None:
    inner = _CountingClient()
    client = CachingNarrationClient(inner=inner, cache_root=tmp_path, provider="openai")

    client.generate_bilingual_narrative(_metrics(job_count=5))
    client.generate_bilingual_narrative(_metrics(job_count=99))

    assert inner.calls == 2


def test_caching_client_regenerates_when_the_provider_changes(tmp_path: Path) -> None:
    inner = _CountingClient()
    metrics = _metrics()

    openai_narrative = CachingNarrationClient(
        inner=inner, cache_root=tmp_path, provider="openai"
    ).generate_bilingual_narrative(metrics)
    assert inner.calls == 1

    # Switching providers must reach the wrapped client instead of republishing the
    # other provider's text, which is the only way a provider switch gets verified.
    anthropic_client = CachingNarrationClient(
        inner=inner, cache_root=tmp_path, provider="anthropic"
    )
    anthropic_narrative = anthropic_client.generate_bilingual_narrative(metrics)

    assert inner.calls == 2
    assert anthropic_client.hits == 0
    assert anthropic_narrative != openai_narrative
    assert (tmp_path / "anthropic" / "weekly" / "2026-W10.json").is_file()
    assert (tmp_path / "openai" / "weekly" / "2026-W10.json").is_file()


def test_caching_client_reads_legacy_entries_for_the_default_provider(tmp_path: Path) -> None:
    inner = _CountingClient()
    metrics = _metrics()

    # A pre-namespace entry, as committed by earlier runs.
    legacy_path = tmp_path / "weekly" / "2026-W10.json"
    legacy_path.parent.mkdir(parents=True, exist_ok=True)
    legacy_path.write_text(
        json.dumps(
            {
                "metrics_hash": metrics_cache_key(metrics),
                "narrative": narrative_to_dict(
                    GeneratedNarrative(
                        model="legacy",
                        en_headline="legacy headline",
                        en_bullets=("a", "b", "c"),
                        es_headline="titular heredado",
                        es_bullets=("x", "y", "z"),
                    )
                ),
            }
        ),
        encoding="utf-8",
    )

    openai_client = CachingNarrationClient(inner=inner, cache_root=tmp_path, provider="openai")
    reused = openai_client.generate_bilingual_narrative(metrics)

    assert inner.calls == 0
    assert openai_client.hits == 1
    assert reused.model == "legacy"

    # A different provider must not inherit the legacy entry.
    anthropic_client = CachingNarrationClient(
        inner=inner, cache_root=tmp_path, provider="anthropic"
    )
    anthropic_client.generate_bilingual_narrative(metrics)

    assert inner.calls == 1
    assert anthropic_client.hits == 0
