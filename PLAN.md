# Mexico LinkedIn Jobs Portfolio Plan

## Summary

- Build this as a separate public repo in `C:\git\mx-jobs-insights`, consuming `LinkedInWebScraper` `data` branch inputs and turning them into a bilingual Mexico-focused analytics portfolio.
- Work phase by phase, one reviewed step at a time. No git commit happens until explicitly approved. Each approved step becomes a small commit before moving on.
- Phase 0 starts with repo bootstrap only: create `PLAN.md`, create the initial folder structure, add `AGENTS.md`, and add the Codex/dev docs scaffold so future phases have clear rules for subagents, skills, and workflow.

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
- `AGENTS.md` points to the durable docs under `docs/` and `codex/`; it does not become a second architecture spec.
- Production logic lives in `src/` and `scripts/`. Notebooks are exploratory only.

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

- Update .gitignore for this repo's actual runtime outputs:
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

## Phases 1-5

### Phase 1: Ingestion and Normalization

- Build source adapters for:
  - SQLite from `state/linkedin_jobs.sqlite`
  - CSV from `exports/latest` and dated `exports/YYYY-MM-DD`
- Normalize both into one canonical analytics model.
- Persist curated outputs in DuckDB and Parquet.
- Add reproducible sample fixtures for tests.

### Phase 2: Analytics and Report Generation

- Build weekly and monthly KPI pipelines from the same curated model.
- Generate Markdown and HTML reports from shared metric payloads.
- Add bilingual rendering.
- Add OpenAI narrative generation from aggregated metrics only.

### Phase 3: Dashboard and Public Site

- Build the local-first Streamlit dashboard over curated DuckDB/Parquet data.
- Build the MkDocs Material Pages site with bilingual overview pages, report archive pages, and downloadable public CSV/report artifacts.

### Phase 4: Automation

- Add GitHub Actions for weekly, monthly, and manual runs.
- Pull the latest scraper `data` branch contents into the pipeline workspace.
- Rebuild curated data, reports, downloads, and Pages output.
- Add failure handling, concurrency control, and artifact retention.

### Phase 5: Cloud Expansion

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
  - ingestion adapter unit tests
  - source equivalence tests between SQLite and CSV fixtures
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

- This repo currently only contains `README.md`, `.gitignore`, `LICENSE`, and git metadata, so phase 0 can establish clean structure without migration work.
- The first actual implementation step is phase 0 step 0.1: add `PLAN.md` and the initial folder structure.
- `docs/codex/` and `codex/` are durable developer assets and should exist from the start.
- Small commits and explicit approval checkpoints are part of the implementation process, not optional workflow guidance.
