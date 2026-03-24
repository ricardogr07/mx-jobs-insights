"""
Backfill historical reports (W01-W11 2026 and Jan-Feb 2026 monthly) with correct date filtering.

This script generates reports filtered by Posted On date (reported_date) instead of
observation date. This is necessary because the source data from 2026-01-14 onwards was
loaded in a single snapshot on 2026-03-23, so all jobs need to be distributed to their
correct reporting periods based on when they were posted.

Usage:
    python scripts/backfill_historical_reports.py

The script will:
1. Generate weekly reports for ISO weeks W01 through W11 (2026-01-06 through 2026-03-15)
2. Generate monthly reports for 2026-01 and 2026-02
3. Regenerate the current W12 report with correct filtering

Each report will use --filter-by-posted-date to ensure jobs are bucketed by their
Posted On date, not when they were re-observed.
"""

from __future__ import annotations

import subprocess
import sys
from datetime import date

# Weekly periods to backfill (W01-W11)
# Each tuple is (end_of_week_date, week_id)
WEEKLY_BACKFILLS = [
    (date(2026, 1, 12), "2026-W02"),  # W01 ends 2026-01-12 but is ISO W02
    (date(2026, 1, 19), "2026-W03"),
    (date(2026, 1, 26), "2026-W04"),
    (date(2026, 2, 2), "2026-W05"),
    (date(2026, 2, 9), "2026-W06"),
    (date(2026, 2, 16), "2026-W07"),
    (date(2026, 2, 23), "2026-W08"),
    (date(2026, 3, 2), "2026-W09"),
    (date(2026, 3, 9), "2026-W10"),
    (date(2026, 3, 16), "2026-W11"),
]

# Monthly periods to backfill
# Each tuple is (end_of_month_date, month_id)
MONTHLY_BACKFILLS = [
    (date(2026, 2, 1), "2026-01"),  # Jan 2026
    (date(2026, 3, 1), "2026-02"),  # Feb 2026
]

# Current period to regenerate (W12 with proper filtering)
CURRENT_WEEKLY = (date(2026, 3, 23), "2026-W12")


def run_report_command(cadence: str, as_of_date: date, filter_by_posted_date: bool = True) -> int:
    """Execute a report generation command."""
    cmd = [
        sys.executable,
        "-m",
        "mexico_linkedin_jobs_portfolio",
        "report",
        "--cadence",
        cadence,
        "--as-of",
        as_of_date.isoformat(),
    ]
    if filter_by_posted_date:
        cmd.append("--filter-by-posted-date")

    print(f"\n{'='*80}")
    print(f"Running: {' '.join(cmd)}")
    print(f"{'='*80}")

    result = subprocess.run(cmd)
    return result.returncode


def main() -> int:
    """Execute all backfill reports."""
    print("Starting historical report backfill with Posted On date filtering...")
    print(f"\nTotal operations: {len(WEEKLY_BACKFILLS)} weekly + {len(MONTHLY_BACKFILLS)} monthly + 1 current")

    failed_reports = []

    # Run weekly backfills
    print("\n" + "=" * 80)
    print("WEEKLY BACKFILLS (W01-W11)")
    print("=" * 80)
    for as_of_date, week_id in WEEKLY_BACKFILLS:
        result = run_report_command("weekly", as_of_date)
        if result != 0:
            failed_reports.append(f"weekly:{week_id}@{as_of_date}")

    # Run monthly backfills
    print("\n" + "=" * 80)
    print("MONTHLY BACKFILLS (Jan-Feb 2026)")
    print("=" * 80)
    for as_of_date, month_id in MONTHLY_BACKFILLS:
        result = run_report_command("monthly", as_of_date)
        if result != 0:
            failed_reports.append(f"monthly:{month_id}@{as_of_date}")

    # Regenerate current W12
    print("\n" + "=" * 80)
    print("REGENERATE CURRENT WEEK (W12 with proper date filtering)")
    print("=" * 80)
    as_of_date, week_id = CURRENT_WEEKLY
    result = run_report_command("weekly", as_of_date)
    if result != 0:
        failed_reports.append(f"weekly:{week_id}@{as_of_date}")

    # Summary
    print("\n" + "=" * 80)
    print("BACKFILL SUMMARY")
    print("=" * 80)
    total = len(WEEKLY_BACKFILLS) + len(MONTHLY_BACKFILLS) + 1
    if failed_reports:
        print(f"[FAILED] {len(failed_reports)} of {total} reports failed:")
        for report in failed_reports:
            print(f"   - {report}")
        return 1
    else:
        print(f"[SUCCESS] All {total} reports completed successfully!")
        print("\nNext steps:")
        print("1. Verify the generated reports look correct visually")
        print("2. Run 'mkdocs build' to regenerate the site with new report content")
        print("3. Push the updated artifacts and site to the repository")
        print("\nFuture reports (starting Monday next week) will use normal filtering by observation date.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
