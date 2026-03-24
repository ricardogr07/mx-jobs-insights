"""CLI entrypoints for ingestion, reporting, site generation, and automation."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Sequence
from datetime import date
from pathlib import Path
from typing import cast

from mexico_linkedin_jobs_portfolio.automation import PipelineOrchestrator
from mexico_linkedin_jobs_portfolio.config import (
    BIGQUERY_PRIVATE_DATASET_ENV,
    BIGQUERY_PUBLIC_DATASET_ENV,
    DEFAULT_UPSTREAM_REPO_URL,
    GCP_REGION_ENV,
    GCS_BUCKET_ENV,
    GCS_PREFIX_ENV,
    GOOGLE_CLOUD_PROJECT_ENV,
    OPENAI_API_KEY_ENV,
    OPENAI_BASE_URL_ENV,
    OPENAI_MODEL_ENV,
    PIPELINE_CADENCES,
    PIPELINE_LOCALES,
    PUBLIC_KEY_SALT_ENV,
    REPORT_CADENCES,
    REPORT_LOCALES,
    SITE_LOCALES,
    SOURCE_MODES,
    UPSTREAM_REF_ENV,
    UPSTREAM_REPO_URL_ENV,
    CuratedStorageConfig,
    PipelineConfig,
    ReportCadence,
    ReportConfig,
    ReportLocale,
    SiteConfig,
    SourceMode,
    UpstreamWorkspaceConfig,
)
from mexico_linkedin_jobs_portfolio.curation import (
    CuratedWriteResult,
    DuckDBCuratedStore,
    build_curated_batch,
)
from mexico_linkedin_jobs_portfolio.models import IngestionRunSummary, WorkspaceValidationResult
from mexico_linkedin_jobs_portfolio.presentation import SitePipeline
from mexico_linkedin_jobs_portfolio.reporting import ReportPipeline
from mexico_linkedin_jobs_portfolio.sources import (
    CsvSourceAdapter,
    LocalUpstreamWorkspaceProvider,
    SQLiteSourceAdapter,
)


def add_shared_arguments(parser: argparse.ArgumentParser) -> None:
    """Attach the shared source arguments used by ingest and curate."""

    parser.add_argument(
        "--source",
        choices=SOURCE_MODES,
        default="auto",
        help="Source selection mode.",
    )
    parser.add_argument(
        "--upstream-root",
        default=str(Path("../LinkedInWebScraper")),
        help="Local path to the upstream LinkedInWebScraper workspace.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the current command summary without attempting durable writes.",
    )


def build_parser() -> argparse.ArgumentParser:
    """Build the current CLI parser for ingest, curate, report, site, and pipeline."""

    parser = argparse.ArgumentParser(prog="mx-jobs-insights")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest_parser = subparsers.add_parser("ingest", help="Inspect the upstream workspace and canonical source summary.")
    add_shared_arguments(ingest_parser)

    curate_parser = subparsers.add_parser("curate", help="Normalize upstream records and write curated storage.")
    add_shared_arguments(curate_parser)
    curate_parser.add_argument(
        "--curated-root",
        default=str(CuratedStorageConfig().root),
        help="Directory where curated DuckDB state and Parquet sidecars should be written.",
    )

    report_parser = subparsers.add_parser(
        "report", help="Generate aggregate reports from curated data."
    )
    report_parser.add_argument(
        "--cadence",
        choices=REPORT_CADENCES,
        required=True,
        help="Closed reporting cadence to generate.",
    )
    report_parser.add_argument(
        "--as-of",
        dest="as_of_date",
        help="Optional YYYY-MM-DD reference date used to resolve the latest completed period.",
    )
    report_parser.add_argument(
        "--locale",
        choices=REPORT_LOCALES,
        default="all",
        help="Locale scope for rendered report artifacts.",
    )
    report_parser.add_argument(
        "--curated-root",
        default=str(CuratedStorageConfig().root),
        help="Directory containing the curated DuckDB database or Parquet sidecars.",
    )
    report_parser.add_argument(
        "--output-root",
        default="artifacts/reports",
        help="Directory where generated report artifacts should be written.",
    )
    report_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Compute the report period and metrics without writing artifacts or calling OpenAI.",
    )
    report_parser.add_argument(
        "--filter-by-posted-date",
        action="store_true",
        help="Filter jobs by Posted On date (reported_date) instead of observation date (for backfills).",
    )

    site_parser = subparsers.add_parser(
        "site", help="Generate public MkDocs source from existing report artifacts."
    )
    site_parser.add_argument(
        "--report-root",
        default="artifacts/reports",
        help="Directory containing completed report artifacts.",
    )
    site_parser.add_argument(
        "--docs-root",
        default="docs",
        help="Directory where public MkDocs source pages should be generated.",
    )
    site_parser.add_argument(
        "--locale",
        choices=SITE_LOCALES,
        default="all",
        help="Locale scope for generated public pages and copied HTML snapshots.",
    )
    site_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Resolve the public site index without writing MkDocs source pages.",
    )

    pipeline_parser = subparsers.add_parser(
        "pipeline", help="Run the full automation entrypoint over the existing pipeline seams."
    )
    add_shared_arguments(pipeline_parser)
    pipeline_parser.add_argument(
        "--cadence",
        choices=PIPELINE_CADENCES,
        required=True,
        help="Closed reporting cadence to publish through the automation pipeline.",
    )
    pipeline_parser.add_argument(
        "--as-of",
        dest="as_of_date",
        help="Optional YYYY-MM-DD reference date used to resolve the latest completed period.",
    )
    pipeline_parser.add_argument(
        "--locale",
        choices=PIPELINE_LOCALES,
        default="all",
        help="Locale scope for generated reports and public site outputs.",
    )
    pipeline_parser.add_argument(
        "--curated-root",
        default=str(CuratedStorageConfig().root),
        help="Directory where curated DuckDB state and Parquet sidecars should be written.",
    )
    pipeline_parser.add_argument(
        "--report-root",
        default="artifacts/reports",
        help="Directory where generated report artifacts should be written.",
    )
    pipeline_parser.add_argument(
        "--docs-root",
        default="docs",
        help="Directory where public MkDocs source pages should be generated.",
    )

    return parser


def build_workspace_config(args: argparse.Namespace) -> UpstreamWorkspaceConfig:
    """Translate parsed CLI arguments into the shared upstream workspace config."""

    return UpstreamWorkspaceConfig(
        root=Path(args.upstream_root),
        source_mode=cast(SourceMode, args.source),
    )


def build_curated_config(args: argparse.Namespace) -> CuratedStorageConfig:
    """Translate parsed CLI arguments into the curated storage config."""

    curated_root = getattr(args, "curated_root", CuratedStorageConfig().root)
    return CuratedStorageConfig(root=Path(curated_root))


def build_report_config(args: argparse.Namespace) -> ReportConfig:
    """Translate parsed CLI arguments and environment into the report config."""

    as_of_date = date.fromisoformat(args.as_of_date) if args.as_of_date else None
    return ReportConfig(
        cadence=cast(ReportCadence, args.cadence),
        locale=cast(ReportLocale, args.locale),
        as_of_date=as_of_date,
        curated_root=Path(args.curated_root),
        output_root=Path(args.output_root),
        dry_run=bool(args.dry_run),
        openai_api_key=os.environ.get(OPENAI_API_KEY_ENV),
        openai_model=os.environ.get(OPENAI_MODEL_ENV),
        public_key_salt=os.environ.get(PUBLIC_KEY_SALT_ENV),
        openai_base_url=os.environ.get(OPENAI_BASE_URL_ENV, "https://api.openai.com/v1"),
        filter_by_posted_date=bool(getattr(args, "filter_by_posted_date", False)),
    )


def build_site_config(args: argparse.Namespace) -> SiteConfig:
    """Translate parsed CLI arguments into the site-generation config."""

    return SiteConfig(
        report_root=Path(args.report_root),
        docs_root=Path(args.docs_root),
        locale=cast(ReportLocale, args.locale),
        dry_run=bool(args.dry_run),
    )


def build_pipeline_config(args: argparse.Namespace) -> PipelineConfig:
    """Translate parsed CLI arguments and environment into the pipeline config."""

    as_of_date = date.fromisoformat(args.as_of_date) if args.as_of_date else None
    return PipelineConfig(
        cadence=cast(ReportCadence, args.cadence),
        source_mode=cast(SourceMode, args.source),
        upstream_root=Path(args.upstream_root),
        curated_root=Path(args.curated_root),
        report_root=Path(args.report_root),
        docs_root=Path(args.docs_root),
        locale=cast(ReportLocale, args.locale),
        as_of_date=as_of_date,
        dry_run=bool(args.dry_run),
        openai_api_key=os.environ.get(OPENAI_API_KEY_ENV),
        openai_model=os.environ.get(OPENAI_MODEL_ENV),
        public_key_salt=os.environ.get(PUBLIC_KEY_SALT_ENV),
        openai_base_url=os.environ.get(OPENAI_BASE_URL_ENV, "https://api.openai.com/v1"),
        upstream_repo_url=os.environ.get(UPSTREAM_REPO_URL_ENV, DEFAULT_UPSTREAM_REPO_URL),
        upstream_ref=os.environ.get(UPSTREAM_REF_ENV),
        google_cloud_project=os.environ.get(GOOGLE_CLOUD_PROJECT_ENV),
        gcp_region=os.environ.get(GCP_REGION_ENV),
        gcs_bucket=os.environ.get(GCS_BUCKET_ENV),
        gcs_prefix=os.environ.get(GCS_PREFIX_ENV),
        bigquery_private_dataset=os.environ.get(BIGQUERY_PRIVATE_DATASET_ENV),
        bigquery_public_dataset=os.environ.get(BIGQUERY_PUBLIC_DATASET_ENV),
    )


def load_adapter_records(
    workspace: UpstreamWorkspaceConfig,
    validation: WorkspaceValidationResult,
) -> tuple[list, list, IngestionRunSummary]:
    """Load canonical records from the resolved source adapter."""

    if validation.resolved_source_mode == "sqlite":
        return SQLiteSourceAdapter().load(workspace)
    if validation.resolved_source_mode == "csv":
        return CsvSourceAdapter().load(workspace)
    raise RuntimeError("No resolved source mode is available for adapter loading.")


def build_run_summary(
    command_name: str,
    workspace: UpstreamWorkspaceConfig,
    validation: WorkspaceValidationResult,
    *,
    dry_run: bool,
    adapter_summary: IngestionRunSummary | None = None,
    source_run_count: int = 0,
    write_result: CuratedWriteResult | None = None,
) -> IngestionRunSummary:
    """Return a summary describing the current ingest or curate command state."""

    if dry_run:
        notes = [
            "Dry run validated command parsing, source loading, and the upstream workspace contract.",
            "Use this mode to inspect source readiness without writing curated outputs.",
        ]
    else:
        notes = [
            "This command writes curated storage from the resolved upstream source.",
            "Use it to validate end-to-end source loading, canonical normalization, and storage writes.",
        ]
    notes.extend(validation.notes)

    observation_count = 0
    entity_count = 0
    status = validation.status
    resolved_source_mode = validation.resolved_source_mode

    if adapter_summary is not None:
        observation_count = adapter_summary.observation_count
        entity_count = adapter_summary.entity_count
        status = adapter_summary.status
        source_run_count = adapter_summary.source_run_count or source_run_count
        notes.extend(adapter_summary.notes)

    if command_name == "ingest":
        if resolved_source_mode == "sqlite":
            notes.append("SQLite ingestion is now active for validation.")
        elif resolved_source_mode == "csv":
            notes.append("CSV ingestion is now active for validation.")
        else:
            notes.append("No concrete source adapter was selected.")
    else:
        if dry_run and source_run_count:
            status = "curation_dry_run_ready"
            notes.append(
                f"Built canonical curated batch with {source_run_count} source run projection(s)."
            )
            notes.append(
                "Dry run validated the canonical curation path without writing DuckDB or Parquet artifacts."
            )
        elif write_result is not None:
            source_run_count = write_result.source_run_count
            observation_count = write_result.observation_count
            entity_count = write_result.entity_count
            status = "curation_written"
            notes.append(f"Wrote curated DuckDB state to {write_result.duckdb_path}.")
            notes.append(f"Exported Parquet sidecars to {write_result.parquet_root}.")
        else:
            notes.append("Curated DuckDB and Parquet writes are available without --dry-run.")

    deduped_notes: list[str] = []
    for note in notes:
        if note not in deduped_notes:
            deduped_notes.append(note)

    return IngestionRunSummary(
        command_name=command_name,
        source_mode=workspace.source_mode,
        upstream_root=workspace.resolved_root(),
        dry_run=dry_run,
        resolved_source_mode=resolved_source_mode,
        source_run_count=source_run_count,
        observation_count=observation_count,
        entity_count=entity_count,
        duckdb_path=write_result.duckdb_path if write_result is not None else None,
        parquet_root=write_result.parquet_root if write_result is not None else None,
        status=status,
        notes=tuple(deduped_notes),
    )


def execute_dry_run(
    command_name: str,
    workspace: UpstreamWorkspaceConfig,
    validation: WorkspaceValidationResult,
) -> tuple[IngestionRunSummary, int]:
    """Execute the current dry-run path for the validated workspace."""

    if not validation.is_valid:
        return build_run_summary(command_name, workspace, validation, dry_run=True), 1

    observations, entities, adapter_summary = load_adapter_records(workspace, validation)

    source_run_count = 0
    if command_name == "curate" and adapter_summary is not None:
        batch = build_curated_batch(observations, entities, adapter_summary)
        source_run_count = len(batch.source_runs)

    return build_run_summary(
        command_name,
        workspace,
        validation,
        dry_run=True,
        adapter_summary=adapter_summary,
        source_run_count=source_run_count,
    ), 0


def execute_curate_write(
    workspace: UpstreamWorkspaceConfig,
    validation: WorkspaceValidationResult,
    curated_config: CuratedStorageConfig,
) -> tuple[IngestionRunSummary, int]:
    """Execute the curated write path."""

    if not validation.is_valid:
        return build_run_summary("curate", workspace, validation, dry_run=False), 1

    observations, entities, adapter_summary = load_adapter_records(workspace, validation)
    batch = build_curated_batch(observations, entities, adapter_summary)
    write_result = DuckDBCuratedStore(curated_config).persist_batch(batch)

    return build_run_summary(
        "curate",
        workspace,
        validation,
        dry_run=False,
        adapter_summary=adapter_summary,
        source_run_count=len(batch.source_runs),
        write_result=write_result,
    ), 0


def execute_report(args: argparse.Namespace) -> tuple[dict[str, object], int]:
    """Execute the report path and return the CLI payload plus exit code."""

    report_config = build_report_config(args)
    summary, exit_code = ReportPipeline().run(report_config)
    payload = summary.to_display_dict()
    payload["report_request"] = report_config.to_display_dict()
    payload["curated_storage"] = report_config.curated_storage.to_display_dict()
    payload["resolved_period"] = {
        "period_id": summary.period_id,
        "period_start": summary.period_start.isoformat() if summary.period_start else None,
        "period_end": summary.period_end.isoformat() if summary.period_end else None,
    }
    return payload, exit_code


def execute_site(args: argparse.Namespace) -> tuple[dict[str, object], int]:
    """Execute the site path and return the CLI payload plus exit code."""

    site_config = build_site_config(args)
    summary, exit_code = SitePipeline().run(site_config)
    payload = summary.to_display_dict()
    payload["site_request"] = site_config.to_display_dict()
    return payload, exit_code


def execute_pipeline(args: argparse.Namespace) -> tuple[dict[str, object], int]:
    """Execute the automation path and return the CLI payload plus exit code."""

    pipeline_config = build_pipeline_config(args)
    summary, exit_code = PipelineOrchestrator().run(pipeline_config)
    payload = summary.to_display_dict()
    payload["pipeline_request"] = pipeline_config.to_display_dict()
    payload["workspace"] = pipeline_config.workspace.to_display_dict()
    payload["curated_storage"] = pipeline_config.curated_storage.to_display_dict()
    payload["report_request"] = pipeline_config.report_config.to_display_dict()
    payload["site_request"] = pipeline_config.site_config.to_display_dict()
    return payload, exit_code


def main(argv: Sequence[str] | None = None) -> int:
    """Run the repo CLI commands."""

    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.command == "report":
        payload, exit_code = execute_report(args)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return exit_code

    if args.command == "site":
        payload, exit_code = execute_site(args)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return exit_code

    if args.command == "pipeline":
        payload, exit_code = execute_pipeline(args)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return exit_code

    if args.command == "ingest" and not args.dry_run:
        print(
            "Ingest is summary-only. Re-run with --dry-run, or use curate without --dry-run to write curated outputs.",
            file=sys.stderr,
        )
        return 2

    workspace = build_workspace_config(args)
    validation = LocalUpstreamWorkspaceProvider().validate(workspace)
    if args.command == "curate" and not args.dry_run:
        curated_config = build_curated_config(args)
        summary, exit_code = execute_curate_write(workspace, validation, curated_config)
    else:
        curated_config = build_curated_config(args) if args.command == "curate" else None
        summary, exit_code = execute_dry_run(args.command, workspace, validation)

    payload = summary.to_display_dict()
    if curated_config is not None:
        payload["curated_storage"] = curated_config.to_display_dict()
    payload["workspace"] = workspace.to_display_dict()
    payload["workspace_validation"] = validation.to_display_dict()
    print(json.dumps(payload, indent=2, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())



























