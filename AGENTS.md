# Agent Guide

Use these files first:
- `PLAN.md`
- `docs/index.md`
- `internal/codex/`
- `codex/config.toml`

Core repo rules:
- Work one reviewed step at a time. Do not commit, tag, or release anything without explicit user approval.
- Main agent owns integration, validation, and commit boundaries.
- Subagents must have explicit, non-overlapping write scopes and must not revert each other's work.
- Prefer documented repo commands and workflow notes from `codex/config.toml` and `internal/codex/`.
- `codex/config.toml` is a template/catalog only. Do not store secrets, tokens, or machine-specific credentials in it.

This file stays intentionally short. Detailed guidance lives in `internal/codex/`.
