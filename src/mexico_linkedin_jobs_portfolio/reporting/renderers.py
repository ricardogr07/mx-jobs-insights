"""Localized Markdown and HTML renderers for Phase 2 reports."""

from __future__ import annotations

from html import escape

from mexico_linkedin_jobs_portfolio.models import DimensionCount, GeneratedNarrative, ReportMetrics

_MONTH_NAMES = {
    "en": [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ],
    "es": [
        "enero",
        "febrero",
        "marzo",
        "abril",
        "mayo",
        "junio",
        "julio",
        "agosto",
        "septiembre",
        "octubre",
        "noviembre",
        "diciembre",
    ],
}

_TEXT = {
    "en": {
        "title": "Mexico LinkedIn Jobs Report",
        "period": "Period",
        "cadence": "Cadence",
        "narrative": "Narrative Summary",
        "headline_metrics": "Headline Metrics",
        "distinct_jobs": "Distinct jobs",
        "observations": "Observations",
        "source_runs": "Source runs",
        "cities": "Cities",
        "remote": "Remote type",
        "seniority": "Seniority",
        "employment": "Employment type",
        "industry": "Industry",
        "english": "English requirement",
        "experience": "Experience buckets",
        "tech_stack": "Top tech stack terms",
        "companies": "Top companies",
        "empty": "No data in this period.",
        "weekly": "Weekly",
        "monthly": "Monthly",
    },
    "es": {
        "title": "Reporte de Vacantes de LinkedIn en Mexico",
        "period": "Periodo",
        "cadence": "Cadencia",
        "narrative": "Resumen Narrativo",
        "headline_metrics": "Metricas Principales",
        "distinct_jobs": "Vacantes distintas",
        "observations": "Observaciones",
        "source_runs": "Corridas fuente",
        "cities": "Ciudades",
        "remote": "Modalidad remota",
        "seniority": "Seniority",
        "employment": "Tipo de empleo",
        "industry": "Industria",
        "english": "Requisito de ingles",
        "experience": "Rangos de experiencia",
        "tech_stack": "Tecnologias principales",
        "companies": "Empresas principales",
        "empty": "No hay datos en este periodo.",
        "weekly": "Semanal",
        "monthly": "Mensual",
    },
}


def render_markdown(metrics: ReportMetrics, narrative: GeneratedNarrative, locale: str) -> str:
    """Render one locale-specific Markdown report from the shared metrics payload."""

    text = _TEXT[locale]
    headline, bullets = narrative.for_locale(locale)
    lines = [
        f"# {text['title']}",
        "",
        f"## {text['period']}",
        f"- {text['cadence']}: {text[metrics.period.cadence]}",
        f"- {text['period']}: {_format_period_label(metrics, locale)}",
        f"- ID: `{metrics.period.period_id}`",
        f"- Range: `{metrics.period.start_date.isoformat()}` to `{metrics.period.end_date.isoformat()}`",
        "",
        f"## {text['narrative']}",
        headline,
        "",
    ]
    for bullet in bullets:
        lines.append(f"- {bullet}")

    lines.extend(
        [
            "",
            f"## {text['headline_metrics']}",
            f"- {text['distinct_jobs']}: {metrics.job_count}",
            f"- {text['observations']}: {metrics.observation_count}",
            f"- {text['source_runs']}: {metrics.source_run_count}",
            "",
        ]
    )
    lines.extend(_render_markdown_section(text["cities"], metrics.city_counts, locale))
    lines.extend(_render_markdown_section(text["remote"], metrics.remote_type_counts, locale))
    lines.extend(_render_markdown_section(text["seniority"], metrics.seniority_counts, locale))
    lines.extend(
        _render_markdown_section(text["employment"], metrics.employment_type_counts, locale)
    )
    lines.extend(_render_markdown_section(text["industry"], metrics.industry_counts, locale))
    lines.extend(
        _render_markdown_section(
            text["english"], metrics.english_requirement_counts, locale
        )
    )
    lines.extend(
        _render_markdown_section(
            text["experience"], metrics.experience_bucket_counts, locale
        )
    )
    lines.extend(_render_markdown_section(text["tech_stack"], metrics.tech_stack_counts, locale))
    lines.extend(
        _render_markdown_section(text["companies"], metrics.top_company_counts, locale)
    )
    return "\n".join(lines).strip() + "\n"


