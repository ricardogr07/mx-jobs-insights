# Presentation Policy

This page defines the v1 presentation contract for `mx-jobs-insights`.

## Audience

The primary audience is mixed public:

- recruiters and hiring managers who need a polished portfolio story
- technical peers who want to inspect methodology, pipeline design, and analytics choices

## Bilingual Requirement

v1 is bilingual from day one.

The public site and generated reports must support:

- English (`en`)
- Spanish (`es`)

The implementation may share one metric payload and render two locale-specific outputs from it.

## Site and App Split

### GitHub Pages

GitHub Pages is the public-facing surface for v1.

It should host:

- landing and overview pages
- weekly report archive
- monthly report archive
- methodology and data-policy pages
- downloadable public artifacts
- static HTML snapshots of generated reports

### Streamlit

Streamlit is the interactive application layer.

In v1 it is local-first and primarily intended for:

- private exploration
- filtering and drill-down
- validating curated data before later cloud deployment

The Streamlit app should be designed so it can move to cloud hosting later without changing the core pipeline logic.

## Report Contract

The reporting pipeline should generate:

- weekly reports
- monthly reports
- Markdown outputs for Pages integration
- standalone HTML snapshots for archive/download use
- bilingual narrative summaries

## AI Requirement

OpenAI is required for published narrative reports in v1.

That means:

- published weekly/monthly reports are expected to include AI-generated narrative summaries
- the prompt input must be aggregated metrics only
- missing OpenAI configuration is a production misconfiguration, not a silent publish-success path

## Bootstrap Navigation Note

The current `mkdocs.yml` navigation is intentionally bootstrap-only for phase 0.

At this stage it documents:

- development contracts and policies
- internal Codex guidance

The broader public GitHub Pages structure described above will be added in later phases once reporting, site generation, and public artifacts exist.

## Visual Direction

The public site should read as a portfolio-quality analytics showcase rather than an internal dashboard clone.

The guiding presentation rule is:

- public site: narrative and polished
- Streamlit app: analytical and exploratory

## Initial Default

Until later phases refine the rendering layer, the default assumption is:

- GitHub Pages is the public home
- Streamlit remains local-first
- bilingual content is a required product constraint, not a future enhancement
- the current docs nav is an internal/bootstrap nav, not the final public-site information architecture