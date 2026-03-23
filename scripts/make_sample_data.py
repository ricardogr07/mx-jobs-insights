# ruff: noqa: E402
"""Regenerate tiny Phase-1 source fixtures from a local upstream workspace."""

from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import sqlite3
import sys
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from mexico_linkedin_jobs_portfolio.config import UpstreamWorkspaceConfig
from mexico_linkedin_jobs_portfolio.sources import LocalUpstreamWorkspaceProvider

REQUIRED_TABLES = ("scrape_runs", "jobs", "job_snapshots", "job_enrichments")
DEFAULT_OUTPUT_ROOT = ROOT / "tests" / "data" / "upstream_workspace"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="make_sample_data",
        description="Regenerate tiny Phase-1 source fixtures from a local upstream workspace.",
    )
    parser.add_argument(
        "--upstream-root",
        default=str(ROOT.parent / "LinkedInWebScraper"),
        help="Local LinkedInWebScraper workspace to sample from.",
    )
    parser.add_argument(
        "--output-root",
        default=str(DEFAULT_OUTPUT_ROOT),
        help="Fixture root that will receive state/, exports/, and manifest.json.",
    )
    parser.add_argument(
        "--job-limit",
        type=int,
        default=2,
        help="Maximum number of job IDs to keep in the SQLite slice for one run.",
    )
    parser.add_argument(
        "--csv-row-limit",
        type=int,
        default=1,
        help="Maximum number of rows to keep in each CSV slice.",
    )
    parser.add_argument(
        "--sqlite-run-id",
        help="Explicit scrape run ID to use for the SQLite slice. Defaults to the first ordered run.",
    )
    parser.add_argument(
        "--dated-export",
        help="Explicit relative path under exports/ for the dated CSV slice.",
    )
    parser.add_argument(
        "--latest-export",
        help="Explicit filename under exports/latest for the latest CSV slice.",
    )
    parser.add_argument(
        "--latest-file-mtime",
        help="Override the mtime recorded for the latest CSV slice, in ISO-8601 format.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing output workspace.",
    )
    return parser


def resolve_dated_export(exports_root: Path, requested_relative_path: str | None) -> Path:
    if requested_relative_path:
        candidate = exports_root / requested_relative_path
        if not candidate.is_file():
            raise FileNotFoundError(f"Requested dated export was not found: {candidate}")
        return candidate

    dated_files: list[Path] = []
    for child in sorted(exports_root.iterdir()):
        if child.is_dir() and child.name != "latest":
            dated_files.extend(sorted(child.glob("*.csv")))
    if not dated_files:
        raise FileNotFoundError(f"No dated CSV exports were found under {exports_root}.")
    return dated_files[0]


def resolve_latest_export(exports_root: Path, requested_filename: str | None) -> Path:
    latest_root = exports_root / "latest"
    if requested_filename:
        candidate = latest_root / requested_filename
        if not candidate.is_file():
            raise FileNotFoundError(f"Requested latest export was not found: {candidate}")
        return candidate

    latest_files = sorted(latest_root.glob("*.csv"))
    if not latest_files:
        raise FileNotFoundError(f"No CSV files were found under {latest_root}.")
    return latest_files[0]


def select_sqlite_slice(
    sqlite_path: Path,
    requested_run_id: str | None,
    job_limit: int,
) -> tuple[str, tuple[str, ...]]:
    if job_limit < 1:
        raise ValueError("--job-limit must be at least 1.")

    query = """
    SELECT
        js.run_id,
        js.job_id
    FROM job_snapshots AS js
    JOIN scrape_runs AS sr
        ON sr.id = js.run_id
    ORDER BY COALESCE(sr.finished_at, sr.started_at, js.created_at), js.run_id, js.snapshot_order, js.job_id
    """

    with sqlite3.connect(sqlite_path) as connection:
        rows = connection.execute(query).fetchall()

    if not rows:
        raise RuntimeError(f"No job snapshot rows were found in {sqlite_path}.")

    run_id = requested_run_id or rows[0][0]
    job_ids: list[str] = []
    for candidate_run_id, job_id in rows:
        if candidate_run_id != run_id:
            continue
        if job_id in job_ids:
            continue
        job_ids.append(job_id)
        if len(job_ids) >= job_limit:
            break

    if not job_ids:
        raise RuntimeError(f"Could not find job snapshot rows for run ID {run_id!r}.")

    return run_id, tuple(job_ids)


def copy_csv_slice(source_path: Path, target_path: Path, row_limit: int) -> int:
    if row_limit < 1:
        raise ValueError("--csv-row-limit must be at least 1.")

    with source_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        rows = []
        for index, row in enumerate(reader):
            if index >= row_limit:
                break
            rows.append({key: value for key, value in row.items() if key is not None})

    target_path.parent.mkdir(parents=True, exist_ok=True)
    with target_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return len(rows)


