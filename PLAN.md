# Mexico LinkedIn Jobs Portfolio Plan

## Summary

- Build this as a separate public repo in `C:\git\mx-jobs-insights`, consuming `LinkedInWebScraper` `data` branch inputs and turning them into a bilingual Mexico-focused analytics portfolio.
- Work phase by phase, one reviewed step at a time. No git commit happens until explicitly approved. Each approved step becomes a small commit before moving on.
- Phase 0 is complete. Phase 1 focuses on ingestion and normalization, with explicit reviewed substeps so source adapters, canonical models, fixtures, and subagent specialization can evolve without overlapping ownership.

## Working Rules

- `PLAN.md` in the repo root is the planning source of truth for this project.
- Every phase is split into small reviewed steps. The sequence is:
  1. implement one step
  2. review locally
  3. get approval
  4. commit
  5. move to the next step
- No commit, tag, or release action happens without explicit approval.
- Main agent owns integration and final review. Subagents are used in parallel for bounded tasks with disjoint ownership.
- Reuse an existing relevant subagent thread when the work stays in the same domain, and close idle agents once their scoped task is complete.
- `AGENTS.md` points to the durable docs under `docs/` and `codex/`; it does not become a second architecture spec.
- Production logic lives in `src/` and `scripts/`. Notebooks are exploratory only.

## Current Status

- Phase 0 is already established:
  - root scaffold and package namespace exist
  - `PLAN.md`, `AGENTS.md`, `codex/`, and `docs/codex/` exist
  - `.gitignore`, `pyproject.toml`, `tox.toml`, and `mkdocs.yml` exist
  - source data contract, public data policy, and presentation policy are documented
- The current upstream data contract has been verified:
  - upstream repo: `ricardogr07/LinkedInWebScraper`
  - source branch: `data`
  - inputs present today:
    - `state/linkedin_jobs.sqlite`
    - `exports/latest/*.csv`
    - `exports/YYYY-MM-DD/*.csv`
  - current CSV exports already include enriched fields such as `ShortDescription`, `TechStack`, `YoE`, `MinLevelStudies`, `English`, and OpenAI metadata

## Phase 0: Bootstrap and Repo Guardrails

### Step 0.1: Root plan and scaffold

- Add `PLAN.md` at the repo root with this phased roadmap.
- Create the initial folder structure:
  - `src/mexico_linkedin_jobs_portfolio/`
  - `scripts/`
  - `configs/`
  - `docs/`
  - `docs/codex/`
  - `docs/development/`
  - `tests/`
  - `notebooks/2024-archive/`
  - `artifacts/` only as an ignored runtime/output convention, not tracked content
- Add minimal `__init__.py` package scaffolding and placeholder README sections only where needed to explain structure.

### Step 0.2: Codex and agent scaffolding

- Add `AGENTS.md` at the repo root.
- Add a repo-tracked `codex/` folder with:
  - `codex/config.toml`
  - internal guidance on rules, approved commands, subagent roles, and workflow expectations
- Add `docs/codex/` pages for:
  - `index.md`
  - `subagents.md`
  - `skills.md`
  - `tools-and-commands.md`
  - `integrations.md`
- Keep these docs internal/developer-oriented, not end-user portfolio docs.

### Step 0.3: Repo hygiene baseline

- Update `.gitignore` for this repo's actual runtime outputs:
  - `artifacts/`
  - local DuckDB/SQLite files
  - generated reports/downloads if produced outside tracked docs/assets areas
  - local config overrides such as `.env` or non-example runtime TOML
- Add the minimal packaging/tooling skeleton needed for later phases:
  - `pyproject.toml`
  - `tox.toml`
  - `mkdocs.yml`
- Define the package namespace as `mexico_linkedin_jobs_portfolio`.

### Step 0.4: Project decisions captured in docs

- Document the source repo contract:
  - source repo is `ricardogr07/LinkedInWebScraper`
  - source branch is `data`
  - v1 supports SQLite and CSV ingestion equally
- Document the public data policy:
  - aggregate-first public outputs
  - de-identified row-level public CSV with title allowed, but no company, URL, raw description, raw IDs, or raw OpenAI payloads
- Document the presentation policy:
  - bilingual `en` and `es`
  - GitHub Pages public site
  - Streamlit local-first app
  - OpenAI required for published narrative reports in v1

