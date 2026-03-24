from __future__ import annotations

from pathlib import Path

import pytest

PUBLISH_WORKFLOW_PATH = Path(".github/workflows/publish-portfolio-site.yml")


def _load_workflow_text() -> str:
    if not PUBLISH_WORKFLOW_PATH.is_file():
        pytest.skip("Phase 4 workflow file has not been added yet.")
    return PUBLISH_WORKFLOW_PATH.read_text(encoding="utf-8")


def test_publish_workflow_contract_matches_phase_4_plan() -> None:
    text = _load_workflow_text()

    assert "name: Publish Portfolio Site" in text
    assert "workflow_dispatch:" in text
    assert "cadence:" in text
    assert "as_of_date:" in text
    assert "deploy_pages:" in text
    assert "schedule:" in text
    assert "cron: '0 14 * * 1'" in text or 'cron: "0 14 * * 1"' in text
    assert "cron: '0 15 1 * *'" in text or 'cron: "0 15 1 * *"' in text
    assert "permissions:" in text
    assert "contents: read" in text
    assert "pages: write" in text
    assert "id-token: write" in text
    assert "concurrency:" in text
    assert "cancel-in-progress: false" in text
    assert text.count("actions/checkout") >= 2
    assert "ricardogr07/LinkedInWebScraper" in text
    assert "ref: data" in text
    assert "path: LinkedInWebScraper" in text
    assert "python -m pip install -e .[dev]" in text or 'python -m pip install -e ".[dev]"' in text
    assert "OPENAI_API_KEY" in text
    assert "MX_JOBS_OPENAI_MODEL" in text
    assert "MX_JOBS_PUBLIC_KEY_SALT" in text
    assert "pipeline --cadence" in text or "pipeline" in text
    assert "actions/upload-pages-artifact" in text
    assert "actions/deploy-pages" in text
    assert "deploy_pages" in text
    assert "artifact" in text.lower()
    assert "GITHUB_STEP_SUMMARY" in text
    assert "# Publish summary" in text
    assert "Public site:" in text

