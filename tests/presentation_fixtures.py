from __future__ import annotations

from datetime import date
from pathlib import Path

from mexico_linkedin_jobs_portfolio.config import CuratedStorageConfig, ReportConfig
from mexico_linkedin_jobs_portfolio.curation import DuckDBCuratedStore, build_curated_batch
from mexico_linkedin_jobs_portfolio.models import (
    CanonicalEntityRecord,
    CanonicalObservationRecord,
    GeneratedNarrative,
    IngestionRunSummary,
)
from mexico_linkedin_jobs_portfolio.reporting import ReportPipeline


class StubNarrationClient:
    def generate_bilingual_narrative(self, metrics) -> GeneratedNarrative:
        return GeneratedNarrative(
            model="stub-model",
            en_headline="Hiring demand remained concentrated in analytics roles.",
            en_bullets=(
                "Monterrey and Guadalajara carried the visible demand.",
                "Remote and hybrid roles split the observed mix.",
                "Python remained the most common shared technology term.",
            ),
            es_headline="La demanda se concentro en roles de analitica.",
            es_bullets=(
                "Monterrey y Guadalajara concentraron la demanda visible.",
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
        observation_count=4,
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
        CanonicalObservationRecord(
            job_id="job-2",
            observed_at=date(2026, 3, 24),
            source_mode="sqlite",
            city="Guadalajara",
            title="ML Engineer",
            state="Jalisco",
            reported_date=date(2026, 3, 21),
            source_run_id="run-2",
            remote_type="Hybrid",
            seniority_level="Mid level",
            employment_type="Contract",
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


def write_report_fixtures(tmp_path: Path) -> tuple[Path, Path]:
    curated_root = write_curated_fixture(tmp_path)
    report_root = tmp_path / "reports"
    pipeline = ReportPipeline(narration_client=StubNarrationClient())

    for cadence, as_of in (("monthly", date(2026, 4, 1)), ("weekly", date(2026, 3, 30))):
        summary, exit_code = pipeline.run(
            ReportConfig(
                cadence=cadence,
                as_of_date=as_of,
                curated_root=curated_root,
                output_root=report_root,
                dry_run=False,
                openai_api_key="test-key",
                openai_model="gpt-5.4-nano",
                public_key_salt="test-salt",
            )
        )
        if exit_code != 0:
            raise RuntimeError(f"Failed to build report fixture for {cadence}: {summary.status}")

    return curated_root, report_root
