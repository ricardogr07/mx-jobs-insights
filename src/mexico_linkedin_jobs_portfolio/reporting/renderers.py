"""Localized Markdown and HTML renderers for report artifacts."""

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
    """Render one locale-specific standalone HTML snapshot with charts and improved styling."""

    text = _TEXT[locale]
    headline, bullets = narrative.for_locale(locale)
    
    # Try to generate charts if plotly is available
    charts_html = _render_charts_section(metrics, locale)
    maps_html = _render_maps_section(metrics, locale)
    analysis_html = _render_analysis_section(metrics, locale)
    
    # Build dimension sections
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
            '  <meta name="viewport" content="width=device-width, initial-scale=1.0">',
            f"  <title>{escape(text['title'])}</title>",
            "  <style>",
            _get_css_styles(),
            "  </style>",
            "</head>",
            "<body>",
            f"  <header class=\"report-header\">",
            f"    <h1>{escape(text['title'])}</h1>",
            f"    <p class=\"period-label\">{escape(_format_period_label(metrics, locale))}</p>",
            "  </header>",
            '  <nav class="report-nav">',
            '    <a href="#overview">Overview</a> | ',
            '    <a href="#charts">Charts</a> | ',
            '    <a href="#maps">Maps</a> | ',
            '    <a href="#analysis">Analysis</a> | ',
            '    <a href="#details">Details</a>',
            "  </nav>",
            '  <main class="report-content">',
            '    <section id="overview" class="section-overview">',
            f"      <h2>{escape(text['narrative'])}</h2>",
            f"      <p class=\"narrative-headline\">{escape(headline)}</p>",
            f"      <ul class=\"narrative-bullets\">{bullet_html}</ul>",
            "    </section>",
            '    <section class="section-metrics">',
            f"      <h2>{escape(text['headline_metrics'])}</h2>",
            '      <div class="metrics-grid">',
            f'        <div class="metric-card"><span class="metric-label">{escape(text["distinct_jobs"])}</span><span class="metric-value">{metrics.job_count}</span></div>',
            f'        <div class="metric-card"><span class="metric-label">{escape(text["observations"])}</span><span class="metric-value">{metrics.observation_count}</span></div>',
            f'        <div class="metric-card"><span class="metric-label">{escape(text["source_runs"])}</span><span class="metric-value">{metrics.source_run_count}</span></div>',
            "      </div>",
            "    </section>",
            charts_html,
            maps_html,
            analysis_html,
            '    <section id="details" class="section-details">',
            '      <h2 style="margin-top: 2rem;">Data Breakdown</h2>',
            *sections,
            "    </section>",
            '    <footer class="report-footer">',
            f"      <p><small>Period ID: {escape(metrics.period.period_id)} | Range: {escape(metrics.period.start_date.isoformat())} to {escape(metrics.period.end_date.isoformat())}</small></p>",
            "    </footer>",
            "  </main>",
            "</body>",
            "</html>",
        ]
    )


