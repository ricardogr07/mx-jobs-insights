# mx-jobs-insights Roadmap

## Summary

`mx-jobs-insights` turns `LinkedInWebScraper` Mexico job data into curated analytics, bilingual report artifacts, a public MkDocs site, and local/cloud automation paths.

This file tracks the current architecture, the active cleanup backlog, and the next product-facing roadmap items. Detailed phase-by-phase implementation history now lives in [`internal/roadmap-history.md`](internal/roadmap-history.md).

## Current State

### Product Surfaces
- `curate`: read the upstream workspace, normalize the canonical model, and persist DuckDB plus Parquet outputs.
- `report`: compute closed weekly or monthly metrics, render bilingual Markdown and HTML, write the public CSV, and summarize the run.
- `site`: materialize the public MkDocs source from completed report artifacts.
- `pipeline`: orchestrate `curate`, `report`, `site`, docs validation, and optional cloud delivery.

### Delivery Surfaces
- GitHub Actions quality gate for lint, tests, docs, and package build.
- GitHub Pages publication from artifact-based site builds.
- Optional container, GCS, BigQuery, Terraform, and Cloud Run delivery paths.

### Public Data Boundary
- Public pages and downloads are derived from curated report artifacts, not direct raw-source reads.
- Public row-level exports exclude company, URL, raw description text, raw job identifiers, and raw OpenAI payloads.
- Private drill-down remains local-only in the Streamlit app and bounded private datasets.

## Active Cleanup

This cleanup pass keeps the current runtime behavior intact while making the repo easier to operate and review:

- separate public docs under `docs/` from internal operator and Codex material under `internal/`
- replace phase-oriented repo narratives with stable product and operator language
- normalize command catalogs, workflow docs, and subagent guidance around capabilities instead of implementation phases
- remove stale placeholders, outdated references, and legacy workflow naming
- keep tests, docs build, and workflow contract checks aligned with the cleaned structure

## Next Roadmap

### Near Term
- tighten repo consistency after the cleanup pass
- keep CI, Pages publication, and cloud release paths green from `main`
- expand fixture-backed coverage where cleanup uncovers weak contracts

### Product Follow-Ups
- improve report depth and period coverage with larger real-world upstream data slices
- add stronger operator runbooks for release and cloud recovery flows
- harden cloud deployment promotion and observability once the current delivery path is stable

## Completed Milestones

- canonical ingestion from SQLite and CSV upstream sources
- curated DuckDB and Parquet storage
- bilingual weekly and monthly report generation with public CSV output
- public MkDocs site generation and local Streamlit exploration
- GitHub-native publication workflow and CI quality gate
- container, cloud mirror, warehouse export, and Terraform foundation

## Working Rules

- no commit, tag, or release action happens without explicit user approval
- main agent owns integration, validation, and commit boundaries
- subagents, when used, must have explicit non-overlapping write scopes
- production code lives in `src/` and `scripts/`; notebooks remain exploratory only
- `PLAN.md` is the current roadmap, while `internal/roadmap-history.md` keeps the archived implementation detail
