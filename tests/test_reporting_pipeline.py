from __future__ import annotations

import csv
import hashlib
import json
from datetime import date
from pathlib import Path

from mexico_linkedin_jobs_portfolio.analytics import CuratedDatasetReader, build_report_metrics
from mexico_linkedin_jobs_portfolio.analytics.periods import resolve_closed_period
from mexico_linkedin_jobs_portfolio.config import CuratedStorageConfig, ReportConfig
from mexico_linkedin_jobs_portfolio.curation import DuckDBCuratedStore, build_curated_batch
from mexico_linkedin_jobs_portfolio.interfaces.cli.main import main
from mexico_linkedin_jobs_portfolio.models import (
    CanonicalEntityRecord,
    CanonicalObservationRecord,
    GeneratedNarrative,
    IngestionRunSummary,
)
from mexico_linkedin_jobs_portfolio.reporting import ReportPipeline, build_narration_request_body


class StubNarrationClient:
    def __init__(self) -> None:
        self.metrics_payload: dict[str, object] | None = None

    def generate_bilingual_narrative(self, metrics) -> GeneratedNarrative:
        self.metrics_payload = metrics.narrative_payload()
        return GeneratedNarrative(
            model="stub-model",
            en_headline="Weekly demand stayed concentrated in two cities.",
            en_bullets=(
                "Monterrey and Guadalajara carried the visible job volume.",
                "Remote and hybrid roles split the observed mix.",
                "Python remained the most common shared technology term.",
            ),
            es_headline="La demanda semanal se concentro en dos ciudades.",
            es_bullets=(
                "Monterrey y Guadalajara concentraron el volumen visible.",
                "Las vacantes remotas e hibridas dividieron la mezcla observada.",
                "Python se mantuvo como la tecnologia compartida mas frecuente.",
            ),
        )


def build_sample_curated_batch(tmp_path: Path):
    summary = IngestionRunSummary(
        command_name="sqlite_adapter",
        source_mode="sqlite",
        upstream_root=tmp_path / "LinkedInWebScraper",
        dry_run=True,
        resolved_source_mode="sqlite",
        observation_count=3,
        entity_count=2,
        status="sqlite_loaded",
        notes=("Loaded canonical test records.",),
    )
    observations = [
        CanonicalObservationRecord(
            job_id="job-1",
            observed_at=date(2026, 3, 22),
            source_mode="sqlite",
            city="Monterrey",
            title="Senior Data Scientist",
            state="Nuevo Leon",
            reported_date=date(2026, 3, 20),
            source_run_id="run-1",
            remote_type="Remote",
            seniority_level="Senior level",
            employment_type="Full-time",
        ),
        CanonicalObservationRecord(
            job_id="job-2",
            observed_at=date(2026, 3, 22),
            source_mode="sqlite",
            city="Guadalajara",
            title="ML Engineer",
            state="Jalisco",
            reported_date=date(2026, 3, 21),
            source_run_id="run-1",
            remote_type="Hybrid",
            seniority_level="Mid level",
            employment_type="Contract",
        ),
        CanonicalObservationRecord(
            job_id="job-1",
            observed_at=date(2026, 3, 23),
            source_mode="sqlite",
            city="Monterrey",
            title="Senior Data Scientist",
            state="Nuevo Leon",
            reported_date=date(2026, 3, 20),
            source_run_id="run-2",
            remote_type="Remote",
            seniority_level="Senior level",
            employment_type="Full-time",
        ),
    ]
    entities = [
        CanonicalEntityRecord(
            job_id="job-1",
            canonical_title="Senior Data Scientist",
            company_name="Acme Analytics",
            job_url="https://example.com/jobs/1",
            description_text="Build forecasting models for retail demand.",
            industry="Technology",
            english_required=True,
            minimum_years_experience=3.0,
            tech_stack=("Python", "SQL", "dbt"),
        ),
        CanonicalEntityRecord(
            job_id="job-2",
            canonical_title="ML Engineer",
            company_name="Beta Labs",
            job_url="https://example.com/jobs/2",
            description_text="Support production ML systems.",
            industry="Consulting",
            english_required=False,
            minimum_years_experience=2.0,
            tech_stack=("Python", "Airflow"),
        ),
    ]
    return build_curated_batch(observations, entities, summary)


