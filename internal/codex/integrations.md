# Integrations

This page covers the small set of integrations worth standardizing for ongoing development work.

## Status Model
- `observed`: usable immediately in this environment
- `optional`: supported and worth adding when the workflow needs it
- `blocked_or_misconfigured`: present or intended, but not currently usable

## `openai_docs`
- Kind: MCP
- Status: `optional`
- Purpose: query official OpenAI documentation during narrative-generation, SDK, and model-selection work.
- Add command:

```bash
codex mcp add openaiDeveloperDocs --url https://developers.openai.com/mcp
```

- Reference: https://platform.openai.com/docs/docs-mcp

## `github_cli`
- Kind: command-line integration
- Status: `blocked_or_misconfigured`
- Purpose: local GitHub operations such as branch inspection, issue lookup, and workflow checks.
- Check command:

```bash
gh auth status
```

- Current note: the CLI is installed, but the active GitHub token is invalid in this session.
- Reference: https://cli.github.com/

## `github_mcp`
- Kind: MCP
- Status: `optional`
- Purpose: provide structured GitHub repository context and operations through an MCP server.
- Prerequisites:
  - valid GitHub token
  - remote server or Docker-based setup path
- References:
  - https://docs.github.com/en/copilot/how-tos/provide-context/use-mcp/use-the-github-mcp-server
  - https://github.com/github/github-mcp-server

## Deferred Integrations
- browser-oriented or deployment-specific MCPs remain optional until the repo has a stronger need for them
- prefer keeping the default maintenance workflow small and explicit
