"""Thin CLI shell for phase-1 ingestion and curation planning."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import cast

from mexico_linkedin_jobs_portfolio.config import (
    SOURCE_MODES,
    CuratedStorageConfig,
    SourceMode,
    UpstreamWorkspaceConfig,
)
from mexico_linkedin_jobs_portfolio.curation import (
    CuratedWriteResult,
    DuckDBCuratedStore,
    build_curated_batch,
)
from mexico_linkedin_jobs_portfolio.models import IngestionRunSummary, WorkspaceValidationResult
from mexico_linkedin_jobs_portfolio.sources import (
    CsvSourceAdapter,
    LocalUpstreamWorkspaceProvider,
    SQLiteSourceAdapter,
)


def add_shared_arguments(parser: argparse.ArgumentParser) -> None:
    """Attach the common phase-1 shell arguments used by ingest and curate."""

    parser.add_argument(
        "--source",
        choices=SOURCE_MODES,
        default="auto",
        help="Planned source selection mode.",
    )
    parser.add_argument(
        "--upstream-root",
        default=str(Path("../LinkedInWebScraper")),
        help="Local path to the upstream LinkedInWebScraper workspace.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the current shell contract without attempting source reads or curated writes.",
    )


def build_parser() -> argparse.ArgumentParser:
    """Build the phase-1 CLI parser for ingest and curate shell commands."""

    parser = argparse.ArgumentParser(prog="mx-jobs-insights")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest_parser = subparsers.add_parser("ingest", help="Planned ingestion shell.")
    add_shared_arguments(ingest_parser)

    curate_parser = subparsers.add_parser("curate", help="Planned canonical curation shell.")
    add_shared_arguments(curate_parser)
    curate_parser.add_argument(
        "--curated-root",
        default=str(CuratedStorageConfig().root),
        help="Directory where curated DuckDB state and Parquet sidecars should be written.",
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
    """Return a summary describing the current phase-1 command state."""

    if dry_run:
        notes = [
            "Phase 1 shell only; source adapters and curated writes are still landing incrementally.",
            "Use this dry run to validate command parsing and the upstream workspace contract.",
        ]
    else:
        notes = [
            "Phase 1 now includes the first non-dry-run curated write path.",
            "Use this command to validate end-to-end source loading, canonical normalization, and curated storage writes.",
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
            notes.append("Concrete source adapters land in steps 1.4 and 1.5.")
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
    """Execute the first non-dry-run curated write path for phase 1."""

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


def main(argv: Sequence[str] | None = None) -> int:
    """Run the current phase-1 CLI shell."""

    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.command == "ingest" and not args.dry_run:
        print(
            "Phase 1 ingest stays summary-only. Re-run with --dry-run, or use curate without --dry-run to write curated outputs.",
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