def _get_css_styles() -> str:
    """Enhanced CSS styles for report layout."""
    return """
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #2c3e50;
            background: linear-gradient(135deg, #f5f7fa 0%, #f9fafb 100%);
            padding: 1rem;
        }
        
        header.report-header {
            text-align: center;
            padding: 2rem 1rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 12px;
            margin-bottom: 1.5rem;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        header h1 {
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
            font-weight: 700;
        }
        
        .period-label {
            font-size: 1.1rem;
            opacity: 0.95;
            font-weight: 500;
        }
        
        nav.report-nav {
            text-align: center;
            padding: 1rem;
            margin-bottom: 1.5rem;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }
        
        nav a {
            color: #667eea;
            text-decoration: none;
            font-weight: 500;
            margin: 0 1rem;
            transition: color 0.3s ease;
        }
        
        nav a:hover { color: #764ba2; }
        
        main.report-content {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        section {
            background: white;
            border-radius: 10px;
            padding: 2rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        section:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(0,0,0,0.12);
        }
        
        h2 {
            color: #2c3e50;
            font-size: 1.8rem;
            margin-bottom: 1.2rem;
            border-bottom: 3px solid #667eea;
            padding-bottom: 0.7rem;
        }
        
        .section-metrics {
            background: linear-gradient(135deg, #f5f7fa 0%, #e9ecef 100%);
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            margin-top: 1.5rem;
        }
        
        .metric-card {
            background: white;
            border-radius: 10px;
            padding: 1.5rem;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            border-left: 4px solid #667eea;
            transition: all 0.3s ease;
        }
        
        .metric-card:hover {
            transform: scale(1.05);
            box-shadow: 0 6px 16px rgba(102, 126, 234, 0.2);
        }
        
        .metric-label {
            display: block;
            font-size: 0.85rem;
            color: #7a8896;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 0.5rem;
            font-weight: 600;
        }
        
        .metric-value {
            display: block;
            font-size: 2rem;
            color: #667eea;
            font-weight: 700;
        }
        
        .section-charts {
            background: #fafbfc;
        }
        
        .charts-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 2rem;
            margin-top: 1.5rem;
        }
        
        .chart-container {
            background: white;
            border-radius: 8px;
            padding: 1rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }
        
        .chart-container img {
            width: 100%;
            height: auto;
            display: block;
            border-radius: 6px;
        }
        
        .section-details ul {
            list-style: none;
            padding-left: 0;
        }
        
        .section-details li {
            padding: 0.7rem 0;
            border-bottom: 1px solid #e9ecef;
            display: flex;
            justify-content: space-between;
        }
        
        .section-details li:last-child {
            border-bottom: none;
        }
        
        .section-details li:nth-child(odd) {
            background: rgba(102, 126, 234, 0.02);
            padding: 0.7rem 0.7rem;
            border-radius: 4px;
        }
        
        .narrative-headline {
            font-size: 1.1rem;
            color: #555;
            margin-bottom: 1rem;
            font-weight: 500;
        }
        
        .narrative-bullets {
            list-style-position: inside;
            margin-left: 1rem;
        }
        
        .narrative-bullets li {
            margin-bottom: 0.6rem;
            line-height: 1.5;
        }
        
        footer.report-footer {
            text-align: center;
            color: #7a8896;
            font-size: 0.9rem;
            padding-top: 2rem;
            border-top: 1px solid #e9ecef;
            margin-top: 2rem;
        }
        
        .section-maps {
            background: linear-gradient(135deg, #f5f7fa 0%, #f9fafb 100%);
        }
        
        .maps-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
            gap: 2rem;
            margin-top: 1.5rem;
        }
        
        .map-container-wrapper {
            background: white;
            border-radius: 10px;
            padding: 1rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            border-left: 4px solid #667eea;
            overflow: hidden;
            transition: all 0.3s ease;
            display: flex;
            flex-direction: column;
            min-height: 550px;
        }
        
        .map-container-wrapper:hover {
            box-shadow: 0 6px 16px rgba(102, 126, 234, 0.15);
            transform: translateY(-2px);
        }
        
        .map-canvas {
            flex: 1;
            min-height: 500px;
            border-radius: 6px;
            overflow: hidden;
            position: relative;
        }
        
        .map-canvas .leaflet-container {
            width: 100%;
            height: 100%;
            border-radius: 6px;
            font-family: inherit;
        }
        
        .map-canvas .leaflet-control {
            border-radius: 6px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.1);
        }
        
        .map-canvas .leaflet-control-zoom a {
            background: white;
            color: #667eea;
            font-weight: 600;
            transition: all 0.2s ease;
        }
        
        .map-canvas .leaflet-control-zoom a:hover {
            background: #667eea;
            color: white;
        }
        
        .map-description {
            font-size: 0.95rem;
            color: #666;
            margin-bottom: 1.5rem;
            font-style: italic;
        }
        
        .section-analysis {
            background: linear-gradient(135deg, #f5f7fa 0%, #f9fafb 100%);
        }
        
        .analysis-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 2rem;
            margin-top: 1.5rem;
        }
        
        .analysis-container {
            background: white;
            border-radius: 10px;
            padding: 1.5rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            border-top: 4px solid #667eea;
            overflow: hidden;
            transition: all 0.3s ease;
        }
        
        .analysis-container:hover {
            box-shadow: 0 6px 16px rgba(102, 126, 234, 0.15);
            transform: translateY(-2px);
        }
        
        .analysis-container img {
            width: 100%;
            height: auto;
            display: block;
            border-radius: 6px;
            margin-top: 0.5rem;
        }
        
        @media (max-width: 768px) {
            header h1 { font-size: 1.8rem; }
            .maps-grid { grid-template-columns: 1fr; }
            .analysis-grid { grid-template-columns: 1fr; }
            .map-canvas { min-height: 400px; }
            .map-container-wrapper { min-height: 450px; }
            h2 { font-size: 1.4rem; }
            .charts-grid { grid-template-columns: 1fr; }
            nav a { margin: 0 0.5rem; font-size: 0.95rem; }
            .metrics-grid { grid-template-columns: 1fr; }
        }
"""


def _render_charts_section(metrics: ReportMetrics, locale: str) -> str:
    """Generate HTML section with embedded charts."""
    try:
        from mexico_linkedin_jobs_portfolio.analytics.charts import (
            create_all_charts,
            figure_to_base64_png,
        )
    except ImportError:
        # Plotly not available, skip charts
        return ""
    
    chart_labels = {
        "en": {
            "top_cities": "Top 10 Cities",
            "seniority_dist": "Seniority Distribution",
            "remote_dist": "Remote vs On-site",
            "tech_stack": "Top Technologies",
            "employment": "Employment Type",
            "companies": "Top Hiring Companies",
            "industries": "Top Industries",
        },
        "es": {
            "top_cities": "Top 10 Ciudades",
            "seniority_dist": "Distribución por Antigüedad",
            "remote_dist": "Remoto vs Presencial",
            "tech_stack": "Principales Tecnologías",
            "employment": "Tipo de Empleador",
            "companies": "Top Empresas Contratando",
            "industries": "Top Industrias",
        },
    }
    
    labels = chart_labels.get(locale, chart_labels["en"])
    
    try:
        charts = create_all_charts(metrics, locale)
        chart_divs = []
        
        for chart_key, fig in charts.items():
            try:
                img_b64 = figure_to_base64_png(fig, width=950, height=600)
                if img_b64:
                    label = labels.get(chart_key, chart_key)
                    chart_divs.append(
                        f'    <div class="chart-container"><img src="{img_b64}" alt="{escape(label)}" title="{escape(label)}"></div>'
                    )
            except Exception:
                # Skip chart if generation fails
                pass
        
        if not chart_divs:
            return ""
        
        section_title = "Visualizations" if locale == "en" else "Visualizaciones"
        return "\n".join(
            [
                '    <section id="charts" class="section-charts">',
                f"      <h2>{escape(section_title)}</h2>",
                '      <div class="charts-grid">',
                *chart_divs,
                "      </div>",
                "    </section>",
            ]
        )
    except Exception:
        # If any error, just skip charts section
        return ""


