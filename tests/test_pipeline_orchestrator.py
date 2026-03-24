from __future__ import annotations

import json
from dataclasses import replace
from datetime import date
from pathlib import Path
from typing import cast

import pytest

from mexico_linkedin_jobs_portfolio.automation import PipelineOrchestrator
from mexico_linkedin_jobs_portfolio.config import PipelineConfig, ReportCadence
from mexico_linkedin_jobs_portfolio.reporting import ReportPipeline
from tests.presentation_fixtures import StubNarrationClient
from tests.sample_data import copy_sample_workspace


class RecordingDocsBuilder:
    def __init__(self) -> None:
        self.calls: list[Path] = []
        self.project_root = Path(__file__).resolve().parents[1]

    def build(self, docs_root: Path) -> tuple[Path | None, str, tuple[str, ...], int]:
        self.calls.append(docs_root)
        return (
            docs_root.parent / "site",
            "mkdocs_build_passed",
            ("mkdocs build validated in test.",),
            0,
        )


def _safe_finalize(config, summary, exit_code):
    if config.dry_run:
        return summary, exit_code

    finalized = replace(summary, pipeline_run_summary_path=config.pipeline_artifacts.run_summary_path)
    config.pipeline_artifacts.resolved_root().mkdir(parents=True, exist_ok=True)
    config.pipeline_artifacts.run_summary_path.write_text(
        json.dumps(finalized.to_display_dict(), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return finalized, exit_code


def _build_config(
    tmp_path: Path,
    *,
    cadence: str,
    as_of_date: date,
    dry_run: bool,
) -> tuple[PipelineConfig, Path]:
    upstream_root = copy_sample_workspace(tmp_path)
    config = PipelineConfig(
        cadence=cast(ReportCadence, cadence),
        upstream_root=upstream_root,
        curated_root=tmp_path / "curated",
        report_root=tmp_path / "reports",
        docs_root=tmp_path / "docs",
        as_of_date=as_of_date,
        dry_run=dry_run,
        openai_api_key="test-key",
        openai_model="gpt-5.4-nano",
        public_key_salt="test-salt",
    )
    return config, upstream_root


def test_pipeline_dry_run_summarizes_workspace_and_period(tmp_path: Path) -> None:
    config, _ = _build_config(
        tmp_path,
        cadence="weekly",
        as_of_date=date(2026, 3, 23),
        dry_run=True,
    )

    summary, exit_code = PipelineOrchestrator().run(config)

    assert exit_code == 0
    assert summary.status == "pipeline_dry_run_ready"
    assert summary.workspace_status == "workspace_valid"
    assert summary.curate_status == "curation_dry_run_ready"
    assert summary.report_status == "report_dry_run_planned"
    assert summary.site_status == "site_dry_run_planned"
    assert summary.docs_status == "mkdocs_build_planned"
    assert summary.resolved_source_mode == "sqlite"
    assert summary.period_id == "2026-W12"
    assert summary.source_run_count == 1
    assert summary.publish_ready is False
    assert summary.pipeline_run_summary_path is None


@pytest.mark.parametrize(
    (
        "cadence",
        "as_of_date",
        "expected_period_id",
        "expected_observation_count",
        "expected_job_count",
        "expected_public_row_count",
    ),
    [
        ("weekly", date(2026, 3, 30), "2026-W13", 0, 0, 0),
        ("monthly", date(2026, 4, 1), "2026-03", 2, 2, 2),
    ],
)
def test_pipeline_non_dry_run_reuses_fixture_backed_flows(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    cadence: str,
    as_of_date: date,
    expected_period_id: str,
    expected_observation_count: int,
    expected_job_count: int,
    expected_public_row_count: int,
) -> None:
    config, _ = _build_config(
        tmp_path,
        cadence=cadence,
        as_of_date=as_of_date,
        dry_run=False,
    )
    docs_builder = RecordingDocsBuilder()
    orchestrator = PipelineOrchestrator(
        report_pipeline=ReportPipeline(narration_client=StubNarrationClient()),
        docs_builder=docs_builder,
    )
    monkeypatch.setattr(PipelineOrchestrator, "_finalize", staticmethod(_safe_finalize))

    summary, exit_code = orchestrator.run(config)

    assert exit_code == 0
    assert summary.status == "pipeline_written"
    assert summary.publish_ready is True
    assert summary.period_id == expected_period_id
    assert summary.workspace_status == "workspace_valid"
    assert summary.curate_status == "curation_written"
    assert summary.report_status == "report_written"
    assert summary.site_status == "site_written"
    assert summary.docs_status == "mkdocs_build_passed"
    assert summary.resolved_source_mode == "sqlite"
    assert summary.source_run_count == 1
    assert summary.observation_count == expected_observation_count
    assert summary.job_count == expected_job_count
    assert summary.public_row_count == expected_public_row_count
    assert summary.duckdb_path is not None and summary.duckdb_path.is_file()
    assert summary.report_run_summary_path is not None and summary.report_run_summary_path.is_file()
    assert summary.site_run_summary_path is not None and summary.site_run_summary_path.is_file()
    assert summary.pipeline_run_summary_path is not None and summary.pipeline_run_summary_path.is_file()
    assert summary.site_output_root is not None
    assert summary.site_output_root.name == "site"
    assert (config.docs_root / "development" / "index.md").is_file()
    assert docs_builder.calls == [config.docs_root]


def test_pipeline_non_dry_run_fails_closed_when_report_runtime_env_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    upstream_root = copy_sample_workspace(tmp_path)
    config = PipelineConfig(
        cadence="monthly",
        upstream_root=upstream_root,
        curated_root=tmp_path / "curated",
        report_root=tmp_path / "reports",
        docs_root=tmp_path / "docs",
        as_of_date=date(2026, 4, 1),
        dry_run=False,
    )
    monkeypatch.setattr(PipelineOrchestrator, "_finalize", staticmethod(_safe_finalize))

    summary, exit_code = PipelineOrchestrator().run(config)

    assert exit_code == 1
    assert summary.status == "pipeline_report_failed"
    assert summary.curate_status == "curation_written"
    assert summary.report_status == "report_config_invalid"
    assert summary.site_status == "not_run"
    assert summary.docs_status == "not_run"
    assert summary.publish_ready is False
    assert summary.pipeline_run_summary_path is not None and summary.pipeline_run_summary_path.is_file()
    assert "OPENAI_API_KEY" in "\n".join(summary.notes)
    assert "MX_JOBS_OPENAI_MODEL" in "\n".join(summary.notes)
    assert "MX_JOBS_PUBLIC_KEY_SALT" in "\n".join(summary.notes)









