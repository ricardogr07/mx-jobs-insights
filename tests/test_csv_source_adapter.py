from __future__ import annotations

import csv
import os
from datetime import datetime
from pathlib import Path

import pytest
from sample_data import copy_sample_workspace

from mexico_linkedin_jobs_portfolio.config import UpstreamWorkspaceConfig
from mexico_linkedin_jobs_portfolio.interfaces.cli.main import main
from mexico_linkedin_jobs_portfolio.sources import CsvSourceAdapter

CSV_FIELDNAMES = [
    "Title",
    "Company",
    "Location",
    "Remote",
    "SeniorityLevel",
    "EmploymentType",
    "Industries",
    "DatePosted",
    "Description",
    "Url",
    "JobID",
    "ShortDescription",
    "TechStack",
    "YoE",
    "English",
    "MinYoE",
]


def write_csv(
    path: Path, rows: list[dict[str, str]], *, modified_at: datetime | None = None
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    if modified_at is not None:
        timestamp = modified_at.timestamp()
        os.utime(path, (timestamp, timestamp))


def test_csv_source_adapter_loads_dated_and_latest_exports(tmp_path: Path) -> None:
    root = copy_sample_workspace(tmp_path, sqlite=False, csv=True)
    adapter = CsvSourceAdapter()

    observations, entities, summary = adapter.load(
        UpstreamWorkspaceConfig(root=root, source_mode="csv")
    )

    assert adapter.is_available(UpstreamWorkspaceConfig(root=root, source_mode="csv")) is True
    assert len(observations) == 2
    assert len(entities) == 2
    assert summary.status == "csv_loaded"
    assert summary.observation_count == 2
    assert summary.entity_count == 2
    assert any("Loaded 2 CSV rows across 2 files." in note for note in summary.notes)
    assert any("Deduplicated 0 repeated job observations" in note for note in summary.notes)
    assert any(
        "Used file modification timestamps for 1 latest-export file(s)" in note
        for note in summary.notes
    )

    observations_by_job = {observation.job_id: observation for observation in observations}
    dated_observation = observations_by_job["job-1"]
    latest_observation = observations_by_job["job-2"]

    assert dated_observation.observed_at.isoformat() == "2026-03-22"
    assert dated_observation.city == "Monterrey"
    assert latest_observation.observed_at.isoformat() == "2026-03-23"
    assert latest_observation.city == "Guadalajara"

    entities_by_job = {entity.job_id: entity for entity in entities}
    assert entities_by_job["job-1"].tech_stack == ("Python", "SQL", "dbt")
    assert entities_by_job["job-1"].english_required is True
    assert entities_by_job["job-2"].english_required is False
    assert entities_by_job["job-2"].minimum_years_experience == 2.0


def test_csv_source_adapter_deduplicates_repeated_job_observations(tmp_path: Path) -> None:
    root = tmp_path / "LinkedInWebScraper"
    root.mkdir()
    duplicate_row = {
        "Title": "Senior Data Scientist",
        "Company": "Acme Analytics",
        "Location": "Monterrey, Nuevo Leon, Mexico",
        "Remote": "Remote",
        "SeniorityLevel": "Senior level",
        "EmploymentType": "Full-time",
        "Industries": "Technology",
        "DatePosted": "2026-03-20",
        "Description": "Build forecasting models for retail demand.",
        "Url": "https://example.com/jobs/1",
        "JobID": "job-1",
        "ShortDescription": "Lead forecasting work across ML projects.",
        "TechStack": "Python, SQL, dbt",
        "YoE": "3+ years",
        "English": "Yes",
        "MinYoE": "3",
    }
    write_csv(root / "exports" / "2026-03-22" / "a.csv", [duplicate_row])
    write_csv(root / "exports" / "2026-03-22" / "b.csv", [duplicate_row])

    observations, _, summary = CsvSourceAdapter().load(
        UpstreamWorkspaceConfig(root=root, source_mode="csv")
    )

    assert len(observations) == 1
    assert any("Deduplicated 1 repeated job observations" in note for note in summary.notes)


def test_csv_source_adapter_rejects_missing_required_columns(tmp_path: Path) -> None:
    root = tmp_path / "LinkedInWebScraper"
    root.mkdir()
    broken_file = root / "exports" / "latest" / "broken.csv"
    broken_file.parent.mkdir(parents=True)
    broken_file.write_text(
        "Title,Location,DatePosted\nData Scientist,Monterrey,2026-03-20\n",
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="missing required columns"):
        CsvSourceAdapter().load(UpstreamWorkspaceConfig(root=root, source_mode="csv"))


def test_cli_csv_dry_run_outputs_loaded_counts(capsys, tmp_path: Path) -> None:
    root = copy_sample_workspace(tmp_path, sqlite=False, csv=True)

    exit_code = main(["ingest", "--source", "csv", "--dry-run", "--upstream-root", str(root)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert '"resolved_source_mode": "csv"' in captured.out
    assert '"observation_count": 2' in captured.out
    assert '"entity_count": 2' in captured.out
    assert '"status": "csv_loaded"' in captured.out
