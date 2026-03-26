# Streamlit Local Development Workflow

Guide for running the Mexico LinkedIn Jobs Insights Streamlit app locally for development and analysis.

## Overview

The Streamlit dashboard loads curated job data from DuckDB and report artifacts, providing an interactive interface for:
- Browsing job listings with full details
- Filtering by period, cadence (weekly/monthly), and date ranges
- Viewing public reports and metrics
- Exporting data to CSV

## Prerequisites

- **Python 3.11+** (project requirement)
- **Pip package manager**
- **Local workspace** with this repository cloned

## Installation

### Step 1: Install Dependencies

Install the app environment with required packages:

```bash
pip install -e ".[app]"
```

**What this installs:**
- `streamlit>=1.32.0` - Interactive app framework
- `duckdb>=1.1.3` - Curated data access
- All core project dependencies

**Note:** No API keys, environment variables, or secrets needed to run locally.

### Step 2: Prepare Data (Optional)

The app expects data in two locations:

#### Option A: Use Existing Artifacts (Recommended for Quick Start)
The repo includes pre-generated reports in `artifacts/reports/`. If this directory exists with recent data, you can skip data generation.

#### Option B: Generate Fresh Data
If you want the latest job data, run the pipeline:

```bash
pip install -e ".[dev]"  # Install dev dependencies (includes viz packages)
python -m mexico_linkedin_jobs_portfolio pipeline --curated-only
```

This generates fresh curated data in `artifacts/curated/`:
- `mx_jobs_insights.duckdb` - Job observations and entities
- `parquet/` - Sidecar Parquet files (fallback format)

## Running the App

### Launch Streamlit Dashboard

From the repository root:

```bash
streamlit run src/mexico_linkedin_jobs_portfolio/interfaces/streamlit/app.py
```

Expected output:
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://<your-ip>:8501
```

Open http://localhost:8501 in your browser.

### Configuration in Sidebar

On app startup, configure data sources:

1. **Report Root Directory**
   - Default: `artifacts/reports`
   - Contains `run_summary.json` files organized by cadence/period
   - Click "Refresh Report Index" to reload available periods

2. **Curated Data Root Directory**
   - Default: `artifacts/curated`
   - Contains `mx_jobs_insights.duckdb` or Parquet files
   - App automatically selects available format

3. **Report Cadence**
   - `latest` - Most recent available report
   - `weekly` - Select specific week (W01-W52)
   - `monthly` - Select specific month (01-12)

4. **Period Selection** (if not using "latest")
   - Dropdown populated from available periods in report root
   - Only shows periods matching selected cadence

## App Features

### Overview Tab
- **Public Metrics:** Job count, observation count, data freshness
- **Top Cities:** Bar chart of job distribution by city
- **Tech Stack:** Most mentioned technologies
- **Employment Types:** Full-time vs part-time distribution

### Public Report Tab
- **Markdown Preview:** Report text and analysis
- **HTML View:** Links to full HTML render
- **CSV Export:** Download job data for analysis
- **Metadata:** Report generation timestamps

### Local Drill-Down Tab
- **Job Listings:** Full records with all fields (raw join data)
- **Filtering:** By date, city, company, seniority
- **Export:** Individual job records as JSON
- **Inspection:** View complete field values

## Data Sources

### Primary: Curated Dataset
- **Format:** DuckDB database or Parquet files
- **Tables:** 
  - `job_observations` - Job listings with timestamps
  - `job_entities` - Enriched job data (skills, seniority, etc.)
- **Automatic Join:** App joins these tables by job_id
- **Filtering:** By selected period's posted-on date range

### Secondary: Report Artifacts
- **Location:** `artifacts/reports/{cadence}/{period_id}/`
- **Files:**
  - `run_summary.json` - Execution metadata + metrics
  - `*.html` - Pre-rendered visualizations
  - `*.md` - Analysis text
  - `*.csv` - Job exports
- **Discovery:** App scans directory structure for available periods

## Validation & Error Handling

### Expected Loading Sequence
1. App starts → Scans report root for available periods
2. User selects cadence + period → Loads metrics from `run_summary.json`
3. User views "Local Drill-Down" → Loads curated database
4. Table joins occur → Filters to selected period
5. UI renders with data or error messages

### Common Issues

**"No reports found"**
- Check `artifacts/reports/` directory exists
- Verify subdirectories follow pattern: `{cadence}/{period_id}/`
- Look for `run_summary.json` files in period directories

**"Failed to load curated data"**
- Check `artifacts/curated/` directory exists
- Verify `mx_jobs_insights.duckdb` or Parquet files are readable
- Check file permissions: `ls -la artifacts/curated/`

**"Empty job records"**
- Period may have no jobs in date range
- Verify period boundaries in sidebar match data generated
- Check curated data was generated for the period

### Graceful Degradation
The app handles missing components:
- Missing visualizations → Shows "No data available"
- Missing CSV export → Hides export button
- Missing HTML render → Shows placeholder link
- Read permissions error → Displays error message with path

## Development Workflow

### Testing Changes

1. **Edit visualization functions:**
   ```bash
   # Edit src/mexico_linkedin_jobs_portfolio/interfaces/streamlit/app.py
   # Streamlit auto-reloads on save
   ```

2. **Test in browser:**
   - Sidebar shows "Always rerun" option during development
   - Click "Rerun" after changes to refresh
   - Check browser console for errors

3. **Debug data loading:**
   - Check app logs in terminal where `streamlit run` was executed
   - Errors print before reaching browser

### Performance Notes

- **Lazy Loading:** Curated data loads only when "Local Drill-Down" tab clicked
- **Caching:** Streamlit caches data between reruns (same period)
- **Large Datasets:** 10K+ job records may take 2-3 seconds to join and display

## Troubleshooting

### Port Already in Use
Streamlit defaults to port 8501. If occupied:

```bash
streamlit run --logger.level=debug --server.port 8502 \
  src/mexico_linkedin_jobs_portfolio/interfaces/streamlit/app.py
```

### Streamlit Crashes
Check Python version and reinstall dependencies:

```bash
python --version  # Should be 3.11+
pip install --upgrade streamlit duckdb
streamlit run src/mexico_linkedin_jobs_portfolio/interfaces/streamlit/app.py
```

### Data Freshness
App shows report timestamps. If data is stale:

1. Run pipeline to generate new curated data
2. Run backfill workflow to generate new reports
3. Click "Refresh Report Index" in sidebar

## References

- **App Code:** [interfaces/streamlit/app.py](../../src/mexico_linkedin_jobs_portfolio/interfaces/streamlit/app.py)
- **Data Models:** [models/reporting.py](../../src/mexico_linkedin_jobs_portfolio/models/reporting.py)
- **Curated Data:** [analytics/dataset.py](../../src/mexico_linkedin_jobs_portfolio/analytics/dataset.py)
- **Streamlit Docs:** https://docs.streamlit.io/

## Next Steps

- **For Real Data:** Run `python -m mexico_linkedin_jobs_portfolio pipeline` to load production data
- **For Analysis:** Use "Local Drill-Down" tab to explore job listings
- **For Reports:** View pre-rendered HTML reports in "Public Report" tab
- **For Export:** Download CSV from sidebar for Excel/analysis tools
