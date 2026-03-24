"""Chart generation for report visualizations using Plotly."""

from __future__ import annotations

import base64
from io import BytesIO

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from mexico_linkedin_jobs_portfolio.models import DimensionCount, ReportMetrics


def figure_to_base64_png(fig: go.Figure, width: int = 1000, height: int = 600) -> str:
    """Convert Plotly figure to base64-encoded PNG string for HTML embedding."""
    try:
        img_bytes = fig.to_image(format="png", width=width, height=height)
        b64 = base64.b64encode(img_bytes).decode("utf-8")
        return f"data:image/png;base64,{b64}"
    except Exception:
        # Fallback: return empty/placeholder if kaleido not installed
        return ""


def create_top_cities_chart(metrics: ReportMetrics, locale: str = "en") -> go.Figure:
    """Bar chart: top 10 cities by job count."""
    top_n = min(10, len(metrics.city_counts))
    cities = metrics.city_counts[:top_n]
    
    labels = [item.label for item in cities]
    values = [item.count for item in cities]
    
    fig = go.Figure(
        data=[
            go.Bar(
                x=labels,
                y=values,
                marker_color="rgba(99, 110, 250, 0.8)",
                text=values,
                textposition="outside",
                hovertemplate="<b>%{x}</b><br>Jobs: %{y}<extra></extra>",
            )
        ]
    )
    
    title = "Top 10 Cities" if locale == "en" else "Top 10 Ciudades"
    fig.update_layout(
        title=title,
        xaxis_title="City" if locale == "en" else "Ciudad",
        yaxis_title="Job Count" if locale == "en" else "Conteo de Empleos",
        template="plotly_white",
        height=500,
        showlegend=False,
        hovermode="x unified",
    )
    fig.update_xaxes(tickangle=-45)
    return fig


def create_seniority_distribution_chart(metrics: ReportMetrics, locale: str = "en") -> go.Figure:
    """Pie chart: job distribution by seniority level."""
    seniority = metrics.seniority_counts
    
    labels = [item.label for item in seniority]
    values = [item.count for item in seniority]
    
    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hovertemplate="<b>%{label}</b><br>Jobs: %{value} (%{percent})<extra></extra>",
                marker=dict(
                    colors=[
                        "rgba(99, 110, 250, 0.9)",
                        "rgba(239, 85, 59, 0.9)",
                        "rgba(0, 204, 150, 0.9)",
                        "rgba(171, 99, 250, 0.9)",
                        "rgba(255, 161, 90, 0.9)",
                    ]
                ),
            )
        ]
    )
    
    title = "Seniority Distribution" if locale == "en" else "Distribución de Antigüedad"
    fig.update_layout(
        title=title,
        template="plotly_white",
        height=500,
    )
    return fig


def create_remote_distribution_chart(metrics: ReportMetrics, locale: str = "en") -> go.Figure:
    """Pie chart: job distribution by remote type."""
    remote = metrics.remote_type_counts
    
    labels = [item.label for item in remote]
    values = [item.count for item in remote]
    
    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hovertemplate="<b>%{label}</b><br>Jobs: %{value} (%{percent})<extra></extra>",
                marker=dict(
                    colors=[
                        "rgba(99, 110, 250, 0.9)",
                        "rgba(239, 85, 59, 0.9)",
                        "rgba(0, 204, 150, 0.9)",
                    ]
                ),
            )
        ]
    )
    
    title = "Remote vs On-site" if locale == "en" else "Remoto vs Presencial"
    fig.update_layout(
        title=title,
        template="plotly_white",
        height=500,
    )
    return fig


def create_top_tech_stack_chart(metrics: ReportMetrics, locale: str = "en") -> go.Figure:
    """Bar chart: top technologies/skills mentioned."""
    tech = metrics.tech_stack_counts
    top_n = min(12, len(tech))
    top_tech = tech[:top_n]
    
    labels = [item.label for item in top_tech]
    values = [item.count for item in top_tech]
    
    fig = go.Figure(
        data=[
            go.Bar(
                y=labels,
                x=values,
                orientation="h",
                marker_color="rgba(0, 204, 150, 0.8)",
                text=values,
                textposition="outside",
                hovertemplate="<b>%{y}</b><br>Jobs: %{x}<extra></extra>",
            )
        ]
    )
    
    title = "Top 12 Technologies" if locale == "en" else "Top 12 Tecnologías"
    fig.update_layout(
        title=title,
        xaxis_title="Job Mentions" if locale == "en" else "Menciones en Empleos",
        yaxis_title="Technology" if locale == "en" else "Tecnología",
        template="plotly_white",
        height=550,
        showlegend=False,
        hovermode="y unified",
    )
    return fig