## Phase 1: Ingestion and Normalization
### Step 1.1: Phase-1 planning and agent-role expansion
- Update `PLAN.md` so Phase 1 is split into reviewed substeps, just like Phase 0.
- Extend `codex/config.toml` and `docs/codex/subagents.md` with Phase-1-specific roles:
  - `source_sync_contracts`
  - `sqlite_source_adapter`
  - `csv_source_adapter`
  - `canonical_curation`
  - `fixtures_validation`
- Add planned command references for Phase 1 shells in `docs/codex/tools-and-commands.md`, including a standalone workspace-validation shell for step 1.3.

### Step 1.2: Ingestion contract shell
- Add the package structure needed for Phase 1:
  - `src/mexico_linkedin_jobs_portfolio/config/`
  - `src/mexico_linkedin_jobs_portfolio/sources/`
  - `src/mexico_linkedin_jobs_portfolio/curation/`
  - `src/mexico_linkedin_jobs_portfolio/models/`
  - `src/mexico_linkedin_jobs_portfolio/interfaces/cli/`
- Define the first shared types and interfaces:
  - `SourceMode = auto | sqlite | csv`
  - `UpstreamWorkspaceConfig`
  - `SourceAdapter` protocol
  - `CanonicalObservationRecord`
  - `CanonicalEntityRecord`
  - `IngestionRunSummary`
- Add a thin CLI shell for `ingest` and `curate` with `--dry-run`, but no full business logic yet.

### Step 1.3: Local upstream workspace contract
- Implement a local-path-first workspace provider.
- Default upstream local path: sibling repo `../LinkedInWebScraper`.
- Validate the presence of the upstream `data` branch workspace shape without mutating the upstream repo.
- Defer managed git fetch/checkout automation to a later step or later phase; keep an interface seam so it can be added without changing adapters.

### Step 1.4: SQLite adapter shell and first working path
- Add a `SQLiteSourceAdapter` that reads:
  - `scrape_runs`
  - `jobs`
  - `job_snapshots`
  - `job_enrichments`
- Make SQLite the first fully working path for source normalization because `auto` mode prefers it when both sources exist.
- Normalize SQLite rows into the canonical observation/entity model without exposing downstream code to raw table shapes.

### Step 1.5: CSV adapter shell and parity path
- Add a `CsvSourceAdapter` that reads:
  - `exports/latest/*.csv`
  - `exports/YYYY-MM-DD/*.csv`
- Enforce the minimum CSV contract already documented:
  - `Title`, `Location`, `DatePosted`, `JobID`
- Ingest optional enriched columns when present.
- Reconstruct observation dates from dated folder context when available.
- Normalize CSV into the exact same canonical model used by SQLite.

### Step 1.6: Canonical curated model and storage shell
- Make DuckDB the authoritative curated store.
- Emit Parquet sidecars for downstream convenience.
- Phase-1 canonical model should include:
  - `source_runs`
  - `job_observations`
  - `job_entities`
- `job_observations` is the main fact table at observation grain.
- `job_entities` is the latest-known per-job projection.
- Public filtering is not part of Phase 1 storage; richer private fields may remain in the curated model for now.

### Step 1.7: Sample fixtures and reproducibility
- Add small checked-in sample artifacts for both source modes:
  - one SQLite fixture slice
  - one `exports/latest` CSV slice
  - one dated CSV slice
- Add a helper script for regenerating tiny fixtures from local upstream data, but keep the checked-in fixtures deterministic and small enough for tests.
- Keep fixtures under a dedicated test-data area, separate from future runtime artifacts.

### Step 1.8: First end-to-end ingest smoke
- Add a first working local path:
  - `ingest --source sqlite --dry-run`
  - `ingest --source csv --dry-run`
  - `curate --source auto --dry-run`
- Then add the first non-dry-run curated write path:
  - read upstream source
  - normalize to canonical model
  - persist to DuckDB
  - emit Parquet sidecars
  - print a run summary

## Phase-1 Commit Boundaries
- Commit 1: Phase-1 plan/docs/subagent-role expansion
- Commit 2: ingestion contract shell and package scaffolding
- Commit 3: local upstream workspace provider
- Commit 4: SQLite adapter first working path
- Commit 5: CSV adapter parity path
- Commit 6: canonical DuckDB + Parquet curated storage
- Commit 7: fixtures and regeneration helper
- Commit 8: first ingest/curate smoke path
## Phase 2: Analytics and Report Generation

