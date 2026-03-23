"""Shared configuration models for locating and describing the upstream data workspace."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

SourceMode = Literal["auto", "sqlite", "csv"]
SOURCE_MODES: tuple[SourceMode, ...] = ("auto", "sqlite", "csv")


@dataclass(frozen=True, slots=True)
class UpstreamWorkspaceConfig:
    """Describe the local upstream workspace contract for the LinkedInWebScraper data branch."""

    root: Path = Path("../LinkedInWebScraper")
    source_mode: SourceMode = "auto"
    preferred_ref: str = "data"
    sqlite_relative_path: Path = Path("state/linkedin_jobs.sqlite")
    exports_relative_path: Path = Path("exports")

    def resolved_root(self) -> Path:
        """Return the normalized upstream workspace path without requiring it to exist yet."""

        return self.root.expanduser().resolve(strict=False)

    @property
    def sqlite_path(self) -> Path:
        """Return the expected SQLite path inside the upstream workspace."""

        return self.resolved_root() / self.sqlite_relative_path

    @property
    def exports_path(self) -> Path:
        """Return the expected exports root inside the upstream workspace."""

        return self.resolved_root() / self.exports_relative_path

    def to_display_dict(self) -> dict[str, str]:
        """Serialize the workspace contract into string values suitable for CLI display."""

        return {
            "root": str(self.resolved_root()),
            "source_mode": self.source_mode,
            "preferred_ref": self.preferred_ref,
            "sqlite_path": str(self.sqlite_path),
            "exports_path": str(self.exports_path),
        }
