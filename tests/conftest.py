from __future__ import annotations

import shutil
import sys
from collections.abc import Iterator
from pathlib import Path
from uuid import uuid4

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
TESTS = ROOT / "tests"
TEMP_ROOT = ROOT / "artifacts" / "test-tmp"

for candidate in (SRC, TESTS):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))


@pytest.fixture
def tmp_path() -> Iterator[Path]:
    TEMP_ROOT.mkdir(parents=True, exist_ok=True)
    path = TEMP_ROOT / f"case-{uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)
