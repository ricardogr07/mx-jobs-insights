# Backfill Historical Reports Workflow

Complete step-by-step guide for running the GitHub Actions backfill workflow to regenerate historical job reports with posted-date filtering.

## Overview

The **Backfill Historical Reports** workflow automatically generates reports for past reporting periods (weeks/months) by filtering job listings based on their original posted date rather than observation date. This ensures historical accuracy since all 2026-01-14+ job data was loaded in a single snapshot on 2026-03-23.

**Key Features:**
- Manual trigger via GitHub Actions UI or CLI
- Concurrency protection (only one run at a time)
- Generates 12 reports: 10 weekly + 2 monthly + 1 current
- Optional site regeneration and GitHub Pages deployment
- Detailed diagnostics and run artifacts

## Prerequisites Checklist

Before running the workflow, verify these are configured in your repository:

### Secrets (Repository Settings → Secrets and variables → Secrets)
- ✅ `OPENAI_API_KEY` - OpenAI API key for bill categorization and analysis
- ✅ `MX_JOBS_PUBLIC_KEY_SALT` - Encryption salt for hashing sensitive data

### Variables (Repository Settings → Secrets and variables → Variables)
- ✅ `MX_JOBS_OPENAI_MODEL` - Model name (e.g., `gpt-4-turbo-preview`)
- ✅ `MX_JOBS_OPENAI_BASE_URL` - API endpoint (usually `https://api.openai.com/v1`)

### External Dependencies
- ✅ `ricardogr07/LinkedInWebScraper` - Upstream repository with source data
  - Must have `data` branch accessible
  - Data files must be available for pipeline to process

### Verification
To check if secrets/variables are set:

```bash
# Requires GitHub CLI (gh)
gh secret list --repo <owner>/<repo>
gh variable list --repo <owner>/<repo>
```

Expected output:
```
Name                          Scope         Updated
OPENAI_API_KEY               Actions       2026-03-25
MX_JOBS_PUBLIC_KEY_SALT      Actions       2026-03-25
MX_JOBS_OPENAI_MODEL         Actions       2026-03-25
MX_JOBS_OPENAI_BASE_URL      Actions       2026-03-25
```

## Manual Trigger: Step-by-Step

### Method 1: GitHub Web UI (Recommended)

1. **Navigate to Actions**
   - Go to your repository on github.com
   - Click **Actions** tab in the navbar

2. **Find Workflow**
   - Look for **"Backfill Historical Reports"** in the left sidebar
   - Click on it

3. **Trigger Workflow**
   - Click **"Run workflow"** button (blue button, top right)
   - A dropdown appears with workflow input options

4. **Configure Options**
   - **regenerate_site** - Toggle switch
     - `true` (default) - Regenerate and deploy website
     - `false` - Generate reports only  
   - Leave blank to use default (true)

5. **Execute**
   - Click **"Run workflow"** button in the dropdown
   - Workflow queues and starts within 30 seconds

6. **Monitor**
   - Page auto-refreshes showing progress
   - Click workflow name to view real-time logs

### Method 2: GitHub CLI

**With Site Regeneration (default):**
```bash
gh workflow run 'Backfill Historical Reports' --ref main
```

**Reports Only (no site deployment):**
```bash
gh workflow run 'Backfill Historical Reports' --ref main -f regenerate_site=false
```

**Monitor in Real Time:**
```bash
gh run watch  # Picks most recent run
```

## Workflow Execution Flow

### Timeline & Stages

| Stage | Duration | Purpose | Status |
|-------|----------|---------|--------|
| **1. Repository Checkout** | ~10s | Clone current repo | Essential |
| **2. Data Checkout** | ~30s | Clone upstream LinkedInWebScraper (data branch) | Essential |
| **3. Python Setup** | ~20s | Install Python 3.11 runtime | Essential |
| **4. Dependencies** | ~60s | `pip install -e ".[dev]"` with dev packages | Essential |
| **5. Pipeline Run** | 2-5min | Generate curated dataset from source data | Essential |
| **6. Backfill Script** | 5-10min | Generate 12 reports (W02-W12, Jan-Feb, current) | Essential |
| **7. Site Regeneration** | 2-3min | MkDocs build static site | Conditional (if `regenerate_site=true`) |
| **8. Diagnostics** | ~30s | Archive metrics and summaries | Always |
| **9. Upload Diagnostics** | ~1min | Artifact available 30 days | Always |
| **10. Pages Artifact** | ~30s | Prepare site for deployment | Conditional |
| **11. Deploy Pages** | 1-2min | Push to GitHub Pages | Conditional |
| **12. Job Summary** | ~10s | Write summary to Actions tab | Always |

