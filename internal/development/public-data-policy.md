# Public Data Policy

## Default Rule
Public outputs are aggregate-first. Row-level publication is allowed only for explicitly approved de-identified exports.

## Allowed In Public Outputs
- aggregate counts and rankings
- period metadata and run summaries that do not expose private row-level fields
- de-identified row-level CSV exports that follow the approved public schema
- public HTML snapshots of generated reports

## Forbidden In Public Outputs
- raw company names in row-level downloads
- employer URLs
- raw description text
- raw job identifiers
- raw OpenAI prompts, responses, payloads, or response IDs
- any private drill-down data used only by the local dashboard or private datasets

## Public Row-Level CSV Contract
- one row per distinct job in the selected period
- derive `public_job_key` from a deterministic salted hash over private identifiers
- use the latest observation in the selected period plus the latest entity projection
- fail closed if the public-key salt is missing
