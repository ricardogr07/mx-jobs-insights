"""Markdown renderers for Phase 3 public site pages."""

from __future__ import annotations

from os.path import relpath
from pathlib import Path

from mexico_linkedin_jobs_portfolio.models import DimensionCount, SiteReportEntry, SiteReportIndex


def render_landing_page(
    index: SiteReportIndex,
    *,
    locale_coverage: tuple[str, ...],
    landing_path: Path,
    weekly_index_path: Path,
    monthly_index_path: Path,
    methodology_path: Path,
    downloads_index_path: Path,
    public_root: Path,
) -> str:
    title = _label(
        locale_coverage,
        "Mexico LinkedIn Jobs Portfolio",
        "Portafolio de Vacantes de LinkedIn en Mexico",
    )
    intro = _label(
        locale_coverage,
        "This public site is generated from reviewed weekly and monthly report artifacts.",
        "Este sitio publico se genera a partir de artefactos semanales y mensuales ya revisados.",
    )
    lines = [f"# {title}", "", intro, ""]
    lines.extend(
        [
            f"- {_label(locale_coverage, 'Weekly archive', 'Archivo semanal')}: [{_label(locale_coverage, 'Open', 'Abrir')}]({_relative_link(landing_path, weekly_index_path)})",
            f"- {_label(locale_coverage, 'Monthly archive', 'Archivo mensual')}: [{_label(locale_coverage, 'Open', 'Abrir')}]({_relative_link(landing_path, monthly_index_path)})",
            f"- {_label(locale_coverage, 'Downloads', 'Descargas')}: [{_label(locale_coverage, 'Open', 'Abrir')}]({_relative_link(landing_path, downloads_index_path)})",
            f"- {_label(locale_coverage, 'Methodology', 'Metodologia')}: [{_label(locale_coverage, 'Open', 'Abrir')}]({_relative_link(landing_path, methodology_path)})",
            "",
        ]
    )
    lines.extend(
        _render_latest_section(
            index.latest_weekly,
            locale_coverage=locale_coverage,
            source_path=landing_path,
            public_root=public_root,
            heading_en="Latest Weekly Report",
            heading_es="Reporte Semanal Mas Reciente",
        )
    )
    lines.extend(
        _render_latest_section(
            index.latest_monthly,
            locale_coverage=locale_coverage,
            source_path=landing_path,
            public_root=public_root,
            heading_en="Latest Monthly Report",
            heading_es="Reporte Mensual Mas Reciente",
        )
    )
    return "\n".join(lines).strip() + "\n"


def render_archive_page(
    cadence: str,
    entries: tuple[SiteReportEntry, ...],
    *,
    locale_coverage: tuple[str, ...],
    page_path: Path,
    public_root: Path,
) -> str:
    cadence_label_en = "Weekly Reports" if cadence == "weekly" else "Monthly Reports"
    cadence_label_es = "Reportes Semanales" if cadence == "weekly" else "Reportes Mensuales"
    lines = [f"# {_label(locale_coverage, cadence_label_en, cadence_label_es)}", ""]
    if not entries:
        lines.extend(
            [
                _label(
                    locale_coverage,
                    "No reports are available yet.",
                    "Aun no hay reportes disponibles.",
                ),
                "",
            ]
        )
        return "\n".join(lines)

    lines.extend(
        [
            f"| {_label(locale_coverage, 'Period', 'Periodo')} | {_label(locale_coverage, 'Jobs', 'Vacantes')} | {_label(locale_coverage, 'Observations', 'Observaciones')} | {_label(locale_coverage, 'Assets', 'Activos')} |",
            "| --- | ---: | ---: | --- |",
        ]
    )
    for entry in entries:
        page_link = _relative_link(page_path, page_path.parent / f"{entry.period_id}.md")
        asset_links = _join_asset_links(
            entry,
            locale_coverage=locale_coverage,
            source_path=page_path,
            public_root=public_root,
        )
        lines.append(
            f"| [{entry.period_id}]({page_link}) | {entry.metrics.job_count} | {entry.metrics.observation_count} | {asset_links} |"
        )
    lines.append("")
    return "\n".join(lines)


