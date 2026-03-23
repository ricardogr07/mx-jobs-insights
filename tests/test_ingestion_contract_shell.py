from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import duckdb
from sample_data import copy_sample_workspace

from mexico_linkedin_jobs_portfolio.config import CuratedStorageConfig, UpstreamWorkspaceConfig
from mexico_linkedin_jobs_portfolio.curation import DuckDBCuratedStore, build_curated_batch
from mexico_linkedin_jobs_portfolio.interfaces.cli.main import main
from mexico_linkedin_jobs_portfolio.models import (
    CanonicalEntityRecord,
    CanonicalObservationRecord,
    IngestionRunSummary,
)
from mexico_linkedin_jobs_portfolio.sources import (
    CsvSourceAdapter,
    LocalUpstreamWorkspaceProvider,
    SQLiteSourceAdapter,
    resolve_source_mode,
)
from mexico_linkedin_jobs_portfolio.sources.sqlite import split_location
from scripts.make_sample_data import main as make_sample_data_main


def test_workspace_config_builds_expected_paths() -> None:
    config = UpstreamWorkspaceConfig(root=Path("../LinkedInWebScraper"), source_mode="sqlite")

    assert config.sqlite_path == config.resolved_root() / "state" / "linkedin_jobs.sqlite"
    assert config.exports_path == config.resolved_root() / "exports"


def test_resolve_source_mode_prefers_sqlite_for_auto() -> None:
    assert resolve_source_mode("auto", sqlite_available=True, exports_available=True) == "sqlite"
    assert resolve_source_mode("auto", sqlite_available=False, exports_available=True) == "csv"
    assert resolve_source_mode("auto", sqlite_available=False, exports_available=False) is None


def test_split_location_treats_mexico_country_token_as_country() -> None:
    city, state, country = split_location("Ciudad de Mexico, M\u00e9xico")

    assert city == "Ciudad de Mexico"
    assert state is None
    assert country == "Mexico"


def test_workspace_provider_validates_local_workspace_shape(tmp_path: Path) -> None:
    root = copy_sample_workspace(tmp_path, git_metadata=True)
    provider = LocalUpstreamWorkspaceProvider(branch_probe=lambda _root, _ref: True)

    result = provider.validate(UpstreamWorkspaceConfig(root=root, source_mode="auto"))

    assert result.is_valid is True
    assert result.resolved_source_mode == "sqlite"
    assert result.available_sources == ("sqlite", "csv")
    assert result.preferred_ref_available is True
    assert result.latest_exports_available is True
    assert result.dated_export_directories == ("2026-03-22",)


def test_sqlite_source_adapter_loads_canonical_records(tmp_path: Path) -> None:
    root = copy_sample_workspace(tmp_path, sqlite=True, csv=False)
    adapter = SQLiteSourceAdapter()

    observations, entities, summary = adapter.load(
        UpstreamWorkspaceConfig(root=root, source_mode="sqlite")
    )

    assert adapter.is_available(UpstreamWorkspaceConfig(root=root, source_mode="sqlite")) is True
    assert len(observations) == 2
    assert len(entities) == 2
    assert summary.status == "sqlite_loaded"
    assert summary.observation_count == 2
    assert summary.entity_count == 2

    first_observation = observations[0]
    assert first_observation.job_id == "job-1"
    assert first_observation.city == "Monterrey"
    assert first_observation.state == "Nuevo Leon"
    assert first_observation.country == "Mexico"
    assert first_observation.remote_type == "Remote"
    assert first_observation.reported_date is not None
    assert first_observation.reported_date.isoformat() == "2026-03-20"
    assert first_observation.observed_at.isoformat() == "2026-03-22"

    entities_by_job_id = {entity.job_id: entity for entity in entities}
    job_one = entities_by_job_id["job-1"]
    assert job_one.company_name == "Acme Analytics"
    assert job_one.industry == "Technology"
    assert job_one.english_required is True
    assert job_one.minimum_years_experience == 3.0
    assert job_one.tech_stack == ("Python", "SQL", "dbt")
    assert job_one.description_text == "Build forecasting models for retail demand."


