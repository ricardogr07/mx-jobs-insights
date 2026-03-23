from __future__ import annotations

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "tests" / "data" / "upstream_workspace"
MANIFEST_PATH = FIXTURE_ROOT / "manifest.json"


def load_manifest() -> dict[str, Any]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def apply_fixture_metadata(workspace_root: Path) -> None:
    manifest = load_manifest()
    timestamps = manifest.get("latest_file_timestamps", {})
    if not isinstance(timestamps, dict):
        return

    for relative_path, iso_timestamp in timestamps.items():
        target = workspace_root / relative_path
        if not target.exists():
            continue
        observed_at = datetime.fromisoformat(str(iso_timestamp))
        timestamp = observed_at.timestamp()
        os.utime(target, (timestamp, timestamp))


def copy_sample_workspace(
    tmp_path: Path,
    *,
    sqlite: bool = True,
    csv: bool = True,
    git_metadata: bool = False,
) -> Path:
    root = tmp_path / "LinkedInWebScraper"
    shutil.copytree(
        FIXTURE_ROOT,
        root,
        copy_function=shutil.copy2,
        ignore=shutil.ignore_patterns("manifest.json"),
    )
    apply_fixture_metadata(root)

    if not sqlite:
        shutil.rmtree(root / "state", ignore_errors=True)
    if not csv:
        shutil.rmtree(root / "exports", ignore_errors=True)
    if git_metadata:
        (root / ".git").mkdir()

    return root
