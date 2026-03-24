# Historical Report Backfill Guide

## Problem & Solution

The pipeline loaded all historical job data (posted since 2026-01-14) in a single snapshot on 2026-03-23. All jobs were grouped into the W12 2026 report based on their **observation date** (when scraped) rather than their **Posted On date**.

This backfill regenerates reports for past weeks and months, filtering jobs correctly by their **Posted On date** (job posting date) to distribute them across the appropriate reporting periods.

## What Gets Backfilled

| Period | Type | as_of_date | Description |
|--------|------|-----------|-------------|
| 2026-W02 through 2026-W11 | Weekly | Each Tuesday of the period | Historical weeks with data |
| 2026-01 | Monthly | 2026-02-01 | January 2026 monthly report |
| 2026-02 | Monthly | 2026-03-01 | February 2026 monthly report |
| 2026-W12 | Weekly | 2026-03-23 | Current week, regenerated correctly |

**Total: 12 reports** (10 weekly + 2 monthly + current week)

## Running the Backfill

### Option 1: Automated Script (Recommended)

```bash
python scripts/backfill_historical_reports.py
```

This script will:
1. Run all weekly backfills (W02-W11)
2. Run monthly backfills (Jan-Feb)
3. Regenerate the current week (W12)
4. Report success/failure for each

### Option 2: Manual Individual Reports

Run each report individually with the `--filter-by-posted-date` flag:

**Weekly Example:**
```bash
python -m mexico_linkedin_jobs_portfolio report \
  --cadence weekly \
  --as-of 2026-01-13 \
  --filter-by-posted-date
```

**Monthly Example:**
```bash
python -m mexico_linkedin_jobs_portfolio report \
  --cadence monthly \
  --as-of 2026-02-01 \
  --filter-by-posted-date
```

## Understanding the Flag

The `--filter-by-posted-date` flag changes the filtering behavior:

**Default (observation_at):**
- Jobs are included if **scraped during the reporting period**
- Jobs posted in Jan but re-observed in Mar appear in Mar report

**With --filter-by-posted-date:**
- Jobs are included if **posted during the reporting period**
- Jobs posted in Jan appear in Jan report, regardless of when re-observed
- Correct for backfill scenarios with historical data

## After Backfill Completes

1. **Verify reports look correct:**
   ```bash
   ls -la artifacts/reports/weekly/2026-W*/
   ls -la artifacts/reports/monthly/2026-*/
   ```

2. **Regenerate the public site:**
   ```bash
   python -m mexico_linkedin_jobs_portfolio site --locale all
   mkdocs build
   ```

3. **Review generated pages:**
   - Check `docs/public/weekly/` and `docs/public/monthly/` for new content
   - Verify job counts make sense for each period
   - Spot-check a few job postings to confirm dates are correct

4. **Commit and push:**
   ```bash
   git add artifacts/reports/ docs/public/
   git commit -m "backfill: regenerate historical reports with posted-date filtering"
   git push
   ```

## Going Forward (Next Monday)

Starting from the first report after the backfill:
- Use the **normal pipeline** (no special flags)
- Reports will use **observation date** filtering (standard behavior)
- New data will be bucketed correctly week-by-week as it arrives

The backfill is a **one-time operation** to fix the historical data ingestion issue.

## Troubleshooting

**If a report fails:**
- Check the error message for which period failed
- Open an issue if it's a systematic problem
- For individual failures, try rerunning that specific as_of_date

**If job counts seem wrong:**
- Verify the source CSV file contains jobs with the expected Posted On dates
- Check that reported_date is populated in the DuckDB or Parquet tables
- Confirm the period boundaries align with ISO week / calendar month expectations

**If site generation breaks:**
- Run `mkdocs build` manually to see detailed errors
- Check that all report artifacts exist before running site generation
- Ensure no duplicate period_id entries across reports
