# Source Data Contract

## Upstream Repository
- repository: `ricardogr07/LinkedInWebScraper`
- primary branch for this repo: `data`
- local default workspace path: `../LinkedInWebScraper`

## Supported Inputs
- `state/linkedin_jobs.sqlite`
- `exports/latest/*.csv`
- `exports/YYYY-MM-DD/*.csv`

## Source Modes
- `auto`: prefer SQLite when both sources are present, otherwise fall back to CSV
- `sqlite`: read from the upstream SQLite database
- `csv`: read from the latest or dated CSV exports

## Minimum CSV Contract
- `Title`
- `Location`
- `DatePosted`
- `JobID`

Optional enriched columns are ingested when present.

## Workspace Rules
- treat the upstream workspace as read-only
- validate shape before any source read
- keep source adapters isolated from downstream analytics, reporting, and site code