def copy_sqlite_slice(
    source_path: Path, target_path: Path, run_id: str, job_ids: Sequence[str]
) -> None:
    placeholders = ", ".join("?" for _ in job_ids)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(source_path) as source, sqlite3.connect(target_path) as target:
        for table_name in REQUIRED_TABLES:
            create_sql_row = source.execute(
                "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = ?",
                (table_name,),
            ).fetchone()
            if create_sql_row is None or create_sql_row[0] is None:
                raise RuntimeError(f"Could not load schema for required table {table_name!r}.")
            target.execute(create_sql_row[0])

        copy_table(source, target, "scrape_runs", "id = ?", [run_id])
        copy_table(source, target, "jobs", f"job_id IN ({placeholders})", list(job_ids))
        copy_table(
            source,
            target,
            "job_snapshots",
            f"run_id = ? AND job_id IN ({placeholders})",
            [run_id, *job_ids],
        )
        copy_table(
            source,
            target,
            "job_enrichments",
            f"run_id = ? AND job_id IN ({placeholders})",
            [run_id, *job_ids],
        )
        target.commit()


def copy_table(
    source: sqlite3.Connection,
    target: sqlite3.Connection,
    table_name: str,
    where_clause: str,
    parameters: Sequence[str],
) -> None:
    columns = [row[1] for row in source.execute(f"PRAGMA table_info({table_name})")]
    query = f"SELECT {', '.join(columns)} FROM {table_name} WHERE {where_clause}"
    rows = source.execute(query, list(parameters)).fetchall()
    if not rows:
        return
    placeholders = ", ".join("?" for _ in columns)
    target.executemany(
        f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})",
        rows,
    )


def apply_latest_mtime(target_path: Path, iso_timestamp: str) -> None:
    observed_at = datetime.fromisoformat(iso_timestamp)
    timestamp = observed_at.timestamp()
    os.utime(target_path, (timestamp, timestamp))


def write_manifest(
    output_root: Path,
    *,
    latest_target: Path,
    latest_timestamp: str,
    dated_source: Path,
    latest_source: Path,
    run_id: str,
    job_ids: Sequence[str],
) -> None:
    latest_relative_path = latest_target.relative_to(output_root).as_posix()
    manifest = {
        "dataset_name": "upstream_workspace",
        "sqlite_run_id": run_id,
        "sqlite_job_ids": list(job_ids),
        "dated_export_source": dated_source.as_posix(),
        "latest_export_source": latest_source.as_posix(),
        "latest_file_timestamps": {latest_relative_path: latest_timestamp},
    }
    (output_root / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    workspace = UpstreamWorkspaceConfig(root=Path(args.upstream_root), source_mode="auto")
    validation = LocalUpstreamWorkspaceProvider().validate(workspace)
    if not validation.is_valid:
        parser.error("Upstream workspace is invalid: " + "; ".join(validation.errors))
    if not validation.sqlite_available:
        parser.error(f"SQLite source is unavailable at {workspace.sqlite_path}.")
    if not validation.exports_available:
        parser.error(f"CSV exports are unavailable under {workspace.exports_path}.")

    output_root = Path(args.output_root).resolve(strict=False)
    if output_root.exists():
        if not args.force:
            parser.error(
                f"Output root already exists: {output_root}. Re-run with --force to replace it."
            )
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    dated_source = resolve_dated_export(workspace.exports_path, args.dated_export)
    latest_source = resolve_latest_export(workspace.exports_path, args.latest_export)
    run_id, job_ids = select_sqlite_slice(workspace.sqlite_path, args.sqlite_run_id, args.job_limit)

    dated_target = output_root / "exports" / dated_source.parent.name / dated_source.name
    latest_target = output_root / "exports" / "latest" / latest_source.name
    sqlite_target = output_root / "state" / workspace.sqlite_relative_path.name

    dated_rows = copy_csv_slice(dated_source, dated_target, args.csv_row_limit)
    latest_rows = copy_csv_slice(latest_source, latest_target, args.csv_row_limit)
    copy_sqlite_slice(workspace.sqlite_path, sqlite_target, run_id, job_ids)

    latest_timestamp = args.latest_file_mtime or datetime.fromtimestamp(
        latest_source.stat().st_mtime
    ).isoformat(timespec="seconds")
    apply_latest_mtime(latest_target, latest_timestamp)
    write_manifest(
        output_root,
        latest_target=latest_target,
        latest_timestamp=latest_timestamp,
        dated_source=dated_source,
        latest_source=latest_source,
        run_id=run_id,
        job_ids=job_ids,
    )

    summary = {
        "dated_csv_rows": dated_rows,
        "latest_csv_rows": latest_rows,
        "output_root": str(output_root),
        "sqlite_job_ids": list(job_ids),
        "sqlite_run_id": run_id,
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