**Total Runtime:** 12-25 minutes (varies by pipeline complexity)

### Real-Time Monitoring

**In GitHub UI:**
1. Go to Actions → Backfill Historical Reports → [workflow run name]
2. Each stage shows as **In progress** (spinner), **Passed** (✓), or **Failed** (✗)
3. Click on any stage to expand and see live logs
4. Scroll down to see full console output

**Example Log Output:**
```
Run: python -m mexico_linkedin_jobs_portfolio report --cadence weekly --as-of 2026-01-12 --filter-by-posted-date
================================================================================
Generating report for Week 2 (W02)...
✓ Loaded 45 jobs from curated dataset
✓ Generated metrics dashboard
✓ Created visualizations (5 charts)
✓ Rendered HTML report
✓ Exported CSV (45 rows)
Report saved to: artifacts/reports/weekly/2026-W02/
================================================================================
```

## Backfill Script Details

### What Gets Generated

**12 Reports Total:**

**Weekly (W02-W12):** Past 11 weeks
- W02: Jan 6-12, 2026 (as-of 2026-01-12)
- W03: Jan 13-19, 2026
- W04: Jan 20-26, 2026
- W05: Jan 27-Feb 2, 2026
- W06: Feb 3-9, 2026
- W07: Feb 10-16, 2026
- W08: Feb 17-23, 2026
- W09: Feb 24-Mar 2, 2026
- W10: Mar 3-9, 2026
- W11: Mar 10-16, 2026

**Monthly (Jan-Feb):** Past 2 months
- Jan 2026: Jan 1-31 (as-of 2026-02-01)
- Feb 2026: Feb 1-28 (as-of 2026-03-01)

**Current (W12):** Current week
- W12: Mar 17-23, 2026 (as-of 2026-03-23)

### Report Artifacts Generated

For **each** report, the workflow creates:

```
artifacts/reports/{cadence}/{period_id}/
├── run_summary.json           # Execution metadata + metrics
├── metrics.json               # Job counts, city distribution, etc.
├── index.html                 # Main report render
├── public_export.csv          # Anonymized job listing export
├── analysis.md                # Generated analysis text
└── [additional html files]    # Charts and visualizations
```

### Execution Command

For each report, the underlying command is:

```bash
python -m mexico_linkedin_jobs_portfolio report \
  --cadence {weekly|monthly} \
  --as-of {ISO_DATE} \
  --filter-by-posted-date
```

**Key Flag:** `--filter-by-posted-date`
- Redistributes all loaded jobs to their original posted date
- Crucially important because all data was loaded in one snapshot
- Without this flag, all jobs would be dated 2026-03-23

### Output Structure

Each report creates a summary JSON:

```json
{
  "period_id": "2026-W12",
  "cadence": "weekly",
  "job_count": 125,
  "observation_count": 48,
  "generation_timestamp": "2026-03-25T14:32:15Z",
  "duration_seconds": 45,
  "success": true
}
```

### Error Handling

If any report fails:
1. Script logs the failure
2. Continues processing remaining reports
3. Returns exit code 1 (workflow marked as failed)
4. Error details included in job summary

## Monitoring & Verification

### Real-Time During Execution

**Watch Progress:**
```bash
gh run watch [run-id]  # From terminal
```

**Check Status Online:**
- GitHub UI shows each stage live
- Green checkmarks appear as stages complete
- Red X's appear on failures (with error details)

### After Completion

#### 1. Check Workflow Summary
- Go to Actions → Backfill run
- Scroll to **"Backfill Workflow Summary"** section
- Shows: Total reports, successful, failed, duration

#### 2. Review Diagnostics Artifact
- Click **Artifacts** section at bottom of run page
- Download `backfill-diagnostics.zip` (expires in 30 days)
- Extract contents:
  ```
  BACKFILL_SUMMARY.md          # Detailed execution summary
  metrics/
  ├── 2026-W02.json           # Per-report metrics
  ├── 2026-W03.json
  └── ...
  ```

