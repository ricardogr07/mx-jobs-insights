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

### `pipeline_orchestrator`
- Purpose: own the Phase 4 automation CLI, orchestration summaries, and fixture-backed pipeline integration tests.
- Write scope: config models, automation modules, CLI orchestration wiring, pipeline summary models, tests.
- Use when: building the entrypoint that sequences curate, report, site, and docs validation.

### `workflow_release`
- Purpose: own GitHub Actions workflow definitions, upstream checkout wiring, Pages deploy, and artifact retention rules.
- Write scope: `.github/` and automation-facing runtime docs.
- Use when: adding or revising GitHub-native automation, schedules, or deployment contracts.

### `automation_validation`
- Purpose: own workflow assertions, automation docs, command-catalog updates, and runtime-secret guidance.
- Write scope: tests, `docs/development/`, `docs/codex/`, and `codex/config.toml`.
- Use when: validating the Phase 4 automation contract without editing the core orchestration or workflow behavior.

### `dashboard_site`
- Purpose: own late-phase Streamlit dashboard and public site UX work when higher-level presentation changes are needed.
- Write scope: dashboard code, site templates, Pages-facing docs.
- Use when: implementing data exploration UX or the public showcase site.

### `automation_release`
- Purpose: own workflows, deployment contracts, and publication automation.
- Write scope: `.github/`, release docs, runtime docs.
- Use when: adding CI/CD, schedules, Pages deploys, or future release automation.

### `container_runtime`
- Purpose: own the container image, deployment-neutral pipeline entrypoint, and cloud runtime packaging.
- Write scope: `infra/`, `Dockerfile`, `.dockerignore`, `docs/development`, `docs/codex`.
- Use when: building the Phase 5 container contract or packaging the pipeline for cloud execution.

### `cloud_artifact_sync`
- Purpose: own GCS object layout, sync safety, and cloud artifact publication contracts.
- Write scope: `src/mexico_linkedin_jobs_portfolio`, `tests`, `docs/development`.
- Use when: adding cloud storage mirroring for curated, report, site, or diagnostics outputs.

### `warehouse_exports`
- Purpose: own BigQuery export contracts and public/private dataset boundaries.
- Write scope: `src/mexico_linkedin_jobs_portfolio`, `tests`, `docs/development`.
- Use when: defining or validating BigQuery delivery from curated and report artifacts.

### `terraform_foundation`
- Purpose: own Terraform roots, GCP resource layout, IAM, and environment wiring.
- Write scope: `infra/`, `docs/development`.
- Use when: adding the Phase 5 infrastructure baseline or validation commands.

### `cloud_release_validation`
- Purpose: own cloud release docs, runbooks, and validation coverage for the Phase 5 delivery path.
- Write scope: `tests`, `docs/development`, `docs/codex`, `codex/config.toml`.
- Use when: validating the cloud release path without rewriting container, Terraform, or delivery code.

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

## Phase-4 Specialization Rule
- Phase 4 uses the automation roles above so orchestration code, workflow release wiring, and validation/docs can move in parallel without overlapping write scopes.
- The main agent owns the `pipeline` contract, final integration, and the reviewed commit boundaries.
- Workflow-release work should stay separate from pipeline-core code so GitHub Actions policy changes do not rewrite orchestration logic.
- Automation validation should focus on workflow assertions, docs, and runtime contracts after the pipeline and workflow lanes have stabilized.

## Phase-5 Specialization Rule
- Phase 5 uses the cloud roles above so container packaging, artifact sync, warehouse export, Terraform, and validation work can move in parallel without overlapping write scopes.
- The main agent owns the cloud contract, final integration, and the reviewed commit boundaries.
- Container and Terraform work should stay separate so deployment packaging does not rewrite cloud infrastructure decisions.
- Cloud validation should focus on release docs, runbooks, and runtime contracts after the infrastructure and delivery lanes have stabilized.

## Integration Responsibility
- Main agent validates the final step state before asking for review.
- Main agent decides when a step is ready for approval and possible commit.
- Subagents should return changed files, assumptions, and validation notes, not broad recaps.