def test_fixture_workspace_keeps_entity_projection_aligned_across_sources(tmp_path: Path) -> None:
    root = copy_sample_workspace(tmp_path)

    _, sqlite_entities, _ = SQLiteSourceAdapter().load(
        UpstreamWorkspaceConfig(root=root, source_mode="sqlite")
    )
    _, csv_entities, _ = CsvSourceAdapter().load(
        UpstreamWorkspaceConfig(root=root, source_mode="csv")
    )

    sqlite_by_job_id = {entity.job_id: entity for entity in sqlite_entities}
    csv_by_job_id = {entity.job_id: entity for entity in csv_entities}

    assert sqlite_by_job_id.keys() == csv_by_job_id.keys()
    for job_id in sorted(sqlite_by_job_id):
        sqlite_entity = sqlite_by_job_id[job_id]
        csv_entity = csv_by_job_id[job_id]
        assert sqlite_entity.canonical_title == csv_entity.canonical_title
        assert sqlite_entity.company_name == csv_entity.company_name
        assert sqlite_entity.job_url == csv_entity.job_url
        assert sqlite_entity.description_text == csv_entity.description_text
        assert sqlite_entity.industry == csv_entity.industry
        assert sqlite_entity.english_required == csv_entity.english_required
        assert sqlite_entity.minimum_years_experience == csv_entity.minimum_years_experience
        assert sqlite_entity.tech_stack == csv_entity.tech_stack


def test_workspace_provider_reports_invalid_requested_source(tmp_path: Path) -> None:
    root = copy_sample_workspace(tmp_path, sqlite=False, csv=True)
    provider = LocalUpstreamWorkspaceProvider(branch_probe=lambda _root, _ref: None)

    result = provider.validate(UpstreamWorkspaceConfig(root=root, source_mode="sqlite"))

    assert result.is_valid is False
    assert result.resolved_source_mode is None
    assert result.errors


def test_cli_requires_dry_run_for_shell_only_phase(capsys) -> None:
    exit_code = main(["ingest", "--source", "sqlite"])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "--dry-run" in captured.err


