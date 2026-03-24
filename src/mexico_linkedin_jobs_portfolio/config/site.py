"""Configuration models for Phase 3 public site generation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from mexico_linkedin_jobs_portfolio.config.reporting import REPORT_LOCALES, ReportLocale

SITE_LOCALES: tuple[ReportLocale, ...] = REPORT_LOCALES


@dataclass(frozen=True, slots=True)
class SiteArtifactConfig:
    """Describe where the site-generation run summary should be written."""

    root: Path = Path("artifacts/site")

    def resolved_root(self) -> Path:
        """Return the normalized site-artifact root."""

        return self.root.expanduser().resolve(strict=False)

    @property
    def run_summary_path(self) -> Path:
        """Return the canonical site-generation run-summary path."""

        return self.resolved_root() / "run_summary.json"


@dataclass(frozen=True, slots=True)
class SiteConfig:
    """Describe one Phase 3 public-site generation request."""

    report_root: Path = Path("artifacts/reports")
    docs_root: Path = Path("docs")
    locale: ReportLocale = "all"
    dry_run: bool = True

    @property
    def locale_coverage(self) -> tuple[str, ...]:
        """Return the locale set that should be represented in generated pages."""

        if self.locale == "all":
            return ("en", "es")
        return (self.locale,)

    @property
    def report_root_resolved(self) -> Path:
        """Return the normalized report-artifact root."""

        return self.report_root.expanduser().resolve(strict=False)

    @property
    def docs_root_resolved(self) -> Path:
        """Return the normalized docs root."""

        return self.docs_root.expanduser().resolve(strict=False)

    @property
    def public_root(self) -> Path:
        """Return the public-content subtree under the docs root."""

        return self.docs_root_resolved / "public"

    @property
    def asset_root(self) -> Path:
        """Return the public asset subtree used by the generated site."""

        return self.public_root / "assets"

    @property
    def site_artifacts(self) -> SiteArtifactConfig:
        """Return the configured Phase 3 runtime-artifact root."""

        return SiteArtifactConfig()

    def to_display_dict(self) -> dict[str, str | list[str] | bool]:
        """Serialize the site-generation request for CLI output."""

        return {
            "report_root": str(self.report_root_resolved),
            "docs_root": str(self.docs_root_resolved),
            "public_root": str(self.public_root),
            "locale": self.locale,
            "locale_coverage": list(self.locale_coverage),
            "dry_run": self.dry_run,
        }
