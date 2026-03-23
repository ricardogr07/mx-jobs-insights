# Codex Enablement

This section is an internal developer support pack for using Codex effectively in this repository. It exists to keep the phase-by-phase workflow explicit and reviewable.

## What This Covers
- repo-specific agent rules and review gates
- subagent usage patterns for parallel work
- observed built-in skills and a future repo-specific skill blueprint
- exact local commands and command status markers
- recommended integrations for OpenAI docs and GitHub workflows

## Source of Truth
- project roadmap and phase breakdown: `PLAN.md`
- internal developer guidance: this `docs/codex/` section
- repository ownership and step-review rules: `AGENTS.md`
- template command and integration catalog: `codex/config.toml`

## Status Model
- `available_now`: usable in the current environment without extra setup
- `planned`: expected to exist later in the repo, but not yet implemented
- `recommended_later`: worth standardizing, but not assumed to be installed in-session
- `blocked_or_misconfigured`: present or intended, but not currently usable from this environment

## Current Environment Snapshot

### Available Now
- `git` is installed and the repo is initialized
- `python` is available as the runtime shell entrypoint
- the repo now has a tracked phase plan and initial package scaffold
- Codex can use subagents for bounded parallel work when the task merits it

### Planned
- repo-local packaging, lint, test, docs, and build commands
- workflow validation and release automation
- project-specific ingestion, analytics, reporting, dashboard, and site pipelines

### Recommended Later
- `openai_docs` MCP for official OpenAI references
- `github_mcp` for richer GitHub context once auth and setup are stable
- a future repo-specific skill for phased portfolio development

## Why This Exists
This repository is being built in small reviewed increments. These notes keep agent behavior, subagent partitioning, and command expectations explicit so each step is easier to review before it is committed.