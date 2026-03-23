# Source Data Contract

This page defines the v1 input contract for `mx-jobs-insights`.

## Source of Truth

- Upstream repository: `ricardogr07/LinkedInWebScraper`
- Upstream branch: `data`
- Consumer repository: `mx-jobs-insights`
- Analytics inputs are pulled from the upstream `data` branch into this repo's local pipeline workspace.
- The upstream repo remains the source of truth for raw persisted scrape outputs.

## Supported Source Modes

v1 supports both upstream persistence surfaces equally:

- SQLite: `state/linkedin_jobs.sqlite`
- CSV exports:
  - `exports/latest/*.csv`
  - `exports/YYYY-MM-DD/*.csv`

The portfolio pipeline must support:

- `sqlite` mode: ingest only from the SQLite database
- `csv` mode: ingest only from CSV exports
- `auto` mode: detect whichever supported source is available in the checked-out upstream workspace

## Auto Mode Rule

`auto` mode must be deterministic.

- when only one supported source exists, use that source
- when both SQLite and CSV are present, prefer SQLite
- when neither supported source exists, fail clearly

SQLite is the default precedence when both exist because it carries richer run-history and enrichment context than CSV exports.

## SQLite Expectations

The current upstream SQLite contract is expected to provide these tables:

- `scrape_runs`
- `jobs`
- `job_snapshots`
- `job_enrichments`

The portfolio repo should treat SQLite as a first-class source, not an implementation detail.

## CSV Expectations

The current upstream CSV contract is expected to provide:

- per-city exports under `exports/latest/`
- dated export snapshots under `exports/YYYY-MM-DD/`
- one combined CSV for the current daily run under `exports/latest/`

At minimum, CSV mode should expect these columns when reconstructing the canonical model:

- `Title`
- `Location`
- `DatePosted`
- `JobID`

If present, CSV mode should also ingest optional structured fields such as:

- `Remote`
- `Company`
- `SeniorityLevel`
- `EmploymentType`
- `Industries`
- `JobFunction1`
- `JobFunction2`
- `JobFunction3`
- `English`
- `YoE`
- `MinLevelStudies`
- `ShortDescription`
- `TechStack`

CSV ingestion should preserve the observation date from the folder context when available and use file-level metadata when reconstructing snapshot-like records.

CSV mode is not expected to reproduce the full richness of SQLite tables such as `scrape_runs` and `job_enrichments`. It should instead map whatever export columns are available into the same downstream canonical analytics model.

## Canonicalization Rule

SQLite and CSV ingestion must normalize into the same canonical analytics model before any KPI, report, dashboard, or site logic runs.

Downstream analytics code should not branch on source type once normalization is complete.

## Local Workflow Rule

- This repo may clone, fetch, or check out the upstream `data` branch into a local workspace.
- This repo must not mutate the upstream source repository as part of normal analytics runs.
- Any later seeding, backfill, or upstream data-write workflow is out of scope for the portfolio repo.

## Initial Default

Until later phases refine the runtime config, the default planning assumption is:

- source mode: `auto`
- preferred source when both exist: SQLite
- CSV remains a supported first-class source, but not the default precedence when both sources are present