def create_employment_type_chart(metrics: ReportMetrics, locale: str = "en") -> go.Figure:
    """Bar chart: employment type distribution."""
    employment = metrics.employment_type_counts
    
    labels = [item.label for item in employment]
    values = [item.count for item in employment]
    
    fig = go.Figure(
        data=[
            go.Bar(
                x=labels,
                y=values,
                marker_color="rgba(171, 99, 250, 0.8)",
                text=values,
                textposition="outside",
                hovertemplate="<b>%{x}</b><br>Jobs: %{y}<extra></extra>",
            )
        ]
    )
    
    title = "Employment Type" if locale == "en" else "Tipo de Empleador"
    fig.update_layout(
        title=title,
        xaxis_title="Employment Type" if locale == "en" else "Tipo de Empleador",
        yaxis_title="Job Count" if locale == "en" else "Conteo de Empleos",
        template="plotly_white",
        height=500,
        showlegend=False,
        hovermode="x unified",
    )
    fig.update_xaxes(tickangle=-45)
    return fig


def create_top_companies_chart(metrics: ReportMetrics, locale: str = "en") -> go.Figure:
    """Horizontal bar chart: top hiring companies."""
    companies = metrics.top_company_counts
    top_n = min(10, len(companies))
    top_companies = companies[:top_n]
    
    labels = [item.label for item in top_companies]
    values = [item.count for item in top_companies]
    
    fig = go.Figure(
        data=[
            go.Bar(
                y=labels,
                x=values,
                orientation="h",
                marker_color="rgba(239, 85, 59, 0.8)",
                text=values,
                textposition="outside",
                hovertemplate="<b>%{y}</b><br>Openings: %{x}<extra></extra>",
            )
        ]
    )
    
    title = "Top 10 Hiring Companies" if locale == "en" else "Top 10 Empresas Contratando"
    fig.update_layout(
        title=title,
        xaxis_title="Job Openings" if locale == "en" else "Vacantes",
        yaxis_title="Company" if locale == "en" else "Empresa",
        template="plotly_white",
        height=500,
        showlegend=False,
        hovermode="y unified",
    )
    return fig


def create_industry_distribution_chart(metrics: ReportMetrics, locale: str = "en") -> go.Figure:
    """Horizontal bar chart: top industries."""
    industries = metrics.industry_counts
    top_n = min(10, len(industries))
    top_industries = industries[:top_n]
    
    labels = [item.label for item in top_industries]
    values = [item.count for item in top_industries]
    
    fig = go.Figure(
        data=[
            go.Bar(
                y=labels,
                x=values,
                orientation="h",
                marker_color="rgba(255, 161, 90, 0.8)",
                text=values,
                textposition="outside",
                hovertemplate="<b>%{y}</b><br>Jobs: %{x}<extra></extra>",
            )
        ]
    )
    
    title = "Top 10 Industries" if locale == "en" else "Top 10 Industrias"
    fig.update_layout(
        title=title,
        xaxis_title="Job Count" if locale == "en" else "Conteo de Empleos",
        yaxis_title="Industry" if locale == "en" else "Industria",
        template="plotly_white",
        height=500,
        showlegend=False,
        hovermode="y unified",
    )
    return fig


def create_seniority_skills_heatmap(metrics: ReportMetrics, locale: str = "en") -> go.Figure:
    """Summary heatmap showing skill relevance across seniority levels.
    
    This is a stylized heatmap showing how many jobs at each seniority level
    mention top technologies.
    """
    # For this version, we'll create a simple matrix showing distribution
    # This is a placeholder that shows top 8 tech x 5 seniority combos
    fig = go.Figure()
    
    title = "Technology Alignment (Skill Popularity)" if locale == "en" else "Alineación Tecnológica"
    fig.update_layout(
        title=title,
        template="plotly_white",
        height=400,
        annotations=[
            dict(
                text="Chart data aggregation coming in Phase 2",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=14, color="#999"),
            )
        ],
    )
    return fig


def create_all_charts(metrics: ReportMetrics, locale: str = "en") -> dict[str, go.Figure]:
    """Generate all report charts."""
    return {
        "top_cities": create_top_cities_chart(metrics, locale),
        "seniority_dist": create_seniority_distribution_chart(metrics, locale),
        "remote_dist": create_remote_distribution_chart(metrics, locale),
        "tech_stack": create_top_tech_stack_chart(metrics, locale),
        "employment": create_employment_type_chart(metrics, locale),
        "companies": create_top_companies_chart(metrics, locale),
        "industries": create_industry_distribution_chart(metrics, locale),
    }
