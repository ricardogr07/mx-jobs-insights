"""Local upstream workspace validation and source-mode resolution."""

from __future__ import annotations

import re
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Protocol, runtime_checkable

from mexico_linkedin_jobs_portfolio.config import SourceMode, UpstreamWorkspaceConfig
from mexico_linkedin_jobs_portfolio.models import WorkspaceValidationResult

BranchProbe = Callable[[Path, str], bool | None]
_DATE_DIR_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")


@runtime_checkable
class UpstreamWorkspaceProvider(Protocol):
    """Define the contract for validating and resolving upstream workspaces."""

    def validate(self, workspace: UpstreamWorkspaceConfig) -> WorkspaceValidationResult:
        """Return the current workspace validation result."""


class LocalUpstreamWorkspaceProvider:
    """Validate the local LinkedInWebScraper workspace without mutating it."""

    def __init__(self, branch_probe: BranchProbe | None = None) -> None:
        self._branch_probe = branch_probe or probe_local_branch

    def validate(self, workspace: UpstreamWorkspaceConfig) -> WorkspaceValidationResult:
        root = workspace.resolved_root()
        root_exists = root.exists()
        is_directory = root.is_dir() if root_exists else False
        sqlite_available = workspace.sqlite_path.is_file()
        exports_root = workspace.exports_path
        latest_exports_available = (
            exports_root.is_dir()
            and (exports_root / "latest").is_dir()
            and any((exports_root / "latest").glob("*.csv"))
        )
        dated_export_directories = discover_dated_export_directories(exports_root)
        exports_available = latest_exports_available or bool(dated_export_directories)
        has_git_metadata = (root / ".git").exists()
        preferred_ref_available = (
            self._branch_probe(root, workspace.preferred_ref) if has_git_metadata else None
        )

        resolved_source_mode = resolve_source_mode(
            workspace.source_mode,
            sqlite_available=sqlite_available,
            exports_available=exports_available,
        )

        notes: list[str] = []
        errors: list[str] = []

        if not root_exists:
            errors.append(f"Upstream workspace does not exist: {root}")
        elif not is_directory:
            errors.append(f"Upstream workspace is not a directory: {root}")

        if has_git_metadata:
            if preferred_ref_available is True:
                notes.append(
                    f"Preferred ref '{workspace.preferred_ref}' is present in the local Git metadata."
                )
            elif preferred_ref_available is False:
                notes.append(
                    f"Preferred ref '{workspace.preferred_ref}' was not found locally; validation is using the current working-tree shape only."
                )
            else:
                notes.append(
                    f"Git metadata exists at {root}, but branch availability for '{workspace.preferred_ref}' could not be verified non-destructively."
                )
        else:
            notes.append(
                "No .git metadata was found; validation is based on the current filesystem shape only."
            )

        if latest_exports_available:
            notes.append("Found CSV files under exports/latest.")
        if dated_export_directories:
            notes.append(
                "Found dated export directories: " + ", ".join(dated_export_directories) + "."
            )

        if workspace.source_mode == "auto":
            if resolved_source_mode == "sqlite" and exports_available:
                notes.append(
                    "Auto mode prefers SQLite when both SQLite and CSV exports are available."
                )
            elif resolved_source_mode == "sqlite":
                notes.append(
                    "Auto mode resolved to SQLite because it is the only available source."
                )
            elif resolved_source_mode == "csv":
                notes.append("Auto mode resolved to CSV because SQLite is not available.")
            else:
                errors.append(
                    "Auto mode could not resolve a source because neither SQLite nor CSV exports are available."
                )
        elif resolved_source_mode is None:
            if workspace.source_mode == "sqlite":
                errors.append(
                    f"Requested SQLite source is not available at {workspace.sqlite_path}."
                )
            else:
                errors.append(f"Requested CSV source is not available under {exports_root}.")

        return WorkspaceValidationResult(
            requested_source_mode=workspace.source_mode,
            upstream_root=root,
            root_exists=root_exists,
            is_directory=is_directory,
            sqlite_available=sqlite_available,
            exports_available=exports_available,
            latest_exports_available=latest_exports_available,
            dated_export_directories=dated_export_directories,
            preferred_ref=workspace.preferred_ref,
            preferred_ref_available=preferred_ref_available,
            has_git_metadata=has_git_metadata,
            resolved_source_mode=resolved_source_mode,
            errors=tuple(errors),
            notes=tuple(notes),
        )


def resolve_source_mode(
    requested_source_mode: SourceMode,
    *,
    sqlite_available: bool,
    exports_available: bool,
) -> SourceMode | None:
    """Resolve the effective source mode against the available workspace inputs."""

    if requested_source_mode == "auto":
        if sqlite_available:
            return "sqlite"
        if exports_available:
            return "csv"
        return None
    if requested_source_mode == "sqlite":
        return "sqlite" if sqlite_available else None
    return "csv" if exports_available else None


def discover_dated_export_directories(exports_root: Path) -> tuple[str, ...]:
    """Return the dated export directories that currently contain CSV files."""

    if not exports_root.is_dir():
        return ()

    dated_directories: list[str] = []
    for child in sorted(exports_root.iterdir()):
        if not child.is_dir() or not _DATE_DIR_PATTERN.fullmatch(child.name):
            continue
        if any(child.glob("*.csv")):
            dated_directories.append(child.name)
    return tuple(dated_directories)


def probe_local_branch(root: Path, preferred_ref: str) -> bool | None:
    """Check whether the preferred ref exists locally without mutating the upstream repo."""

    try:
        result = subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "show-ref",
                "--verify",
                "--quiet",
                f"refs/heads/{preferred_ref}",
            ],
            capture_output=True,
            check=False,
            text=True,
            timeout=10,
        )
    except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
        return None

    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    return None
