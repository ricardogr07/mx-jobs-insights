# Subagents

Use subagents to parallelize bounded work, not to outsource integration decisions.

## Default Rules
- Main agent owns the critical path, final validation, and commit boundaries.
- Every subagent must have an explicit write scope before it starts.
- Subagents must not revert or overwrite changes from other agents.
- Prefer delegation for sidecar work that can run in parallel without blocking the next local step.
- Reuse an existing relevant subagent thread before spawning a new one for the same domain.
- Close idle agents after their scoped task is done.
- Keep final integration local when the work is tightly coupled or likely to trigger follow-up edits.

## Agent Types
- `explorer`: answer specific repo questions quickly.
- `worker`: implement bounded changes inside an explicit file scope.

## Domain Catalog

### Repo and Docs
- `repo_bootstrap`: scaffolding, package skeleton setup, and tooling shell work.
- `docs_devx`: internal docs, Codex guidance, and developer workflow material.

### Ingestion and Curation
- `data_contracts`: durable source-policy docs, source-field contracts, and schema decisions.
- `source_sync_contracts`: upstream workspace config, local source-path validation, and source-mode seams.
- `sqlite_source_adapter`: SQLite reader shape, schema mapping, and SQLite-focused ingestion tests.
- `csv_source_adapter`: CSV reader shape, dated-folder reconstruction, and CSV-focused ingestion tests.
- `canonical_curation`: canonical models, DuckDB writes, Parquet sidecars, and curation summaries.
- `fixtures_validation`: sample artifacts, regeneration helpers, equivalence tests, and smoke tests.

### Reporting and Presentation
- `analytics_reports`: KPI definitions, report templates, and narrative payload design.
- `site_generation_contracts`: public site index, site-generation contracts, and site summary models.
- `pages_public_ia`: public MkDocs information architecture and public-facing docs pages.
- `streamlit_explorer`: local Streamlit dashboard shell, loaders, and private drill-down UX.
- `presentation_validation`: presentation smoke tests, docs validations, and public/private boundary checks.

### Automation and Release
- `pipeline_orchestrator`: pipeline CLI orchestration, cross-surface summaries, and pipeline integration tests.
- `workflow_release`: GitHub Actions workflows, upstream checkout wiring, Pages deploy, and artifact retention.
- `automation_validation`: workflow assertions, automation docs, command-catalog updates, and runtime-secret guidance.
- `automation_release`: release workflows, deployment contracts, and publication automation.

### Cloud Delivery
- `container_runtime`: container image, deployment-neutral pipeline entrypoint, and cloud runtime packaging.
- `cloud_artifact_sync`: GCS object layout, sync safety, and cloud artifact publication contracts.
- `warehouse_exports`: BigQuery export contracts and public/private dataset boundaries.
- `terraform_foundation`: Terraform roots, GCP resource layout, IAM, and environment wiring.
- `cloud_release_validation`: cloud release docs, runbooks, and validation coverage.

## Delegation Guidance
- Split work by domain and file ownership, not by "research first, code later" when the write scope is already clear.
- Keep workflow files separate from orchestration code, and keep docs/test lanes separate from behavior changes whenever possible.
- Do not delegate the immediate blocking step if the main agent needs that answer before it can proceed.
- Ask each worker to return changed files, assumptions, and validation notes.
