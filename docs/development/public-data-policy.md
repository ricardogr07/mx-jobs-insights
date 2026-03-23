# Public Data Policy

This page defines what `mx-jobs-insights` can publish publicly in v1.

## Policy Summary

- Public outputs are aggregate-first.
- v1 may expose a de-identified public row-level CSV.
- Public pages and downloads must avoid direct exposure of sensitive or overly specific job-level fields from the upstream source.

## Allowed Public Outputs

The public site may publish:

- weekly and monthly aggregate metrics
- grouped summaries by city, role family, remote type, seniority, and skill cluster
- charts and tables derived from aggregated metrics
- bilingual narrative summaries generated from aggregated metrics
- a de-identified public CSV derived from the curated analytics model
- aggregated company-level rankings or charts, such as top companies by posting volume

## Forbidden Public Fields

The public site and public downloadable datasets must not expose these raw fields:

- company in row-level public datasets
- URL
- full description
- raw upstream `JobID`
- raw OpenAI payloads
- OpenAI response IDs
- any field that recreates the exact upstream job record identity beyond the approved public contract

## Company Policy

Company names are allowed in aggregated public outputs such as grouped tables or charts.

Company names are not allowed in the row-level public CSV or any other public row-level dataset.

## Allowed Public Row-Level Detail

The approved v1 de-identified CSV may include:

- `public_job_key`
- `title`
- `as_of_date`
- `city`
- `state`
- `remote_type`
- `seniority_level`
- `employment_type`
- `industry`
- `english_required`
- `min_years_experience`
- `job_function_primary`
- normalized skill or tag fields derived from the curated model

This public CSV must be built from curated outputs, not copied directly from raw source files.

## Local vs Public Boundary

Local analytics work may retain richer fields for private analysis, testing, and dashboard exploration.

Public outputs must pass through a dedicated publication filter before they are written to GitHub Pages or downloadable artifacts.

## AI Narration Rule

OpenAI-generated report narration must be based on aggregated metrics only.

It must not be prompted with raw public row-level job records, raw upstream descriptions, or raw AI payloads.

## Initial Default

Until later phases refine the publication layer, the default assumption is:

- private curated model can contain richer fields
- public site and public downloads use an explicit allowlist
- company names are allowed only in aggregated public outputs
- if a field is not explicitly allowed for public output, it stays private