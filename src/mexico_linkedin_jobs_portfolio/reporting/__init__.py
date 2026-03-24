"""Reporting pipeline, public filtering, and narrative generation."""

from mexico_linkedin_jobs_portfolio.reporting.openai_narration import (
    NarrationClient,
    OpenAINarrationClient,
    build_narration_request_body,
)
from mexico_linkedin_jobs_portfolio.reporting.pipeline import ReportPipeline
from mexico_linkedin_jobs_portfolio.reporting.publication import (
    PUBLIC_CSV_FIELDNAMES,
    build_public_job_records,
    write_public_csv,
)
from mexico_linkedin_jobs_portfolio.reporting.renderers import render_html, render_markdown

__all__ = [
    "NarrationClient",
    "OpenAINarrationClient",
    "PUBLIC_CSV_FIELDNAMES",
    "ReportPipeline",
    "build_narration_request_body",
    "build_public_job_records",
    "render_html",
    "render_markdown",
    "write_public_csv",
]