- Build weekly and monthly KPI pipelines from the same curated model.
- Generate Markdown and HTML reports from shared metric payloads.
- Add bilingual rendering.
- Add OpenAI narrative generation from aggregated metrics only.

## Phase 3: Dashboard and Public Site

- Build the local-first Streamlit dashboard over curated DuckDB/Parquet data.
- Build the MkDocs Material Pages site with bilingual overview pages, report archive pages, and downloadable public CSV/report artifacts.

## Phase 4: Automation

- Add GitHub Actions for weekly, monthly, and manual runs.
- Pull the latest scraper `data` branch contents into the pipeline workspace.
- Rebuild curated data, reports, downloads, and Pages output.
- Add failure handling, concurrency control, and artifact retention.

## Phase 5: Cloud Expansion

- Keep source, curation, analytics, report rendering, and publishing abstracted from deployment targets.
- Prepare for later Cloud Run/GCS/BigQuery/Terraform expansion without changing core pipeline logic.
- Do not add cloud-specific complexity before the GitHub-native workflow is stable.

## Public Interfaces and Contracts

- Package namespace: `mexico_linkedin_jobs_portfolio`
- Planned CLI surface:
  - `ingest`
  - `curate`
  - `report`
  - `site`
  - `pipeline`
- Planned runtime inputs:
  - source repo/branch config
  - cadence config (`weekly`, `monthly`, `manual`)
  - locale config (`en`, `es`)
  - OpenAI config for narrative generation
- Planned durable outputs:
  - curated DuckDB/Parquet
  - Markdown reports
  - HTML report snapshots
  - public de-identified CSV downloads
  - GitHub Pages site assets

## Subagent Plan

- Use parallel subagents from phase 0 onward with explicit ownership:
  - `repo_bootstrap`: scaffolding, packaging, config shell
  - `docs_devx`: `AGENTS.md`, `codex/`, `docs/codex/`, MkDocs nav
  - `data_contracts`: ingestion contracts, schema mapping, sample fixtures
  - `source_sync_contracts`: upstream workspace config and local path validation
  - `sqlite_source_adapter`: SQLite reader shape and SQLite-focused tests
  - `csv_source_adapter`: CSV reader shape, folder-date reconstruction, and CSV-focused tests
  - `canonical_curation`: canonical models, DuckDB writes, Parquet sidecars, and curation summaries
  - `fixtures_validation`: sample artifacts, regeneration helpers, equivalence tests, and smoke tests
  - `analytics_reports`: KPIs, templates, narrative payloads
  - `dashboard_site`: Streamlit and Pages UX
  - `automation_release`: GitHub Actions and deployment contracts
- Subagents never own integration. The main agent merges results, validates behavior, and waits for approval before any commit.

## Test Plan

- Phase 0:
  - folder structure exists
  - docs build can see internal Codex pages
  - repo hygiene/ignore rules match planned outputs
- Phase 1:
  - source mode resolution tests
  - local workspace path validation tests
  - SQLite schema mapping tests
  - CSV minimum-field validation tests
  - canonical record construction tests
  - DuckDB write/read tests
  - Parquet sidecar emission tests
  - source equivalence tests between SQLite and CSV fixtures where the logical slice overlaps
  - smoke checks for `ingest --source sqlite --dry-run`, `ingest --source csv --dry-run`, and `curate --source auto --dry-run`
  - `auto` mode acceptance checks:
    - SQLite is chosen when both sources exist
    - CSV is chosen when SQLite is absent
    - failure is explicit when neither source exists
- Phase 2:
  - KPI tests
  - Markdown/HTML snapshot tests
  - AI prompt/input shaping tests
- Phase 3:
  - Streamlit helper tests
  - static site generation tests
- Phase 4:
  - workflow tests
  - scheduled/manual pipeline smoke tests
- Phase 5:
  - container/config smoke tests only; no cloud infra rollout until later

## Assumptions and Defaults

- Phase 1 starts with both adapter shells scaffolded, but SQLite becomes the first fully working ingestion path.
- Local development uses a configurable local upstream path first; managed git-sync automation is deferred.
- DuckDB is the curated source of truth; Parquet is a sidecar/export format.
- CLI shells for `ingest` and `curate` land in Phase 1 even before the full analytics/report stack exists.
- Public filtering, dashboard logic, report rendering, and GitHub automation remain out of scope for Phase 1.