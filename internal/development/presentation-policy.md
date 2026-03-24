# Presentation Policy

## Goals
- keep the public site easy to scan from a GitHub Pages URL
- keep the local dashboard useful for deeper private exploration
- keep public and private presentation boundaries explicit

## Public Site
- build the public site from completed report artifacts rather than direct raw-source reads
- expose overview, weekly archive, monthly archive, methodology, and downloads
- publish only public-safe assets under `docs/public/assets/`
- keep the public site bilingual where the generated artifacts support it

## Local Dashboard
- read curated storage and report artifacts through shared loaders
- default to public-safe summaries and report selection
- clearly label any local-only private drill-down section
- keep the dashboard read-only

## Public Boundary
- public pages may include aggregate metrics and archive links
- public downloads may include the de-identified job CSV and HTML report snapshots
- company names may appear only in aggregate rankings or summaries
- raw company, URL, raw description text, raw job identifiers, and raw OpenAI payloads must stay out of public row-level artifacts