def write_curated_fixture(tmp_path: Path) -> Path:
    curated_root = tmp_path / "curated"
    batch = build_sample_curated_batch(tmp_path)
    DuckDBCuratedStore(CuratedStorageConfig(root=curated_root)).persist_batch(batch)
    return curated_root


def test_resolve_closed_period_uses_closed_iso_week_and_calendar_month() -> None:
    weekly = resolve_closed_period("weekly", date(2026, 3, 23))
    monthly = resolve_closed_period("monthly", date(2026, 4, 1))

    assert weekly.period_id == "2026-W12"
    assert weekly.start_date.isoformat() == "2026-03-16"
    assert weekly.end_date.isoformat() == "2026-03-22"
    assert monthly.period_id == "2026-03"
    assert monthly.start_date.isoformat() == "2026-03-01"
    assert monthly.end_date.isoformat() == "2026-03-31"


def test_build_report_metrics_uses_observed_at_and_latest_job_per_period(tmp_path: Path) -> None:
    curated_root = write_curated_fixture(tmp_path)
    dataset = CuratedDatasetReader().load(CuratedStorageConfig(root=curated_root))

    weekly_result = build_report_metrics(
        dataset.records, resolve_closed_period("weekly", date(2026, 3, 23))
    )
    monthly_result = build_report_metrics(
        dataset.records, resolve_closed_period("monthly", date(2026, 4, 1))
    )

    assert weekly_result.metrics.observation_count == 2
    assert weekly_result.metrics.job_count == 2
    assert weekly_result.metrics.source_run_count == 1
    assert monthly_result.metrics.observation_count == 3
    assert monthly_result.metrics.job_count == 2
    assert monthly_result.metrics.source_run_count == 2

    latest_job_one = next(job for job in monthly_result.latest_jobs if job.job_id == "job-1")
    assert latest_job_one.observed_at.isoformat() == "2026-03-23"
    assert monthly_result.metrics.tech_stack_counts[0].label == "Python"
    assert monthly_result.metrics.tech_stack_counts[0].count == 2


def test_build_narration_request_body_contains_only_aggregate_metrics(tmp_path: Path) -> None:
    curated_root = write_curated_fixture(tmp_path)
    dataset = CuratedDatasetReader().load(CuratedStorageConfig(root=curated_root))
    metrics = build_report_metrics(
        dataset.records, resolve_closed_period("monthly", date(2026, 4, 1))
    ).metrics

    body = build_narration_request_body(metrics, "gpt-5.4")
    serialized = json.dumps(body, sort_keys=True)

    assert body["store"] is False
    assert "job-1" not in serialized
    assert "https://example.com/jobs/1" not in serialized
    assert "Build forecasting models for retail demand." not in serialized
    assert "top_company_counts" in serialized
    assert "Acme Analytics" in serialized


def test_report_pipeline_dry_run_summarizes_period_without_artifacts(tmp_path: Path) -> None:
    curated_root = write_curated_fixture(tmp_path)
    output_root = tmp_path / "reports"

    summary, exit_code = ReportPipeline().run(
        ReportConfig(
            cadence="weekly",
            as_of_date=date(2026, 3, 23),
            curated_root=curated_root,
            output_root=output_root,
            dry_run=True,
        )
    )

    assert exit_code == 0
    assert summary.status == "report_dry_run_ready"
    assert summary.period_id == "2026-W12"
    assert summary.job_count == 2
    assert summary.public_row_count == 2
    assert summary.artifact_dir is None
    assert not output_root.exists()


