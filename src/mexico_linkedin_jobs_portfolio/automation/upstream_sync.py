"""Managed upstream workspace seeding for containerized and cloud pipeline runs."""

from __future__ import annotations

import subprocess

from mexico_linkedin_jobs_portfolio.config import UpstreamWorkspaceConfig


class GitUpstreamWorkspaceSeeder:
    """Materialize the upstream data workspace in ephemeral runtimes when needed."""

    def ensure_workspace(
        self,
        workspace: UpstreamWorkspaceConfig,
        *,
        repo_url: str,
    ) -> tuple[str, tuple[str, ...]]:
        root = workspace.resolved_root()
        if root.exists():
            return (
                "workspace_present",
                (f"Using existing upstream workspace at {root}.",),
            )

        root.parent.mkdir(parents=True, exist_ok=True)
        command = [
            "git",
            "clone",
            "--depth",
            "1",
            "--branch",
            workspace.preferred_ref,
            repo_url,
            str(root),
        ]
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                check=False,
                text=True,
                timeout=300,
            )
        except FileNotFoundError as exc:
            raise RuntimeError(
                "Git is required to seed the upstream workspace in cloud runtimes."
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(
                "Timed out while cloning the upstream workspace for the pipeline."
            ) from exc

        if result.returncode != 0:
            stderr = result.stderr.strip() or result.stdout.strip() or "git clone failed"
            raise RuntimeError(
                f"Failed to clone upstream ref '{workspace.preferred_ref}' from {repo_url}: {stderr}"
            )

        return (
            "workspace_seeded",
            (
                f"Cloned upstream ref '{workspace.preferred_ref}' from {repo_url} into {root}.",
            ),
        )