def render_html(metrics: ReportMetrics, narrative: GeneratedNarrative, locale: str) -> str:
    """Render one locale-specific standalone HTML snapshot."""

    text = _TEXT[locale]
    headline, bullets = narrative.for_locale(locale)
    sections = [
        _render_html_list(text["cities"], metrics.city_counts, locale),
        _render_html_list(text["remote"], metrics.remote_type_counts, locale),
        _render_html_list(text["seniority"], metrics.seniority_counts, locale),
        _render_html_list(text["employment"], metrics.employment_type_counts, locale),
        _render_html_list(text["industry"], metrics.industry_counts, locale),
        _render_html_list(text["english"], metrics.english_requirement_counts, locale),
        _render_html_list(text["experience"], metrics.experience_bucket_counts, locale),
        _render_html_list(text["tech_stack"], metrics.tech_stack_counts, locale),
        _render_html_list(text["companies"], metrics.top_company_counts, locale),
    ]
    bullet_html = "".join(f"<li>{escape(item)}</li>" for item in bullets)
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="' + escape(locale) + '">',
            "<head>",
            '  <meta charset="utf-8">',
            f"  <title>{escape(text['title'])}</title>",
            "  <style>",
            "    body { font-family: Georgia, serif; margin: 2rem auto; max-width: 860px; line-height: 1.55; color: #1c1917; }",
            "    h1, h2 { font-family: 'Trebuchet MS', sans-serif; }",
            "    section { margin: 1.5rem 0; }",
            "    ul { padding-left: 1.25rem; }",
            "    .meta { color: #57534e; }",
            "  </style>",
            "</head>",
            "<body>",
            f"  <h1>{escape(text['title'])}</h1>",
            '  <section class="meta">',
            f"    <p><strong>{escape(text['cadence'])}:</strong> {escape(text[metrics.period.cadence])}</p>",
            f"    <p><strong>{escape(text['period'])}:</strong> {escape(_format_period_label(metrics, locale))}</p>",
            f"    <p><strong>ID:</strong> {escape(metrics.period.period_id)}</p>",
            f"    <p><strong>Range:</strong> {escape(metrics.period.start_date.isoformat())} to {escape(metrics.period.end_date.isoformat())}</p>",
            "  </section>",
            "  <section>",
            f"    <h2>{escape(text['narrative'])}</h2>",
            f"    <p>{escape(headline)}</p>",
            f"    <ul>{bullet_html}</ul>",
            "  </section>",
            "  <section>",
            f"    <h2>{escape(text['headline_metrics'])}</h2>",
            "    <ul>",
            f"      <li>{escape(text['distinct_jobs'])}: {metrics.job_count}</li>",
            f"      <li>{escape(text['observations'])}: {metrics.observation_count}</li>",
            f"      <li>{escape(text['source_runs'])}: {metrics.source_run_count}</li>",
            "    </ul>",
            "  </section>",
            *sections,
            "</body>",
            "</html>",
        ]
    )


def _render_markdown_section(title: str, items: tuple[DimensionCount, ...], locale: str) -> list[str]:
    lines = [f"## {title}"]
    if not items:
        lines.extend([f"- {_TEXT[locale]['empty']}", ""])
        return lines
    lines.extend([f"- {item.label}: {item.count}" for item in items])
    lines.append("")
    return lines


def _render_html_list(title: str, items: tuple[DimensionCount, ...], locale: str) -> str:
    if items:
        rows = "".join(f"<li>{escape(item.label)}: {item.count}</li>" for item in items)
    else:
        rows = f"<li>{escape(_TEXT[locale]['empty'])}</li>"
    return "\n".join(
        [
            "  <section>",
            f"    <h2>{escape(title)}</h2>",
            f"    <ul>{rows}</ul>",
            "  </section>",
        ]
    )


def _format_period_label(metrics: ReportMetrics, locale: str) -> str:
    if metrics.period.cadence == "weekly":
        _, iso_week = metrics.period.period_id.split("-W", maxsplit=1)
        if locale == "es":
            return f"Semana {int(iso_week)} de {metrics.period.end_date.isocalendar().year}"
        return f"Week {int(iso_week)}, {metrics.period.end_date.isocalendar().year}"

    month_name = _MONTH_NAMES[locale][metrics.period.start_date.month - 1]
    return f"{month_name} {metrics.period.start_date.year}"
