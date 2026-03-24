# Subagents

Use subagents to parallelize well-scoped work, not to outsource integration decisions.

## Default Rules
- Main agent owns the critical path, final validation, and commit boundaries.
- Every subagent must have an explicit write scope before it starts.
- Subagents must not revert or overwrite changes from other agents.
- Prefer delegation for sidecar work that can run in parallel without blocking the next local step.
- Reuse an existing relevant subagent thread before spawning a new one for the same domain.
- Close idle agents after their scoped task is done so the active agent set stays intentional.
- Keep final integration local when the work is tightly coupled or likely to trigger follow-up edits.

## Explorer vs Worker
- `explorer`: ask specific repo or environment questions and gather facts quickly.
- `worker`: use for bounded implementation or docs/test tasks with a clear file boundary.

## When To Delegate
- Draft docs while the main agent validates structure or tooling.
- Audit a narrow subsystem before a larger refactor.
- Prepare disjoint config, docs, or workflow changes in parallel.
- Add guardrail tests while the main agent implements core behavior.

## When Not To Delegate
- The immediate next step is blocked on the answer.
- The task is smaller than the delegation overhead.
- The task would cause overlapping edits in the same files.
- The task is mostly integration judgment rather than bounded execution.

## Repo Role Catalog

### `repo_bootstrap`
- Purpose: own scaffolding, package skeleton setup, and tooling shell work.
- Write scope: root config files, package skeleton, tests skeleton.
- Use when: adding foundational structure or bootstrap tooling.

### `docs_devx`
- Purpose: own internal docs, Codex guidance, and developer workflow material.
- Write scope: `docs/`, `codex/`, `AGENTS.md`.
- Use when: documenting workflow rules, commands, or developer guidance.

### `data_contracts`
- Purpose: own durable ingestion-policy docs, source-field contracts, and schema decisions after the workspace and adapter seams are established.
- Write scope: `docs/development/`, `docs/codex/`, and `PLAN.md`.
- Use when: documenting or revising ingestion policy and schema decisions, not adapter implementation.

### `source_sync_contracts`
- Purpose: own upstream workspace config, local source-path validation, and source-mode interface seams.
- Write scope: workspace provider code, source contract docs, and source-mode config helpers.
- Use when: adding or revising how this repo discovers and validates the upstream local data workspace.

### `sqlite_source_adapter`
- Purpose: own SQLite reader shape, schema mapping, and SQLite-focused ingestion tests.
- Write scope: SQLite source adapters, SQLite fixture notes, and SQLite-focused tests.
- Use when: implementing or refining the SQLite ingestion path.

### `csv_source_adapter`
- Purpose: own CSV reader shape, dated-folder reconstruction, and CSV-focused ingestion tests.
- Write scope: CSV source adapters, CSV fixture notes, and CSV-focused tests.
- Use when: implementing or refining the CSV ingestion path.

### `canonical_curation`
- Purpose: own canonical models, DuckDB writes, Parquet sidecars, and curation summaries.
- Write scope: canonical models, curation modules, and storage-facing curation tests.
- Use when: normalizing source records into the curated analytics model.

### `fixtures_validation`
- Purpose: own sample artifacts, regeneration helpers, equivalence tests, and ingest smoke tests.
- Write scope: `tests/`, fixture generation scripts, and sample data assets.
- Use when: adding deterministic Phase-1 fixtures or validating SQLite/CSV parity.

### `analytics_reports`
- Purpose: own KPI definitions, report templates, and narrative payload design.
- Write scope: analytics modules, report rendering modules, report docs.
- Use when: implementing weekly/monthly metrics, summaries, or narrative generation.

### `site_generation_contracts`
- Purpose: own the public site index, site-generation contracts, and site CLI-facing summary models.
- Write scope: config models, presentation loaders, CLI integration, site summary models, tests.
- Use when: building the Phase 3 `site` command and its shared artifact catalog.

### `pages_public_ia`
- Purpose: own the public-first MkDocs information architecture and public-facing docs pages.
- Write scope: `docs/index.md`, `docs/development/`, `mkdocs.yml`.
- Use when: restructuring the public site navigation or adding public documentation pages.

### `streamlit_explorer`
- Purpose: own the local Streamlit dashboard shell, loaders, and private drill-down UX.
- Write scope: Streamlit app code, presentation loaders, and app-scoped tests.
- Use when: building the local-only dashboard surface or its view-model helpers.

### `presentation_validation`
- Purpose: own presentation smoke tests, docs validations, and public/private boundary checks.
- Write scope: tests, `docs/development/`, `docs/codex/`, `mkdocs.yml`.
- Use when: validating the Phase 3 site and dashboard contract without changing core UI behavior.

### `dashboard_site`
- Purpose: own late-phase Streamlit dashboard and public site UX work when higher-level presentation changes are needed.
- Write scope: dashboard code, site templates, Pages-facing docs.
- Use when: implementing data exploration UX or the public showcase site.

### `automation_release`
- Purpose: own workflows, deployment contracts, and publication automation.
- Write scope: `.github/`, release docs, runtime docs.
- Use when: adding CI/CD, schedules, Pages deploys, or future release automation.

## Phase-1 Specialization Rule
- Phase 1 uses the specialized roles above so workspace, adapter, curation, and fixture work can run in parallel without overlapping the durable contract-doc ownership of `data_contracts`.
- SQLite and CSV workers may proceed in parallel only after the shared interfaces and workspace contract are stable.
- Canonical curation work should stay behind a stable source adapter boundary so it does not have to reason about raw source-specific shapes.
- Fixture and validation work should run alongside adapter implementation, not after all ingestion code is finished.

## Phase-3 Specialization Rule
- Phase 3 uses the presentation roles above so public site structure, Streamlit UX, and validation can move in parallel without overlapping write scopes.
- The main agent owns integration, shared artifact contracts, and the final reviewed step boundaries.
- Public-first MkDocs work should stay separate from the Streamlit app shell so docs navigation does not become coupled to dashboard implementation details.
- Validation work should keep the public site, Streamlit app, and boundary rules aligned without rewriting the implementation lanes.

## Integration Responsibility
- Main agent validates the final step state before asking for review.
- Main agent decides when a step is ready for approval and possible commit.
- Subagents should return changed files, assumptions, and validation notes, not broad recaps.

