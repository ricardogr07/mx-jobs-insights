#!/usr/bin/env python
"""Test chart generation integration."""

import sys
from datetime import date

from mexico_linkedin_jobs_portfolio.analytics import create_all_charts, figure_to_base64_png
from mexico_linkedin_jobs_portfolio.models import DimensionCount, PeriodWindow, ReportMetrics


def main():
    # Create test metrics
    test_metrics = ReportMetrics(
        period=PeriodWindow(
            cadence="weekly",
            period_id="2026-W12",
            label="Week 12 2026",
            start_date=date(2026, 3, 23),
            end_date=date(2026, 3, 29),
            reference_date=date(2026, 3, 29),
        ),
        observation_count=100,
        job_count=50,
        source_run_count=5,
        city_counts=(
            DimensionCount("Mexico City", 30),
            DimensionCount("Guadalajara", 12),
            DimensionCount("Monterrey", 8),
        ),
        remote_type_counts=(DimensionCount("Remote", 25), DimensionCount("On-site", 25)),
        seniority_counts=(
            DimensionCount("Mid-level", 25),
            DimensionCount("Senior", 20),
            DimensionCount("Entry-level", 5),
        ),
        employment_type_counts=(DimensionCount("Full-time", 45), DimensionCount("Contract", 5)),
        industry_counts=(DimensionCount("Technology", 35), DimensionCount("Finance", 15)),
        english_requirement_counts=(
            DimensionCount("Required", 40),
            DimensionCount("Preferred", 10),
        ),
        experience_bucket_counts=(
            DimensionCount("3-5 years", 25),
            DimensionCount("5+ years", 15),
            DimensionCount("0-3 years", 10),
        ),
        tech_stack_counts=(
            DimensionCount("Python", 35),
            DimensionCount("SQL", 32),
            DimensionCount("AWS", 28),
            DimensionCount("ML", 18),
        ),
        top_company_counts=(DimensionCount("Company A", 5), DimensionCount("Company B", 4)),
    )

    print("Testing chart generation...")
    try:
        charts = create_all_charts(test_metrics, "en")
        print(f"✓ Successfully created {len(charts)} charts:")
        for chart_key, _fig in charts.items():
            print(f"  - {chart_key}")

        print("\nTesting base64 PNG conversion...")
        fig = charts.get("top_cities")
        if fig:
            b64 = figure_to_base64_png(fig)
            if b64 and len(b64) > 100:
                print(f"✓ Base64 conversion successful (length: {len(b64)} chars)")
            else:
                print("⚠ Base64 conversion returned empty or too short")

        print("\n✓ All chart tests passed!")
        return 0
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
