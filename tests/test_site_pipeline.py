from __future__ import annotations

import csv
import json
from pathlib import Path

from mexico_linkedin_jobs_portfolio.config import SiteConfig
from mexico_linkedin_jobs_portfolio.interfaces.cli.main import main
from mexico_linkedin_jobs_portfolio.presentation import ReportArtifactIndexReader, SitePipeline
from tests.presentation_fixtures import write_report_fixtures


def test_report_artifact_index_reader_discovers_weekly_and_monthly_reports(tmp_path: Path) -> None:
    _, report_root = write_report_fixtures(tmp_path)

    report_index = ReportArtifactIndexReader().load(report_root)

    assert report_index.report_count == 2
    assert report_index.latest_monthly is not None
    assert report_index.latest_weekly is not None
    assert report_index.latest_monthly.period_id == "2026-03"
    assert report_index.latest_weekly.period_id == "2026-W13"


def test_site_pipeline_dry_run_summarizes_public_index(tmp_path: Path) -> None:
    _, report_root = write_report_fixtures(tmp_path)
    docs_root = tmp_path / "docs"

    summary, exit_code = SitePipeline().run(
        SiteConfig(
            report_root=report_root,
            docs_root=docs_root,
            dry_run=True,
        )
    )

    assert exit_code == 0
    assert summary.status == "site_dry_run_ready"
    assert summary.report_count == 2
    assert summary.latest_monthly_period_id == "2026-03"
    assert summary.latest_weekly_period_id == "2026-W13"
    assert summary.generated_page_count == 0
    assert not docs_root.exists()


def test_site_pipeline_write_generates_pages_and_public_assets(tmp_path: Path) -> None:
    _, report_root = write_report_fixtures(tmp_path)
    docs_root = tmp_path / "docs"

    summary, exit_code = SitePipeline().run(
        SiteConfig(
            report_root=report_root,
            docs_root=docs_root,
            dry_run=False,
        )
    )

    assert exit_code == 0
    assert summary.status == "site_written"
    assert summary.generated_page_count == 7
    assert summary.copied_asset_count == 6
    assert (docs_root / "index.md").is_file()
    assert (docs_root / "public" / "weekly" / "index.md").is_file()
    assert (docs_root / "public" / "monthly" / "index.md").is_file()
    assert (docs_root / "public" / "downloads" / "index.md").is_file()
    assert (docs_root / "public" / "methodology.md").is_file()
    assert (docs_root / "public" / "weekly" / "2026-W13.md").is_file()
    assert (docs_root / "public" / "monthly" / "2026-03.md").is_file()

    copied_csv = docs_root / "public" / "assets" / "monthly" / "2026-03" / "public_jobs.csv"
    copied_html = docs_root / "public" / "assets" / "monthly" / "2026-03" / "report.en.html"
    assert copied_csv.is_file()
    assert copied_html.is_file()
    assert not (docs_root / "public" / "assets" / "monthly" / "2026-03" / "metrics.json").exists()

    with copied_csv.open("r", encoding="utf-8", newline="") as handle:
        header = next(csv.reader(handle))
    assert "company_name" not in header
    assert "job_url" not in header
    assert "description_text" not in header

    landing_text = (docs_root / "index.md").read_text(encoding="utf-8")
    assert "Latest Monthly Report" in landing_text
    assert "Portafolio de Vacantes de LinkedIn en Mexico" in landing_text


def test_site_pipeline_handles_empty_archive_root(tmp_path: Path) -> None:
    report_root = tmp_path / "reports"
    docs_root = tmp_path / "docs"
    report_root.mkdir()

    summary, exit_code = SitePipeline().run(
        SiteConfig(
            report_root=report_root,
            docs_root=docs_root,
            dry_run=True,
        )
    )

    assert exit_code == 1
    assert summary.status == "site_index_empty"


def test_cli_site_dry_run_outputs_summary(capsys, tmp_path: Path) -> None:
    _, report_root = write_report_fixtures(tmp_path)
    docs_root = tmp_path / "docs"

    exit_code = main(
        [
            "site",
            "--report-root",
            str(report_root),
            "--docs-root",
            str(docs_root),
            "--dry-run",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["status"] == "site_dry_run_ready"
    assert payload["latest_monthly_period_id"] == "2026-03"
    assert payload["latest_weekly_period_id"] == "2026-W13"
    assert payload["report_count"] == 2