#### 3. Verify Live Site (if `regenerate_site=true`)
- Go to GitHub Pages URL: `https://{owner}.github.io/{repo}/`
- Check "Latest Report" shows W12 data
- Verify report dates are correct
- Deployment shows in GitHub Pages settings

#### 4. Download Report Files
- Navigate to `artifacts/reports/` in repository
- Download specific report HTML/CSV as needed
- All reports retained in repository

## Troubleshooting

### Workflow Failed at Pipeline Stage

**Error:** "Failed to merge upstream data"

**Cause:** LinkedInWebScraper data branch unavailable

**Fix:**
1. Verify upstream repo has readable `data` branch
2. Check branch contains required files
3. Contact upstream repo maintainer if issues persist
4. Retry workflow

### API Rate Limits

**Error:** "OpenAI API rate limit exceeded"

**Cause:** Too many concurrent report generations

**Fix:**
1. Workflow queues automatically (max 1 concurrent)
2. If stuck, wait 1 hour and retry
3. Check OpenAI account has sufficient quota
4. Verify API key is valid (test via: `curl https://api.openai.com/v1/models -H "Authorization: Bearer $OPENAI_API_KEY"`)

### Git Pages Deployment Fails

**Error:** "Failed to deploy to GitHub Pages"

**Cause:** Pages not enabled in repository

**Fix:**
1. Go to repository **Settings** → **Pages**
2. Ensure "Build and deployment" source is set to "GitHub Actions"
3. Retry workflow

### Some Reports Generated, Some Failed

**Error:** "5 reports passed, 1 report failed"

**Cause:** Usually data inconsistency or transient API error

**Fix:**
1. Check error details in job summary
2. Review diagnostics artifact
3. Re-run workflow (usually succeeds on retry)

### No Reports Generated

**Error:** "No reports generated" in summary

**Cause:** Script didn't execute or pipeline failed

**Fix:**
1. Check stage 6 (Run Backfill) logs
2. Verify curated data generated successfully (stage 5)
3. Check for Python errors in console
4. Ensure backfill script exists: `scripts/backfill_historical_reports.py`

## Performance Tuning

### Reduce Generation Time

For reports-only (skip site regeneration):
```bash
gh workflow run 'Backfill Historical Reports' --ref main -f regenerate_site=false
```
- **Time Saved:** 2-3 minutes

### Parallel Report Generation (Advanced)

Currently, reports generate sequentially. For faster backfill:
1. Edit [scripts/backfill_historical_reports.py](../../scripts/backfill_historical_reports.py)
2. Use `concurrent.futures.ThreadPoolExecutor` to parallelize report generation
3. Be mindful of API rate limits

## Advanced: Local Simulation

To test backfill logic locally before pushing:

```bash
# Generate curated data
python -m mexico_linkedin_jobs_portfolio pipeline --curated-only

# Run backfill script
python scripts/backfill_historical_reports.py --dry-run

# Verify reports created
ls -la artifacts/reports/weekly/
ls -la artifacts/reports/monthly/
```

## Related Documentation

- **Backfill Script:** [scripts/backfill_historical_reports.py](../../scripts/backfill_historical_reports.py)
- **Workflow YAML:** [.github/workflows/backfill-historical-reports.yml](../../.github/workflows/backfill-historical-reports.yml)
- **CI/Pre-push Rules:** [CI_PRE_PUSH_CHECKLIST.md](../../CI_PRE_PUSH_CHECKLIST.md)
- **GitHub Pages Setup:** https://docs.github.com/en/pages
- **GitHub Actions:** https://docs.github.com/en/actions

## Next Steps

1. **First Run:** Trigger with default settings (`regenerate_site=true`)
2. **Monitor:** Watch Actions tab for ~20 minutes
3. **Verify:** Check GitHub Pages shows updated data
4. **Download:** Get diagnostics artifact for records
5. **Schedule (Optional):** Set up scheduled runs via cron syntax in workflow YAML

## Quick Reference

| Action | Command |
|--------|---------|
| Trigger workflow | `gh workflow run 'Backfill Historical Reports' --ref main` |
| Watch run | `gh run watch` |
| Check secrets | `gh secret list --repo owner/repo` |
| Download artifact | Click in Actions UI or use API |
| View pages | `https://owner.github.io/repo/` |
| Check logs | Actions tab → Workflow run → Stage logs |
