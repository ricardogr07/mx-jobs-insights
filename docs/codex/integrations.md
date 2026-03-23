# Integrations

This page covers the small set of integrations worth standardizing for ongoing development work. It separates what is usable now from what is recommended later.

## Status Model
- `available_now`: usable immediately in this environment
- `planned`: expected later in the repo but not implemented yet
- `recommended_later`: officially supported and worth adding, but not assumed to be installed here
- `blocked_or_misconfigured`: present or intended, but not currently usable

## `openai_docs`
- Kind: MCP
- Status: `recommended_later`
- Purpose: query official OpenAI documentation during narrative-generation, SDK, and model-selection work.
- Official add command:

```bash
codex mcp add openaiDeveloperDocs --url https://developers.openai.com/mcp
```

- Why it matters here: this repo plans to generate AI-assisted report narration and should use primary-source OpenAI docs when that layer is implemented.
- Official reference: https://platform.openai.com/docs/docs-mcp

## `github_cli`
- Kind: command-line integration
- Status: `blocked_or_misconfigured`
- Purpose: local GitHub operations such as branch inspection, issue lookup, and workflow checks.
- Check command:

```bash
gh auth status
```

- Current environment note: the CLI is installed, but the active GitHub token is invalid in this session.
- Official reference: https://cli.github.com/

## `github_mcp`
- Kind: MCP
- Status: `recommended_later`
- Purpose: provide structured GitHub repository context and operations through an MCP server.
- Prerequisites:
  - valid GitHub token
  - remote-server or Docker-based setup path
- Official references:
  - https://docs.github.com/en/copilot/how-tos/provide-context/use-mcp/use-the-github-mcp-server
  - https://github.com/github/github-mcp-server

## Deferred Integrations
- cloud, database, and browser-oriented MCPs are intentionally deferred
- they may become useful later for deployment, cloud analytics, or site publishing work
- they are not standardized during phase 0