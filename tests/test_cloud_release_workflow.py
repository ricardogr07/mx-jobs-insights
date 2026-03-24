from __future__ import annotations

from pathlib import Path

import pytest

WORKFLOW_PATH = Path('.github/workflows/release-cloud-run-job.yml')


def _load_workflow_text() -> str:
    if not WORKFLOW_PATH.is_file():
        pytest.skip('Cloud Run release workflow file is not present in this checkout.')
    return WORKFLOW_PATH.read_text(encoding='utf-8')


def test_cloud_run_release_workflow_contract() -> None:
    text = _load_workflow_text()

    assert 'name: Release Cloud Run Job' in text
    assert 'workflow_dispatch:' in text
    assert 'image_tag:' in text
    assert 'deploy_job:' in text
    assert 'terraform_validate:' in text
    assert 'google-github-actions/auth@v2' in text
    assert 'google-github-actions/setup-gcloud@v2' in text
    assert 'hashicorp/setup-terraform@v3' in text
    assert 'docker build' in text
    assert 'docker push' in text
    assert 'gcloud run jobs deploy' in text
    assert '--args' in text
    assert 'MX_JOBS_UPSTREAM_REPO_URL' in text
    assert 'MX_JOBS_UPSTREAM_REF' in text
    assert 'OPENAI_API_KEY' in text
    assert 'MX_JOBS_PUBLIC_KEY_SALT' in text
    assert 'GITHUB_STEP_SUMMARY' in text
    assert '# Cloud Run release summary' in text