def render_period_page(
    entry: SiteReportEntry,
    *,
    locale_coverage: tuple[str, ...],
    page_path: Path,
    public_root: Path,
) -> str:
    lines = [f"# {entry.period_id}", ""]
    lines.extend(
        [
            f"- {_label(locale_coverage, 'Cadence', 'Cadencia')}: `{entry.cadence}`",
            f"- {_label(locale_coverage, 'Period', 'Periodo')}: `{entry.period_start.isoformat()}` to `{entry.period_end.isoformat()}`",
            f"- {_label(locale_coverage, 'Jobs', 'Vacantes')}: {entry.metrics.job_count}",
            f"- {_label(locale_coverage, 'Observations', 'Observaciones')}: {entry.metrics.observation_count}",
            f"- {_label(locale_coverage, 'Source runs', 'Corridas fuente')}: {entry.metrics.source_run_count}",
            f"- {_label(locale_coverage, 'Assets', 'Activos')}: {_join_asset_links(entry, locale_coverage=locale_coverage, source_path=page_path, public_root=public_root)}",
            "",
        ]
    )
    lines.extend(
        _render_count_section(_label(locale_coverage, "Cities", "Ciudades"), entry.metrics.city_counts[:5])
    )
    lines.extend(
        _render_count_section(
            _label(locale_coverage, "Remote type", "Modalidad remota"),
            entry.metrics.remote_type_counts[:5],
        )
    )
    lines.extend(
        _render_count_section(
            _label(locale_coverage, "Seniority", "Seniority"),
            entry.metrics.seniority_counts[:5],
        )
    )
    lines.extend(
        _render_count_section(
            _label(locale_coverage, "Employment type", "Tipo de empleo"),
            entry.metrics.employment_type_counts[:5],
        )
    )
    lines.extend(
        _render_count_section(
            _label(locale_coverage, "Top tech stack terms", "Tecnologias principales"),
            entry.metrics.tech_stack_counts[:5],
        )
    )
    lines.extend(
        _render_count_section(
            _label(locale_coverage, "Top companies", "Empresas principales"),
            entry.metrics.top_company_counts[:5],
        )
    )
    return "\n".join(lines).strip() + "\n"


def render_downloads_page(
    index: SiteReportIndex,
    *,
    locale_coverage: tuple[str, ...],
    page_path: Path,
    public_root: Path,
) -> str:
    lines = [f"# {_label(locale_coverage, 'Downloads', 'Descargas')}", ""]
    if not index.entries:
        lines.extend(
            [
                _label(
                    locale_coverage,
                    "No downloads are available yet.",
                    "Aun no hay descargas disponibles.",
                ),
                "",
            ]
        )
        return "\n".join(lines)

    lines.extend(
        [
            f"| {_label(locale_coverage, 'Period', 'Periodo')} | {_label(locale_coverage, 'Cadence', 'Cadencia')} | {_label(locale_coverage, 'Public CSV', 'CSV publico')} | {_label(locale_coverage, 'HTML snapshots', 'Snapshots HTML')} |",
            "| --- | --- | --- | --- |",
        ]
    )
    for entry in index.entries:
        public_csv = _relative_link(page_path, public_root / entry.asset_relative_dir() / "public_jobs.csv")
        html_links = _join_html_links(
            entry,
            locale_coverage=locale_coverage,
            source_path=page_path,
            public_root=public_root,
        )
        lines.append(
            f"| {entry.period_id} | {entry.cadence} | [public_jobs.csv]({public_csv}) | {html_links} |"
        )
    lines.append("")
    return "\n".join(lines)


