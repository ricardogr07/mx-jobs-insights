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
