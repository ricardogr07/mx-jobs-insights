# Skills

This page documents the Codex skills currently observed in this environment and a possible repo-specific skill blueprint.

## Current Built-In Skills

### `openai-docs`
- Purpose: use official OpenAI documentation as the primary source for OpenAI-related work.
- Use when: checking current API guidance, model selection, or SDK behavior for report narration.

### `skill-creator`
- Purpose: design or update reusable Codex skills.
- Use when: a repeated workflow deserves a dedicated skill.

### `skill-installer`
- Purpose: install supported Codex skills into the local environment.
- Use when: a documented skill should become locally available without hand-copying files.

### `neon-pairwise-review`
- Purpose: run a governed pairwise review workflow over two candidate responses.
- Use when: a task explicitly needs pairwise evaluation.

## Future Skill Blueprint

### `mx-jobs-portfolio-maintainer`
- Status: `optional concept`
- Purpose: guide repo maintenance with review gates, data-contract awareness, and safe work partitioning.

## Proposed Responsibilities
- map requests to the current roadmap and active surfaces
- remind the agent about review-before-commit rules
- recommend safe subagent partitioning for ingestion, reporting, site, automation, or cloud work
- keep the upstream data-branch contract explicit while the repo evolves
- align implementation steps with the current roadmap and validation gate
