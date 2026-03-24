from __future__ import annotations

import re
from pathlib import Path

PHASE_PATTERN = re.compile(r"(?i)\bphase [0-9]\b|\bmvp\b|shell only")
MARKDOWN_LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def test_mkdocs_nav_is_public_only() -> None:
    text = Path("mkdocs.yml").read_text(encoding="utf-8")

    assert "Development:" not in text
    assert "codex/" not in text
    assert "internal/" not in text
    assert "index.md" in text
    assert "public/weekly/index.md" in text
    assert "public/monthly/index.md" in text
    assert "public/methodology.md" in text
    assert "public/downloads/index.md" in text


def test_public_docs_do_not_reference_internal_paths() -> None:
    for path in Path("docs").rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        assert "internal/" not in text, f"Public doc leaked internal reference: {path}"


def test_cloud_workflow_rename_is_consistent() -> None:
    assert Path(".github/workflows/release-cloud-run-job.yml").is_file()
    assert not Path(".github/workflows/cloud-release.yml").exists()

    readme_text = Path("README.md").read_text(encoding="utf-8")
    cloud_doc_text = Path("internal/development/cloud-deployment.md").read_text(encoding="utf-8")
    workflow_test_text = Path("tests/test_cloud_release_workflow.py").read_text(encoding="utf-8")

    for text in (readme_text, cloud_doc_text, workflow_test_text):
        assert "release-cloud-run-job.yml" in text
        assert "cloud-release.yml" not in text


def test_internal_markdown_links_resolve() -> None:
    internal_root = Path("internal")
    for markdown_path in internal_root.rglob("*.md"):
        text = markdown_path.read_text(encoding="utf-8")
        for target in MARKDOWN_LINK_PATTERN.findall(text):
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            target_path = target.split("#", 1)[0]
            if not target_path:
                continue
            resolved = (markdown_path.parent / target_path).resolve(strict=False)
            assert resolved.exists(), f"Broken internal doc link in {markdown_path}: {target}"


def test_public_and_runtime_surfaces_are_free_of_phase_labels() -> None:
    scan_roots = [
        Path("README.md"),
        Path("AGENTS.md"),
        Path("mkdocs.yml"),
        Path("docs"),
        Path("src"),
        Path(".github/workflows"),
    ]

    offenders: list[str] = []
    for root in scan_roots:
        paths = [root] if root.is_file() else list(root.rglob("*"))
        for path in paths:
            if not path.is_file():
                continue
            if path.suffix not in {".md", ".py", ".yml", ".yaml"}:
                continue
            text = path.read_text(encoding="utf-8")
            if PHASE_PATTERN.search(text):
                offenders.append(str(path))

    assert not offenders, f"Found stale phase-era wording in: {offenders}"