def render_methodology_page(*, locale_coverage: tuple[str, ...]) -> str:
    title = _label(locale_coverage, "Methodology", "Metodologia")
    lines = [f"# {title}", ""]
    lines.extend(
        [
            _label(
                locale_coverage,
                "This public site is generated from Phase 2 report artifacts, not from direct raw-source reads.",
                "Este sitio publico se genera a partir de artefactos de la fase 2 y no desde lecturas directas de las fuentes crudas.",
            ),
            "",
            f"## {_label(locale_coverage, 'Pipeline', 'Pipeline')}",
            f"- {_label(locale_coverage, 'Upstream source data is normalized into curated DuckDB and Parquet outputs.', 'Los datos fuente se normalizan a salidas curadas en DuckDB y Parquet.')}",
            f"- {_label(locale_coverage, 'Closed weekly and monthly report artifacts are generated from curated storage.', 'Los artefactos semanales y mensuales se generan a partir del almacenamiento curado.')}",
            f"- {_label(locale_coverage, 'Phase 3 copies only public-safe CSV downloads and HTML report snapshots into the public site source.', 'La fase 3 copia solo descargas CSV seguras para publico y snapshots HTML al sitio publico.')}",
            "",
            f"## {_label(locale_coverage, 'Public boundary', 'Limite publico')}",
            f"- {_label(locale_coverage, 'Row-level public downloads exclude company, URL, raw descriptions, raw job IDs, and raw OpenAI payloads.', 'Las descargas publicas excluyen empresa, URL, descripciones crudas, IDs de vacante crudos y payloads crudos de OpenAI.')}",
            f"- {_label(locale_coverage, 'Aggregate report content may reference company names only in aggregated ranking sections.', 'El contenido agregado puede mencionar empresas solo en rankings agregados.')}",
            f"- {_label(locale_coverage, 'Private drill-down remains local-only in the Streamlit app.', 'El detalle privado solo vive localmente en la app de Streamlit.')}",
            "",
        ]
    )
    return "\n".join(lines)


def _render_latest_section(
    entry: SiteReportEntry | None,
    *,
    locale_coverage: tuple[str, ...],
    source_path: Path,
    public_root: Path,
    heading_en: str,
    heading_es: str,
) -> list[str]:
    lines = [f"## {_label(locale_coverage, heading_en, heading_es)}"]
    if entry is None:
        lines.extend(
            [
                _label(locale_coverage, "No report available yet.", "Aun no hay reporte disponible."),
                "",
            ]
        )
        return lines

    period_page = public_root / entry.cadence / f"{entry.period_id}.md"
    lines.extend(
        [
            f"- {_label(locale_coverage, 'Period', 'Periodo')}: [{entry.period_id}]({_relative_link(source_path, period_page)})",
            f"- {_label(locale_coverage, 'Jobs', 'Vacantes')}: {entry.metrics.job_count}",
            f"- {_label(locale_coverage, 'Observations', 'Observaciones')}: {entry.metrics.observation_count}",
            f"- {_label(locale_coverage, 'Assets', 'Activos')}: {_join_asset_links(entry, locale_coverage=locale_coverage, source_path=source_path, public_root=public_root)}",
            "",
        ]
    )
    return lines


def _render_count_section(title: str, counts: tuple[DimensionCount, ...]) -> list[str]:
    lines = [f"## {title}"]
    if not counts:
        lines.extend(["- None", ""])
        return lines
    lines.extend([f"- {count.label}: {count.count}" for count in counts])
    lines.append("")
    return lines


def _join_asset_links(
    entry: SiteReportEntry,
    *,
    locale_coverage: tuple[str, ...],
    source_path: Path,
    public_root: Path,
) -> str:
    parts = [
        f"[public_jobs.csv]({_relative_link(source_path, public_root / entry.asset_relative_dir() / 'public_jobs.csv')})"
    ]
    html_links = _join_html_links(
        entry,
        locale_coverage=locale_coverage,
        source_path=source_path,
        public_root=public_root,
    )
    if html_links:
        parts.append(html_links)
    return " | ".join(parts)


def _join_html_links(
    entry: SiteReportEntry,
    *,
    locale_coverage: tuple[str, ...],
    source_path: Path,
    public_root: Path,
) -> str:
    links: list[str] = []
    requested = [locale for locale in locale_coverage if locale in entry.locale_coverage]
    for locale in requested:
        label = "HTML EN" if locale == "en" else "HTML ES"
        links.append(
            f"[{label}]({_relative_link(source_path, public_root / entry.asset_relative_dir() / f'report.{locale}.html')})"
        )
    return " | ".join(links)


def _relative_link(source_path: Path, target_path: Path) -> str:
    return relpath(target_path, start=source_path.parent).replace('\\', '/')


def _label(locale_coverage: tuple[str, ...], en: str, es: str) -> str:
    if set(locale_coverage) == {"en", "es"}:
        return f"{en} / {es}"
    if locale_coverage == ("es",):
        return es
    return en