def test_report_pipeline_dry_run_handles_empty_period(tmp_path: Path) -> None:
    curated_root = write_curated_fixture(tmp_path)

    summary, exit_code = ReportPipeline().run(
        ReportConfig(
            cadence="monthly",
            as_of_date=date(2026, 3, 15),
            curated_root=curated_root,
            output_root=tmp_path / "reports",
            dry_run=True,
        )
    )

    assert exit_code == 0
    assert summary.status == "report_dry_run_ready"
    assert summary.period_id == "2026-02"
    assert summary.observation_count == 0
    assert summary.job_count == 0


def test_report_pipeline_write_handles_empty_period_without_openai(tmp_path: Path) -> None:
    curated_root = write_curated_fixture(tmp_path)

    summary, exit_code = ReportPipeline().run(
        ReportConfig(
            cadence="monthly",
            as_of_date=date(2026, 3, 15),
            curated_root=curated_root,
            output_root=tmp_path / "reports-empty",
            dry_run=False,
            openai_api_key="test-key",
            openai_model="gpt-5.4-nano",
            public_key_salt="test-salt",
        )
    )

    assert exit_code == 0
    assert summary.status == "report_written"
    assert summary.narration_status == "skipped_empty_period"
    assert summary.period_id == "2026-02"
    assert summary.job_count == 0
    assert summary.public_row_count == 0
    assert summary.metrics_path is not None and summary.metrics_path.is_file()
    assert summary.public_csv_path is not None and summary.public_csv_path.is_file()
    assert summary.run_summary_path is not None and summary.run_summary_path.is_file()
    with summary.public_csv_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows == []
    assert "Skipped OpenAI narration because the selected period contains no jobs." in "\n".join(
        summary.notes
    )


def test_report_pipeline_writes_artifacts_with_mock_openai_base_url(tmp_path: Path) -> None:
    curated_root = write_curated_fixture(tmp_path)

    summary, exit_code = ReportPipeline().run(
        ReportConfig(
            cadence="monthly",
            as_of_date=date(2026, 4, 1),
            curated_root=curated_root,
            output_root=tmp_path / "reports-mock",
            dry_run=False,
            openai_api_key="test-key",
            openai_model="gpt-5.4-nano",
            public_key_salt="test-salt",
            openai_base_url="mock://responses",
        )
    )

    assert exit_code == 0
    assert summary.status == "report_written"
    assert summary.narration_status == "generated"
    assert summary.metrics_path is not None and summary.metrics_path.is_file()
    assert summary.markdown_paths is not None
    markdown_text = summary.markdown_paths["en"].read_text(encoding="utf-8")
    assert "distinct jobs were observed during" in markdown_text


def test_report_pipeline_fails_closed_when_runtime_env_is_missing(tmp_path: Path) -> None:
    curated_root = write_curated_fixture(tmp_path)

    summary, exit_code = ReportPipeline().run(
        ReportConfig(
            cadence="monthly",
            as_of_date=date(2026, 4, 1),
            curated_root=curated_root,
            output_root=tmp_path / "reports",
            dry_run=False,
        )
    )

    assert exit_code == 1
    assert summary.status == "report_config_invalid"
    assert "OPENAI_API_KEY" in "\n".join(summary.notes)
    assert "MX_JOBS_OPENAI_MODEL" in "\n".join(summary.notes)
    assert "MX_JOBS_PUBLIC_KEY_SALT" in "\n".join(summary.notes)


