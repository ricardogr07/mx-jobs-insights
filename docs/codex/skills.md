# Skills

This page documents the Codex skills currently observed in this environment and a future skill blueprint for this repository.

## Current Built-In Skills

### `openai-docs`
- Purpose: use official OpenAI documentation as the primary source for OpenAI-related work.
- Use when: checking current API guidance, model selection, or SDK behavior for report narration.
- Why it matters here: this repo plans to use OpenAI for bilingual narrative summaries from aggregated metrics.

### `skill-creator`
- Purpose: design or update reusable Codex skills.
- Use when: the repo reaches repeated workflows that deserve a dedicated skill.

### `skill-installer`
- Purpose: install supported Codex skills into the local environment.
- Use when: a documented skill should become locally available without hand-copying files.

### `neon-pairwise-review`
- Purpose: run a governed pairwise review workflow over two candidate responses.
- Use when: a task explicitly needs pairwise evaluation.

## Future Skill Blueprint

### `mx-jobs-portfolio-maintainer`
- Status: planned only, not implemented in this step.
- Purpose: guide phased portfolio development with strict review gates and data-contract awareness.

## Proposed Responsibilities
- map requests to the current development phase
- remind the agent about review-before-commit rules
- recommend safe subagent partitioning for docs, ingestion, analytics, dashboard, or automation work
- keep the scraper data-branch contract explicit while the new repo evolves
- align implementation steps with the current `PLAN.md` checkpoint

## Likely Inputs
- current phase and step
- target subsystem or file area
- expected validation commands
- whether the change is public-contract sensitive

## Likely Outputs
- a narrowed implementation checklist
- validation sequence for the current step
- recommended subagent roles and write scopes
- contract, rollout, or review notes

This future skill should remain a workflow guide, not a replacement for `PLAN.md`, `AGENTS.md`, or the docs under `docs/codex/`.