def _render_maps_section(metrics: ReportMetrics, locale: str) -> str:
    """Generate HTML section with embedded job distribution map."""
    try:
        from mexico_linkedin_jobs_portfolio.analytics.charts import (
            create_jobs_distribution_map,
        )
    except ImportError:
        # Folium not available, skip maps
        return ""
    
    map_labels = {
        "en": {
            "section_title": "Job Distribution Map",
            "map_description": "Interactive map showing job distribution across Mexican cities",
        },
        "es": {
            "section_title": "Mapa de Distribución de Empleos",
            "map_description": "Mapa interactivo mostrando la distribución de empleos en ciudades mexicanas",
        },
    }
    
    labels = map_labels.get(locale, map_labels["en"])
    
    try:
        map_html = create_jobs_distribution_map(metrics, locale)
        if not map_html:
            return ""
        
        # Wrap folium map HTML in container div with proper styling
        return "\n".join(
            [
                '    <section id="maps" class="section-maps">',
                f"      <h2>{escape(labels['section_title'])}</h2>",
                f"      <p class=\"map-description\">{escape(labels['map_description'])}</p>",
                '      <div class="maps-grid">',
                '        <div class="map-container-wrapper">',
                '          <div class="map-canvas">',
                map_html,
                "          </div>",
                "        </div>",
                "      </div>",
                "    </section>",
            ]
        )
    except Exception:
        # If any error, just skip maps section
        return ""


def _render_analysis_section(metrics: ReportMetrics, locale: str) -> str:
    """Generate HTML section with tech heatmap and word cloud."""
    try:
        from mexico_linkedin_jobs_portfolio.analytics.charts import (
            create_tech_stack_overview_heatmap,
            create_word_cloud_text,
            figure_to_base64_png,
        )
    except ImportError:
        return ""
    
    analysis_labels = {
        "en": {
            "section_title": "Technology Analysis",
            "heatmap_title": "Tech Stack Heatmap",
            "heatmap_desc": "Technology prominence and frequency in job listings",
            "wordcloud_title": "Tech Stack Word Cloud",
            "wordcloud_desc": "Visual representation of technology frequency and prominence",
        },
        "es": {
            "section_title": "Análisis Tecnológico",
            "heatmap_title": "Mapa de Calor de Stack Tecnológico",
            "heatmap_desc": "Prominencia y frecuencia de tecnologías en las ofertas",
            "wordcloud_title": "Nube de Palabras de Stack Tecnológico",
            "wordcloud_desc": "Representación visual de la frecuencia y prominencia de tecnologías",
        },
    }
    
    labels = analysis_labels.get(locale, analysis_labels["en"])
    
    try:
        containers = []
        
        # Generate heatmap
        try:
            fig = create_tech_stack_overview_heatmap(metrics, locale)
            img_b64 = figure_to_base64_png(fig, width=950, height=600)
            
            if img_b64:
                containers.append(
                    f'        <div class="analysis-container">'
                    f'          <h3>{escape(labels["heatmap_title"])}</h3>'
                    f'          <p style="font-size: 0.9rem; color: #666;">{escape(labels["heatmap_desc"])}</p>'
                    f'          <img src="{img_b64}" alt="{escape(labels["heatmap_title"])}" title="{escape(labels["heatmap_title"])}">'
                    f'        </div>'
                )
        except Exception:
            pass
        
        # Generate word cloud
        try:
            img_b64 = create_word_cloud_text(metrics)
            
            if img_b64:
                containers.append(
                    f'        <div class="analysis-container">'
                    f'          <h3>{escape(labels["wordcloud_title"])}</h3>'
                    f'          <p style="font-size: 0.9rem; color: #666;">{escape(labels["wordcloud_desc"])}</p>'
                    f'          <img src="{img_b64}" alt="{escape(labels["wordcloud_title"])}" title="{escape(labels["wordcloud_title"])}">'
                    f'        </div>'
                )
        except Exception:
            pass
        
        if not containers:
            return ""
        
        return "\n".join(
            [
                '    <section id="analysis" class="section-analysis">',
                f"      <h2>{escape(labels['section_title'])}</h2>",
                '      <div class="analysis-grid">',
                *containers,
                "      </div>",
                "    </section>",
            ]
        )
    except Exception:
        return ""


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

