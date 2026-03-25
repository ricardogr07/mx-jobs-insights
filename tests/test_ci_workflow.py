from __future__ import annotations

from pathlib import Path


def test_ci_workflow_contract_matches_local_green_gate() -> None:
    workflow_path = Path(".github/workflows/ci.yml")
    assert workflow_path.is_file(), "Expected .github/workflows/ci.yml to exist."

    text = workflow_path.read_text(encoding="utf-8")

    assert "pull_request:" in text
    assert "push:" in text
    assert "workflow_dispatch:" in text
    assert "branches:" in text
    assert "- main" in text
    assert "concurrency:" in text
    assert "cancel-in-progress: true" in text
    assert "permissions:" in text
    assert "contents: read" in text
    assert "actions/checkout@v4" in text
    assert "actions/setup-python@v5" in text
    assert 'python-version: "3.11"' in text
    assert 'python -m pip install -e ".[dev]"' in text
    assert "python -m ruff check src tests" in text
    assert "python -m pytest -q --basetemp .pytest_tmp" in text
    assert "python -m mkdocs build --strict" in text
    assert "python -m build --no-isolation" in text
    assert "GITHUB_STEP_SUMMARY" in text
    assert "# CI summary" in text
    assert "Public site:" in text
