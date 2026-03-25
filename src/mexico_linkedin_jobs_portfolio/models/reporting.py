"""Reporting models shared across analytics, rendering, and CLI layers."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any

from mexico_linkedin_jobs_portfolio.config import ReportCadence, ReportLocale


@dataclass(frozen=True, slots=True)
class DimensionCount:
    """One aggregate count entry in a report payload."""

    label: str
    count: int

    @classmethod
    def from_display_dict(cls, payload: dict[str, Any]) -> DimensionCount:
        """Parse one serialized aggregate count entry."""

        return cls(label=str(payload["label"]), count=int(payload["count"]))


@dataclass(frozen=True, slots=True)
class PeriodWindow:
    """One closed reporting period derived from the selected cadence."""

    cadence: ReportCadence
    period_id: str
    label: str
    start_date: date
    end_date: date
    reference_date: date

    def to_display_dict(self) -> dict[str, str]:
        """Serialize the reporting period for JSON output."""

        return {
            "cadence": self.cadence,
            "period_id": self.period_id,
            "label": self.label,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "reference_date": self.reference_date.isoformat(),
        }

    @classmethod
    def from_display_dict(cls, payload: dict[str, Any]) -> PeriodWindow:
        """Parse one serialized reporting period."""

        return cls(
            cadence=payload["cadence"],
            period_id=str(payload["period_id"]),
            label=str(payload["label"]),
            start_date=date.fromisoformat(str(payload["start_date"])),
            end_date=date.fromisoformat(str(payload["end_date"])),
            reference_date=date.fromisoformat(str(payload["reference_date"])),
        )


@dataclass(frozen=True, slots=True)
class LatestJobRecord:
    """Latest observation and current entity attributes for one job in a selected period."""

    job_id: str
    observed_at: date
    title: str
    city: str
    state: str | None
    country: str
    remote_type: str | None
    seniority_level: str | None
    employment_type: str | None
    industry: str | None
    english_required: bool | None
    minimum_years_experience: float | None
    tech_stack: tuple[str, ...]
    company_name: str | None = None
    job_url: str | None = None
    description_text: str | None = None


@dataclass(frozen=True, slots=True)
class ReportMetrics:
    """Aggregate metrics shared across report rendering and AI narration."""

    period: PeriodWindow
    observation_count: int
    job_count: int
    source_run_count: int
    city_counts: tuple[DimensionCount, ...]
    remote_type_counts: tuple[DimensionCount, ...]
    seniority_counts: tuple[DimensionCount, ...]
    employment_type_counts: tuple[DimensionCount, ...]
    industry_counts: tuple[DimensionCount, ...]
    english_requirement_counts: tuple[DimensionCount, ...]
    experience_bucket_counts: tuple[DimensionCount, ...]
    tech_stack_counts: tuple[DimensionCount, ...]
    top_company_counts: tuple[DimensionCount, ...]

    def narrative_payload(self) -> dict[str, Any]:
        """Return the aggregate-only payload that may be sent to OpenAI."""

        payload = self.to_display_dict()
        payload.pop("period_label", None)
        return payload

    def to_display_dict(self) -> dict[str, Any]:
        """Serialize the report metrics for JSON or templates."""

        return {
            "cadence": self.period.cadence,
            "period_id": self.period.period_id,
            "period_label": self.period.label,
            "period_start": self.period.start_date.isoformat(),
            "period_end": self.period.end_date.isoformat(),
            "reference_date": self.period.reference_date.isoformat(),
            "observation_count": self.observation_count,
            "job_count": self.job_count,
            "source_run_count": self.source_run_count,
            "city_counts": [asdict(item) for item in self.city_counts],
            "remote_type_counts": [asdict(item) for item in self.remote_type_counts],
            "seniority_counts": [asdict(item) for item in self.seniority_counts],
            "employment_type_counts": [asdict(item) for item in self.employment_type_counts],
            "industry_counts": [asdict(item) for item in self.industry_counts],
            "english_requirement_counts": [
                asdict(item) for item in self.english_requirement_counts
            ],
            "experience_bucket_counts": [asdict(item) for item in self.experience_bucket_counts],
            "tech_stack_counts": [asdict(item) for item in self.tech_stack_counts],
            "top_company_counts": [asdict(item) for item in self.top_company_counts],
        }

    @classmethod
    def from_display_dict(cls, payload: dict[str, Any]) -> ReportMetrics:
        """Parse one serialized report-metrics payload."""

        return cls(
            period=PeriodWindow(
                cadence=payload["cadence"],
                period_id=str(payload["period_id"]),
                label=str(payload["period_label"]),
                start_date=date.fromisoformat(str(payload["period_start"])),
                end_date=date.fromisoformat(str(payload["period_end"])),
                reference_date=date.fromisoformat(str(payload["reference_date"])),
            ),
            observation_count=int(payload["observation_count"]),
            job_count=int(payload["job_count"]),
            source_run_count=int(payload["source_run_count"]),
            city_counts=_parse_dimension_counts(payload.get("city_counts")),
            remote_type_counts=_parse_dimension_counts(payload.get("remote_type_counts")),
            seniority_counts=_parse_dimension_counts(payload.get("seniority_counts")),
            employment_type_counts=_parse_dimension_counts(payload.get("employment_type_counts")),
            industry_counts=_parse_dimension_counts(payload.get("industry_counts")),
            english_requirement_counts=_parse_dimension_counts(
                payload.get("english_requirement_counts")
            ),
            experience_bucket_counts=_parse_dimension_counts(
                payload.get("experience_bucket_counts")
            ),
            tech_stack_counts=_parse_dimension_counts(payload.get("tech_stack_counts")),
            top_company_counts=_parse_dimension_counts(payload.get("top_company_counts")),
        )


@dataclass(frozen=True, slots=True)
class PublicJobRecord:
    """Allowed public CSV projection for one job row."""

    public_job_key: str
    title: str
    as_of_date: date
    city: str
    state: str | None
    remote_type: str | None
    seniority_level: str | None
    employment_type: str | None
    industry: str | None
    english_required: bool | None
    min_years_experience: float | None
    tech_stack: tuple[str, ...]

    def to_csv_row(self) -> dict[str, str]:
        """Serialize the public record into CSV-safe strings."""

        return {
            "public_job_key": self.public_job_key,
            "title": self.title,
            "as_of_date": self.as_of_date.isoformat(),
            "city": self.city,
            "state": self.state or "",
            "remote_type": self.remote_type or "",
            "seniority_level": self.seniority_level or "",
            "employment_type": self.employment_type or "",
            "industry": self.industry or "",
            "english_required": "" if self.english_required is None else str(self.english_required),
            "min_years_experience": (
                "" if self.min_years_experience is None else str(self.min_years_experience)
            ),
            "tech_stack": " | ".join(self.tech_stack),
        }


@dataclass(frozen=True, slots=True)
class GeneratedNarrative:
    """Bilingual narrative generated from aggregate metrics only."""

    model: str
    en_headline: str
    en_bullets: tuple[str, ...]
    es_headline: str
    es_bullets: tuple[str, ...]

    def for_locale(self, locale: ReportLocale) -> tuple[str, tuple[str, ...]]:
        """Return the localized narrative content for one locale."""

        if locale == "es":
            return self.es_headline, self.es_bullets
        return self.en_headline, self.en_bullets


@dataclass(frozen=True, slots=True)
class ReportArtifacts:
    """File-system artifacts emitted by one non-dry-run report."""

    artifact_dir: Path
    metrics_path: Path
    public_csv_path: Path
    run_summary_path: Path
    markdown_paths: dict[str, Path]
    html_paths: dict[str, Path]

    def to_display_dict(self) -> dict[str, Any]:
        """Serialize the written artifact paths for JSON output."""

        return {
            "artifact_dir": str(self.artifact_dir),
            "metrics_path": str(self.metrics_path),
            "public_csv_path": str(self.public_csv_path),
            "run_summary_path": str(self.run_summary_path),
            "markdown_paths": {locale: str(path) for locale, path in self.markdown_paths.items()},
            "html_paths": {locale: str(path) for locale, path in self.html_paths.items()},
        }

    @classmethod
    def from_display_dict(cls, payload: dict[str, Any]) -> ReportArtifacts:
        """Parse one serialized artifact bundle."""

        return cls(
            artifact_dir=Path(str(payload["artifact_dir"])),
            metrics_path=Path(str(payload["metrics_path"])),
            public_csv_path=Path(str(payload["public_csv_path"])),
            run_summary_path=Path(str(payload["run_summary_path"])),
            markdown_paths={
                str(locale): Path(str(path))
                for locale, path in dict(payload.get("markdown_paths", {})).items()
            },
            html_paths={
                str(locale): Path(str(path))
                for locale, path in dict(payload.get("html_paths", {})).items()
            },
        )


@dataclass(frozen=True, slots=True)
class ReportRunSummary:
    """CLI-facing summary of one report run."""

    command_name: str
    cadence: ReportCadence
    locale: ReportLocale
    locale_coverage: tuple[str, ...]
    curated_root: Path
    output_root: Path
    dry_run: bool
    period_id: str | None = None
    period_start: date | None = None
    period_end: date | None = None
    as_of_date: date | None = None
    observation_count: int = 0
    job_count: int = 0
    source_run_count: int = 0
    public_row_count: int = 0
    narration_status: str = "not_requested"
    status: str = "not_run"
    artifact_dir: Path | None = None
    metrics_path: Path | None = None
    public_csv_path: Path | None = None
    run_summary_path: Path | None = None
    markdown_paths: dict[str, Path] | None = None
    html_paths: dict[str, Path] | None = None
    notes: tuple[str, ...] = ()

    def to_display_dict(self) -> dict[str, Any]:
        """Serialize the run summary for CLI JSON output."""

        return {
            "command_name": self.command_name,
            "cadence": self.cadence,
            "locale": self.locale,
            "locale_coverage": list(self.locale_coverage),
            "curated_root": str(self.curated_root),
            "output_root": str(self.output_root),
            "dry_run": self.dry_run,
            "period_id": self.period_id,
            "period_start": self.period_start.isoformat()
            if self.period_start is not None
            else None,
            "period_end": self.period_end.isoformat() if self.period_end is not None else None,
            "as_of_date": self.as_of_date.isoformat() if self.as_of_date is not None else None,
            "observation_count": self.observation_count,
            "job_count": self.job_count,
            "source_run_count": self.source_run_count,
            "public_row_count": self.public_row_count,
            "narration_status": self.narration_status,
            "status": self.status,
            "artifact_dir": str(self.artifact_dir) if self.artifact_dir is not None else None,
            "metrics_path": str(self.metrics_path) if self.metrics_path is not None else None,
            "public_csv_path": (
                str(self.public_csv_path) if self.public_csv_path is not None else None
            ),
            "run_summary_path": (
                str(self.run_summary_path) if self.run_summary_path is not None else None
            ),
            "markdown_paths": {
                locale: str(path) for locale, path in (self.markdown_paths or {}).items()
            },
            "html_paths": {locale: str(path) for locale, path in (self.html_paths or {}).items()},
            "notes": list(self.notes),
        }

    @classmethod
    def from_display_dict(cls, payload: dict[str, Any]) -> ReportRunSummary:
        """Parse one serialized report run summary."""

        return cls(
            command_name=str(payload["command_name"]),
            cadence=payload["cadence"],
            locale=payload["locale"],
            locale_coverage=tuple(str(locale) for locale in payload.get("locale_coverage", [])),
            curated_root=Path(str(payload["curated_root"])),
            output_root=Path(str(payload["output_root"])),
            dry_run=bool(payload["dry_run"]),
            period_id=str(payload["period_id"]) if payload.get("period_id") else None,
            period_start=(
                date.fromisoformat(str(payload["period_start"]))
                if payload.get("period_start")
                else None
            ),
            period_end=(
                date.fromisoformat(str(payload["period_end"]))
                if payload.get("period_end")
                else None
            ),
            as_of_date=(
                date.fromisoformat(str(payload["as_of_date"]))
                if payload.get("as_of_date")
                else None
            ),
            observation_count=int(payload.get("observation_count", 0)),
            job_count=int(payload.get("job_count", 0)),
            source_run_count=int(payload.get("source_run_count", 0)),
            public_row_count=int(payload.get("public_row_count", 0)),
            narration_status=str(payload.get("narration_status", "not_requested")),
            status=str(payload.get("status", "not_run")),
            artifact_dir=Path(str(payload["artifact_dir"]))
            if payload.get("artifact_dir")
            else None,
            metrics_path=Path(str(payload["metrics_path"]))
            if payload.get("metrics_path")
            else None,
            public_csv_path=(
                Path(str(payload["public_csv_path"])) if payload.get("public_csv_path") else None
            ),
            run_summary_path=(
                Path(str(payload["run_summary_path"])) if payload.get("run_summary_path") else None
            ),
            markdown_paths={
                str(locale): Path(str(path))
                for locale, path in dict(payload.get("markdown_paths", {})).items()
            }
            or None,
            html_paths={
                str(locale): Path(str(path))
                for locale, path in dict(payload.get("html_paths", {})).items()
            }
            or None,
            notes=tuple(str(note) for note in payload.get("notes", [])),
        )


def _parse_dimension_counts(values: Any) -> tuple[DimensionCount, ...]:
    if not isinstance(values, list):
        return ()
    return tuple(
        DimensionCount.from_display_dict(item) for item in values if isinstance(item, dict)
    )
