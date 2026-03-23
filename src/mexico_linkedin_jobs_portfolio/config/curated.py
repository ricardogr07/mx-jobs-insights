"""Configuration models for DuckDB curated storage and Parquet sidecars."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class CuratedStorageConfig:
    """Describe where curated DuckDB and Parquet outputs should be written."""

    root: Path = Path("artifacts/curated")
    duckdb_filename: str = "mx_jobs_insights.duckdb"
    parquet_dirname: str = "parquet"

    def resolved_root(self) -> Path:
        """Return the normalized curated output root without requiring it to exist yet."""

        return self.root.expanduser().resolve(strict=False)

    @property
    def duckdb_path(self) -> Path:
        """Return the canonical DuckDB file path for curated state."""

        return self.resolved_root() / self.duckdb_filename

    @property
    def parquet_root(self) -> Path:
        """Return the directory used for Parquet sidecar exports."""

        return self.resolved_root() / self.parquet_dirname

    def to_display_dict(self) -> dict[str, str]:
        """Serialize the curated storage config for CLI or debug output."""

        return {
            "root": str(self.resolved_root()),
            "duckdb_path": str(self.duckdb_path),
            "parquet_root": str(self.parquet_root),
        }