def test_cli_sqlite_ingest_dry_run_outputs_loaded_counts(capsys, tmp_path: Path) -> None:
    root = copy_sample_workspace(tmp_path, sqlite=True, csv=False)

    exit_code = main(["ingest", "--source", "sqlite", "--dry-run", "--upstream-root", str(root)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert '"command_name": "ingest"' in captured.out
    assert '"resolved_source_mode": "sqlite"' in captured.out
    assert '"observation_count": 2' in captured.out
    assert '"entity_count": 2' in captured.out
    assert '"status": "sqlite_loaded"' in captured.out


def test_cli_sqlite_dry_run_outputs_loaded_counts(capsys, tmp_path: Path) -> None:
    root = copy_sample_workspace(tmp_path)

    exit_code = main(["curate", "--source", "auto", "--dry-run", "--upstream-root", str(root)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert '"command_name": "curate"' in captured.out
    assert '"resolved_source_mode": "sqlite"' in captured.out
    assert '"source_run_count": 1' in captured.out
    assert '"observation_count": 2' in captured.out
    assert '"entity_count": 2' in captured.out
    assert '"status": "curation_dry_run_ready"' in captured.out
    assert '"workspace_validation"' in captured.out


def test_cli_curate_write_persists_curated_outputs(capsys, tmp_path: Path) -> None:
    root = copy_sample_workspace(tmp_path)
    curated_root = tmp_path / "curated-output"

    exit_code = main(
        [
            "curate",
            "--source",
            "auto",
            "--upstream-root",
            str(root),
            "--curated-root",
            str(curated_root),
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["dry_run"] is False
    assert payload["resolved_source_mode"] == "sqlite"
    assert payload["source_run_count"] == 1
    assert payload["observation_count"] == 2
    assert payload["entity_count"] == 2
    assert payload["status"] == "curation_written"
    assert payload["duckdb_path"] == str(curated_root.resolve() / "mx_jobs_insights.duckdb")
    assert payload["parquet_root"] == str(curated_root.resolve() / "parquet")

    duckdb_path = Path(payload["duckdb_path"])
    parquet_root = Path(payload["parquet_root"])
    assert duckdb_path.is_file()
    assert (parquet_root / "source_runs.parquet").is_file()
    assert (parquet_root / "job_observations.parquet").is_file()
    assert (parquet_root / "job_entities.parquet").is_file()

    with duckdb.connect(str(duckdb_path)) as connection:
        assert connection.execute("SELECT COUNT(*) FROM source_runs").fetchone()[0] == 1
        assert connection.execute("SELECT COUNT(*) FROM job_observations").fetchone()[0] == 2
        assert connection.execute("SELECT COUNT(*) FROM job_entities").fetchone()[0] == 2


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


def test_build_curated_batch_projects_source_runs(tmp_path: Path) -> None:
    batch = build_sample_curated_batch(tmp_path)

    assert len(batch.source_runs) == 2
    run_one = next(record for record in batch.source_runs if record.source_run_id == "run-1")
    run_two = next(record for record in batch.source_runs if record.source_run_id == "run-2")

    assert run_one.observation_count == 2
    assert run_one.job_count == 2
    assert run_one.city_count == 2
    assert run_one.observed_at_min.isoformat() == "2026-03-22"
    assert run_one.observed_at_max.isoformat() == "2026-03-22"
    assert run_two.observation_count == 1
    assert run_two.job_count == 1
    assert run_two.city_count == 1
    assert run_two.observed_at_min.isoformat() == "2026-03-23"
    assert run_two.observed_at_max.isoformat() == "2026-03-23"


def test_duckdb_curated_store_persists_tables_and_parquet(tmp_path: Path) -> None:
    batch = build_sample_curated_batch(tmp_path)
    store = DuckDBCuratedStore(CuratedStorageConfig(root=tmp_path / "artifacts" / "curated"))

    result = store.persist_batch(batch)

    assert result.source_run_count == 2
    assert result.observation_count == 3
    assert result.entity_count == 2
    assert result.duckdb_path.is_file()
    assert (result.parquet_root / "source_runs.parquet").is_file()
    assert (result.parquet_root / "job_observations.parquet").is_file()
    assert (result.parquet_root / "job_entities.parquet").is_file()

    with duckdb.connect(str(result.duckdb_path)) as connection:
        assert connection.execute("SELECT COUNT(*) FROM source_runs").fetchone()[0] == 2
        assert connection.execute("SELECT COUNT(*) FROM job_observations").fetchone()[0] == 3
        assert connection.execute("SELECT COUNT(*) FROM job_entities").fetchone()[0] == 2
        tech_stack_json = connection.execute(
            "SELECT tech_stack_json FROM job_entities WHERE job_id = 'job-1'"
        ).fetchone()[0]

    assert json.loads(tech_stack_json) == ["Python", "SQL", "dbt"]


def test_make_sample_data_regenerates_fixture_layout(tmp_path: Path) -> None:
    source_parent = tmp_path / "source"
    source_parent.mkdir()
    upstream_root = copy_sample_workspace(source_parent)
    output_root = tmp_path / "generated"

    exit_code = make_sample_data_main(
        ["--upstream-root", str(upstream_root), "--output-root", str(output_root)]
    )

    assert exit_code == 0
    assert (output_root / "manifest.json").is_file()
    assert (output_root / "state" / "linkedin_jobs.sqlite").is_file()
    assert (output_root / "exports" / "latest" / "linkedin_jobs_daily_mexico.csv").is_file()
    assert (
        output_root / "exports" / "2026-03-22" / "LinkedIn_Jobs_Data_Scientist_Monterrey.csv"
    ).is_file()

    manifest = json.loads((output_root / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["sqlite_job_ids"] == ["job-1", "job-2"]

    validation = LocalUpstreamWorkspaceProvider(branch_probe=lambda _root, _ref: None).validate(
        UpstreamWorkspaceConfig(root=output_root, source_mode="auto")
    )
    assert validation.is_valid is True
    assert validation.available_sources == ("sqlite", "csv")

    sqlite_observations, _, _ = SQLiteSourceAdapter().load(
        UpstreamWorkspaceConfig(root=output_root, source_mode="sqlite")
    )
    csv_observations, _, _ = CsvSourceAdapter().load(
        UpstreamWorkspaceConfig(root=output_root, source_mode="csv")
    )
    assert len(sqlite_observations) == 2
    assert len(csv_observations) == 2
