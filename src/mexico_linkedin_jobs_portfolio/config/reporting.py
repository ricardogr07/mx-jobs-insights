"""Configuration models for report generation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Literal, cast

from mexico_linkedin_jobs_portfolio.config.curated import CuratedStorageConfig

ReportCadence = Literal["weekly", "monthly"]
REPORT_CADENCES: tuple[ReportCadence, ...] = ("weekly", "monthly")

ReportLocale = Literal["en", "es", "all"]
REPORT_LOCALES: tuple[ReportLocale, ...] = ("en", "es", "all")

OPENAI_API_KEY_ENV = "OPENAI_API_KEY"
OPENAI_MODEL_ENV = "MX_JOBS_OPENAI_MODEL"
PUBLIC_KEY_SALT_ENV = "MX_JOBS_PUBLIC_KEY_SALT"
OPENAI_BASE_URL_ENV = "MX_JOBS_OPENAI_BASE_URL"

ANTHROPIC_API_KEY_ENV = "ANTHROPIC_API_KEY"
ANTHROPIC_MODEL_ENV = "MX_JOBS_ANTHROPIC_MODEL"
ANTHROPIC_BASE_URL_ENV = "MX_JOBS_ANTHROPIC_BASE_URL"
LLM_PROVIDER_ENV = "MX_JOBS_LLM_PROVIDER"

LLMProvider = Literal["openai", "anthropic"]
LLM_PROVIDERS: tuple[LLMProvider, ...] = ("openai", "anthropic")
DEFAULT_LLM_PROVIDER: LLMProvider = "openai"

DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"
DEFAULT_ANTHROPIC_BASE_URL = "https://api.anthropic.com/v1"


def resolve_llm_provider(value: str | None) -> LLMProvider:
    """Return the narration provider selected by the environment.

    An unset or blank value keeps the code default. An unrecognized value fails loudly
    rather than silently narrating through the wrong provider.
    """

    normalized = (value or "").strip().lower()
    if not normalized:
        return DEFAULT_LLM_PROVIDER
    if normalized not in LLM_PROVIDERS:
        raise ValueError(
            f"{LLM_PROVIDER_ENV} must be one of {', '.join(LLM_PROVIDERS)}: got {value!r}"
        )
    return cast(LLMProvider, normalized)


@dataclass(frozen=True, slots=True)
class ReportStorageConfig:
    """Describe where generated report artifacts should be written."""

    root: Path = Path("artifacts/reports")

    def resolved_root(self) -> Path:
        """Return the normalized report output root."""

        return self.root.expanduser().resolve(strict=False)

    def period_root(self, cadence: ReportCadence, period_id: str) -> Path:
        """Return the canonical output directory for one report period."""

        return self.resolved_root() / cadence / period_id


@dataclass(frozen=True, slots=True)
class ReportConfig:
    """Describe one report-generation request."""

    cadence: ReportCadence
    locale: ReportLocale = "all"
    as_of_date: date | None = None
    curated_root: Path = CuratedStorageConfig().root
    output_root: Path = ReportStorageConfig().root
    dry_run: bool = True
    openai_api_key: str | None = None
    openai_model: str | None = None
    public_key_salt: str | None = None
    openai_base_url: str = DEFAULT_OPENAI_BASE_URL
    filter_by_posted_date: bool = False
    narrative_cache_root: Path | None = None
    llm_provider: LLMProvider = DEFAULT_LLM_PROVIDER
    anthropic_api_key: str | None = None
    anthropic_model: str | None = None
    anthropic_base_url: str = DEFAULT_ANTHROPIC_BASE_URL

    @property
    def curated_storage(self) -> CuratedStorageConfig:
        """Return the curated storage config used as report input."""

        return CuratedStorageConfig(root=self.curated_root)

    @property
    def report_storage(self) -> ReportStorageConfig:
        """Return the report storage config used for generated artifacts."""

        return ReportStorageConfig(root=self.output_root)

    @property
    def locale_coverage(self) -> tuple[str, ...]:
        """Return the locales that should be rendered for this request."""

        if self.locale == "all":
            return ("en", "es")
        return (self.locale,)

    @property
    def narration_model(self) -> str | None:
        """Return the model of the selected narration provider."""

        if self.llm_provider == "anthropic":
            return self.anthropic_model
        return self.openai_model

    def missing_runtime_env(self) -> tuple[str, ...]:
        """Return missing environment-backed values for a non-dry-run report.

        Only the selected provider's credentials are required: choosing one provider
        never fails on the other provider's missing variables.
        """

        missing: list[str] = []
        if self.llm_provider == "anthropic":
            if not self.anthropic_api_key:
                missing.append(ANTHROPIC_API_KEY_ENV)
            if not self.anthropic_model:
                missing.append(ANTHROPIC_MODEL_ENV)
        else:
            if not self.openai_api_key:
                missing.append(OPENAI_API_KEY_ENV)
            if not self.openai_model:
                missing.append(OPENAI_MODEL_ENV)
        if not self.public_key_salt:
            missing.append(PUBLIC_KEY_SALT_ENV)
        return tuple(missing)

    def to_display_dict(self) -> dict[str, str | list[str] | None]:
        """Serialize the report request for CLI or debug output."""

        return {
            "cadence": self.cadence,
            "locale": self.locale,
            "locale_coverage": list(self.locale_coverage),
            "as_of_date": self.as_of_date.isoformat() if self.as_of_date is not None else None,
            "curated_root": str(self.curated_storage.resolved_root()),
            "output_root": str(self.report_storage.resolved_root()),
            "dry_run": self.dry_run,
            "llm_provider": self.llm_provider,
            "openai_base_url": self.openai_base_url,
            "anthropic_base_url": self.anthropic_base_url,
            "missing_runtime_env": list(self.missing_runtime_env()) if not self.dry_run else [],
        }