def test_report_pipeline_writes_artifacts_and_public_csv(tmp_path: Path) -> None:
    curated_root = write_curated_fixture(tmp_path)
    stub_client = StubNarrationClient()

    summary, exit_code = ReportPipeline(narration_client=stub_client).run(
        ReportConfig(
            cadence="monthly",
            as_of_date=date(2026, 4, 1),
            curated_root=curated_root,
            output_root=tmp_path / "reports",
            dry_run=False,
            openai_api_key="test-key",
            openai_model="gpt-5.4",
            public_key_salt="test-salt",
        )
    )

    assert exit_code == 0
    assert summary.status == "report_written"
    assert summary.narration_status == "generated"
    assert summary.period_id == "2026-03"
    assert summary.metrics_path is not None and summary.metrics_path.is_file()
    assert summary.public_csv_path is not None and summary.public_csv_path.is_file()
    assert summary.run_summary_path is not None and summary.run_summary_path.is_file()
    assert summary.artifact_dir is not None
    assert summary.markdown_paths == {
        "en": summary.artifact_dir / "report.en.md",
        "es": summary.artifact_dir / "report.es.md",
    }
    assert summary.html_paths == {
        "en": summary.artifact_dir / "report.en.html",
        "es": summary.artifact_dir / "report.es.html",
    }

    markdown_text = summary.markdown_paths["en"].read_text(encoding="utf-8")
    html_text = summary.html_paths["es"].read_text(encoding="utf-8")
    assert "Weekly demand stayed concentrated in two cities." in markdown_text
    assert "La demanda semanal se concentro en dos ciudades." in html_text

    with summary.public_csv_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 2
    assert "company_name" not in rows[0]
    assert "job_url" not in rows[0]
    assert "description_text" not in rows[0]
    job_one_row = next(row for row in rows if row["title"] == "Senior Data Scientist")
    assert job_one_row["public_job_key"] == hashlib.sha256(b"test-salt:job-1").hexdigest()
    assert job_one_row["public_job_key"] != "job-1"
    assert job_one_row["tech_stack"] == "Python | SQL | dbt"

    metrics_payload = json.loads(summary.metrics_path.read_text(encoding="utf-8"))
    assert metrics_payload["job_count"] == 2
    assert stub_client.metrics_payload is not None
    assert "job-1" not in json.dumps(stub_client.metrics_payload, sort_keys=True)


def test_cli_report_weekly_dry_run_outputs_summary(capsys, tmp_path: Path) -> None:
    curated_root = write_curated_fixture(tmp_path)

    exit_code = main(
        [
            "report",
            "--cadence",
            "weekly",
            "--as-of",
            "2026-03-23",
            "--curated-root",
            str(curated_root),
            "--output-root",
            str(tmp_path / "reports"),
            "--dry-run",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["status"] == "report_dry_run_ready"
    assert payload["period_id"] == "2026-W12"
    assert payload["job_count"] == 2
    assert payload["resolved_period"]["period_end"] == "2026-03-22"


def test_cli_report_monthly_write_outputs_artifacts(capsys, tmp_path: Path, monkeypatch) -> None:
    curated_root = write_curated_fixture(tmp_path)

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("MX_JOBS_OPENAI_MODEL", "gpt-5.4")
    monkeypatch.setenv("MX_JOBS_PUBLIC_KEY_SALT", "test-salt")
    monkeypatch.setattr(
        "mexico_linkedin_jobs_portfolio.reporting.pipeline.OpenAINarrationClient.generate_bilingual_narrative",
        lambda self, metrics: GeneratedNarrative(
            model="patched-model",
            en_headline="Monthly hiring remained concentrated in analytics roles.",
            en_bullets=("One", "Two", "Three"),
            es_headline="La contratacion mensual se concentro en roles de analitica.",
            es_bullets=("Uno", "Dos", "Tres"),
        ),
    )

    exit_code = main(
        [
            "report",
            "--cadence",
            "monthly",
            "--as-of",
            "2026-04-01",
            "--curated-root",
            str(curated_root),
            "--output-root",
            str(tmp_path / "reports"),
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["status"] == "report_written"
    assert payload["period_id"] == "2026-03"
    assert payload["narration_status"] == "generated"
    assert Path(payload["metrics_path"]).is_file()
    assert Path(payload["public_csv_path"]).is_file()
    assert Path(payload["markdown_paths"]["en"]).is_file()
    assert Path(payload["html_paths"]["es"]).is_file()
