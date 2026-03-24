# Codex Enablement

This section keeps the repo-specific Codex guidance in one place without exposing it through the public site.

## What It Covers
- repo rules and review gates
- domain-based subagent roles
- live commands and workflow entrypoints
- observed skills and optional integrations
- operator-facing notes for local, GitHub, and cloud work

## Source Of Truth
- current roadmap: `PLAN.md`
- archived implementation history: `internal/roadmap-history.md`
- operator docs and policies: `internal/development/`
- command and integration catalog: `codex/config.toml`

## Status Labels
- `ready`: the command or surface is available in the current repo state
- `observed`: present in the current environment and verified locally
- `optional`: useful but not required for the core workflow
- `blocked_or_misconfigured`: present or intended, but not currently usable in this environment
