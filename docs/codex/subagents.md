# Subagents

Use subagents to parallelize well-scoped work, not to outsource integration decisions.

## Default Rules
- Main agent owns the critical path, final validation, and commit boundaries.
- Every subagent must have an explicit write scope before it starts.
- Subagents must not revert or overwrite changes from other agents.
- Prefer delegation for sidecar work that can run in parallel without blocking the next local step.
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
- Purpose: own source ingestion contracts, schema mapping notes, and sample fixture planning.
- Write scope: ingestion modules, schema docs, fixture definitions.
- Use when: planning or implementing the LinkedInWebScraper data-branch contract.

### `analytics_reports`
- Purpose: own KPI definitions, report templates, and narrative payload design.
- Write scope: analytics modules, report rendering modules, report docs.
- Use when: implementing weekly/monthly metrics, summaries, or narrative generation.

### `dashboard_site`
- Purpose: own Streamlit dashboard and public site UX work.
- Write scope: dashboard code, site templates, Pages-facing docs.
- Use when: implementing data exploration UX or the public showcase site.

### `automation_release`
- Purpose: own workflows, deployment contracts, and publication automation.
- Write scope: `.github/`, release docs, runtime docs.
- Use when: adding CI/CD, schedules, Pages deploys, or future release automation.

## Integration Responsibility
- Main agent validates the final step state before asking for review.
- Main agent decides when a step is ready for approval and possible commit.
- Subagents should return changed files, assumptions, and validation notes, not broad recaps.