"""Closed reporting-period helpers for weekly and monthly cadences."""

from __future__ import annotations

from datetime import date, timedelta

from mexico_linkedin_jobs_portfolio.config import ReportCadence
from mexico_linkedin_jobs_portfolio.models import PeriodWindow


def resolve_reference_date(as_of_date: date | None) -> date:
    """Return the explicit as-of date or today's date when omitted."""

    return as_of_date or date.today()


def resolve_closed_period(cadence: ReportCadence, as_of_date: date | None = None) -> PeriodWindow:
    """Return the latest completed ISO week or calendar month."""

    reference_date = resolve_reference_date(as_of_date)
    if cadence == "weekly":
        current_week_start = reference_date - timedelta(days=reference_date.isoweekday() - 1)
        end_date = current_week_start - timedelta(days=1)
        start_date = end_date - timedelta(days=end_date.isoweekday() - 1)
        iso_year, iso_week, _ = end_date.isocalendar()
        return PeriodWindow(
            cadence="weekly",
            period_id=f"{iso_year}-W{iso_week:02d}",
            label=f"Week {iso_week}, {iso_year}",
            start_date=start_date,
            end_date=end_date,
            reference_date=reference_date,
        )

    first_of_current_month = reference_date.replace(day=1)
    end_date = first_of_current_month - timedelta(days=1)
    start_date = end_date.replace(day=1)
    return PeriodWindow(
        cadence="monthly",
        period_id=f"{start_date:%Y-%m}",
        label=f"{start_date:%B %Y}",
        start_date=start_date,
        end_date=end_date,
        reference_date=reference_date,
    )


def _first_of_next_month(day: date) -> date:
    """Return the first day of the month after the one containing ``day``."""

    if day.month == 12:
        return date(day.year + 1, 1, 1)
    return date(day.year, day.month + 1, 1)


def enumerate_closed_periods(
    cadence: ReportCadence, first_date: date, as_of_date: date | None = None
) -> list[PeriodWindow]:
    """Return every closed period from the one containing ``first_date`` to the latest.

    Each period's ``reference_date`` is the day after its end (the next Monday for
    weekly, the first of the next month for monthly), so passing it back through
    ``resolve_closed_period`` reproduces the same window. This is what the pipeline
    iterates to rebuild the full archive from source on every run.
    """

    latest = resolve_closed_period(cadence, as_of_date)
    periods: list[PeriodWindow] = []

    if cadence == "weekly":
        week_start = first_date - timedelta(days=first_date.isoweekday() - 1)
        while week_start <= latest.start_date:
            end_date = week_start + timedelta(days=6)
            iso_year, iso_week, _ = end_date.isocalendar()
            periods.append(
                PeriodWindow(
                    cadence="weekly",
                    period_id=f"{iso_year}-W{iso_week:02d}",
                    label=f"Week {iso_week}, {iso_year}",
                    start_date=week_start,
                    end_date=end_date,
                    reference_date=week_start + timedelta(days=7),
                )
            )
            week_start += timedelta(days=7)
        return periods

    month_start = first_date.replace(day=1)
    while month_start <= latest.start_date:
        next_month = _first_of_next_month(month_start)
        periods.append(
            PeriodWindow(
                cadence="monthly",
                period_id=f"{month_start:%Y-%m}",
                label=f"{month_start:%B %Y}",
                start_date=month_start,
                end_date=next_month - timedelta(days=1),
                reference_date=next_month,
            )
        )
        month_start = next_month
    return periods
