from __future__ import annotations

from pathlib import Path


def test_dockerfile_matches_container_runtime_contract() -> None:
    dockerfile = Path('Dockerfile')
    assert dockerfile.is_file(), 'Expected Dockerfile to exist for the container runtime.'

    text = dockerfile.read_text(encoding='utf-8')

    assert 'FROM python:3.11-slim-bookworm' in text
    assert 'WORKDIR /workspace' in text
    assert 'apt-get install --yes --no-install-recommends git' in text
    assert 'python -m pip install .[cloud,docs]' in text
    assert 'interfaces.cli.main", "pipeline"' in text


def test_terraform_root_matches_phase_5_foundation_contract() -> None:
    main_tf = Path('infra/terraform/main.tf')
    variables_tf = Path('infra/terraform/variables.tf')
    outputs_tf = Path('infra/terraform/outputs.tf')

    assert main_tf.is_file(), 'Expected infra/terraform/main.tf to exist.'
    assert variables_tf.is_file(), 'Expected infra/terraform/variables.tf to exist.'
    assert outputs_tf.is_file(), 'Expected infra/terraform/outputs.tf to exist.'

    main_text = main_tf.read_text(encoding='utf-8')
    variables_text = variables_tf.read_text(encoding='utf-8')

    assert 'google_artifact_registry_repository' in main_text
    assert 'google_storage_bucket' in main_text
    assert 'google_bigquery_dataset' in main_text
    assert 'google_cloud_run_v2_job' in main_text
    assert 'google_cloud_scheduler_job' in main_text
    assert 'google_secret_manager_secret' in main_text
    assert 'containerOverrides' in main_text
    assert 'cloud_run_weekly_args' in main_text
    assert 'cloud_run_monthly_args' in main_text
    assert 'MX_JOBS_UPSTREAM_REPO_URL' in main_text
    assert 'MX_JOBS_UPSTREAM_REF' in main_text
    assert 'cloud_run_upstream_repo_url' in variables_text
    assert 'cloud_run_upstream_ref' in variables_text
    assert 'mx_jobs_openai_model' in variables_text
    assert 'mx_jobs_openai_base_url' in variables_text

