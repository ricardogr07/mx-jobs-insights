"""Detailed design for tech skills × seniority heatmap using seaborn and Plotly.

This module demonstrates two approaches:
1. Native Plotly heatmap (recommended for web embedding)
2. Seaborn + matplotlib → base64 (for more styling control)

Key Design Decisions:
- Build pivot table directly from JoinedObservationRecord tuples
- Use matplotlib DPI=100 for sharp rendering at various sizes
- Color scale uses diverging "RdYlGn" to show hot/cold skill demand
- Top-N skills selected to keep heatmap readable (max 10 skills, 5 seniority levels)
"""

from __future__ import annotations

import base64
import io
from collections import Counter, defaultdict
from typing import Optional
import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import seaborn as sns

from mexico_linkedin_jobs_portfolio.analytics.dataset import JoinedObservationRecord
from mexico_linkedin_jobs_portfolio.models import DimensionCount, ReportMetrics


# ============================================================================
# SEABORN CMAKE APPROACH (matplotlib-based)
# ============================================================================


def build_tech_seniority_pivot_from_records(
    records: tuple[JoinedObservationRecord, ...],
    top_n_skills: int = 10,
    top_n_seniorities: Optional[int] = None,
) -> pd.DataFrame:
    """Build cross-tabulation: tech_stack (rows) × seniority_level (columns).
    
    Args:
        records: Raw joined observation records with tech_stack and seniority_level
        top_n_skills: Limit to top N tech skills by frequency (for readability)
        top_n_seniorities: Limit to top N seniority levels (None = all unique)
    
    Returns:
        DataFrame with tech skills as index, seniority levels as columns, 
        job counts as values. Missing cells filled with 0.
    
    Example:
        >>> pivot = build_tech_seniority_pivot_from_records(records)
        >>> pivot
                  Entry-level  Mid-level  Senior
        Python         8           12        15
        SQL            5           15        12
        AWS            2           18         8
    """
    # Step 1: Build counter matrix
    # Structure: {(tech, seniority): count}
    cross_tab: dict[tuple[str, str], int] = defaultdict(int)
    
    for record in records:
        if not record.tech_stack or not record.seniority_level:
            continue
        
        for tech in record.tech_stack:
            cross_tab[(tech, record.seniority_level)] += 1
    
    # Step 2: Identify top skills (by total occurrences)
    skill_totals: dict[str, int] = defaultdict(int)
    for (tech, _), count in cross_tab.items():
        skill_totals[tech] += count
    
    top_skills = sorted(
        skill_totals.items(),
        key=lambda x: x[1],
        reverse=True
    )[:top_n_skills]
    top_skill_names = [skill for skill, _ in top_skills]
    
    # Step 3: Identify all seniority levels seen in top skills
    seniority_set: set[str] = set()
    for (tech, seniority), _ in cross_tab.items():
        if tech in top_skill_names:
            seniority_set.add(seniority)
    
    # Step 4: Order seniority levels logically
    # Common hierarchy: Entry-level → Mid-level → Senior
    seniority_order = [
        "Entry-level", "Mid-level", "Senior",
        "Internship", "Contract", "Executive", "Not Applicable"
    ]
    seniority_ordered = [
        s for s in seniority_order if s in seniority_set
    ]
    # Append any remaining unknown levels
    seniority_ordered += sorted(seniority_set - set(seniority_order))
    
    if top_n_seniorities:
        seniority_ordered = seniority_ordered[:top_n_seniorities]
    
    # Step 5: Build DataFrame
    data = {}
    for seniority in seniority_ordered:
        data[seniority] = [
            cross_tab[(tech, seniority)]
            for tech in top_skill_names
        ]
    
    df = pd.DataFrame(data, index=top_skill_names)
    return df


def create_seaborn_heatmap(
    pivot_df: pd.DataFrame,
    title: str = "Tech Skills by Seniority Level",
    figsize: tuple[int, int] = (12, 7),
    cmap: str = "RdYlGn",
    annot: bool = True,
    fmt: str = "d",
    cbar_label: str = "Job Count",
) -> plt.Figure:
    """Create seaborn heatmap with professional styling.
    
    Args:
        pivot_df: Cross-tabulation DataFrame (tech_skills × seniority)
        title: Chart title
        figsize: (width, height) in inches
        cmap: Colormap name (e.g., "RdYlGn", "YlOrRd", "viridis")
        annot: Show cell values as annotations
        fmt: Number format for annotations
        cbar_label: Label for colorbar
    
    Returns:
        matplotlib Figure object ready for display or conversion
    
    Best Practices Applied:
        1. Use diverging colormap (RdYlGn) to show hot/cold skill demand
        2. Square cells for better visual readability
        3. Annotations show exact counts (not just colors)
        4. Strong title and labels for context
        5. Tight layout to prevent label cutoff
    """
    fig, ax = plt.subplots(figsize=figsize, dpi=100)
    
    # Create heatmap with styling
    sns.heatmap(
        pivot_df,
        annot=annot,
        fmt=fmt,
        cmap=cmap,
        linewidths=1,
        linecolor="white",
        cbar_kws={"label": cbar_label},
        ax=ax,
        square=False,  # Set True if you prefer square cells
        vmin=0,  # Color scale starts at 0
    )
    
    # Title and labels
    ax.set_title(title, fontsize=16, fontweight="bold", pad=20)
    ax.set_xlabel("Seniority Level", fontsize=12, fontweight="bold")
    ax.set_ylabel("Technology", fontsize=12, fontweight="bold")
    
    # Improve readability
    ax.tick_params(axis="x", rotation=45)
    ax.tick_params(axis="y", rotation=0)
    
    plt.tight_layout()
    return fig


def figure_to_base64_seaborn(
    fig: plt.Figure,
    format: str = "png",
    dpi: int = 100,
) -> str:
    """Convert matplotlib figure to base64-encoded data URI for HTML embedding.
    
    Args:
        fig: matplotlib Figure object
        format: Image format ("png", "jpg", "webp")
        dpi: DPI for output image (higher = sharper but larger)
    
    Returns:
        Data URI string: "data:image/png;base64,{encoded_image}"
    
    Example:
        >>> fig = create_seaborn_heatmap(pivot_df)
        >>> data_uri = figure_to_base64_seaborn(fig)
        >>> html = f'<img src="{data_uri}" alt="Skills Heatmap">'
    """
    buffer = io.BytesIO()
    fig.savefig(buffer, format=format, dpi=dpi, bbox_inches="tight")
    buffer.seek(0)
    
    img_bytes = buffer.read()
    b64_string = base64.b64encode(img_bytes).decode("utf-8")
    mime_type = f"image/{format}"
    
    return f"data:{mime_type};base64,{b64_string}"


# ============================================================================
# PLOTLY APPROACH (recommended for web)
# ============================================================================


def create_plotly_heatmap(
    pivot_df: pd.DataFrame,
    title: str = "Tech Skills by Seniority Level",
    colorscale: str = "RdYlGn",
    locale: str = "en",
) -> go.Figure:
    """Create interactive Plotly heatmap.
    
    Args:
        pivot_df: Cross-tabulation DataFrame (tech_skills × seniority)
        title: Chart title
        colorscale: Plotly colorscale name
        locale: Language ("en" or "es" affects labels)
    
    Returns:
        Plotly Figure object (go.Figure)
    
    Advantages:
        - Interactive tooltips
        - Hover to see exact values
        - Responsive to screen size
        - No extra conversion needed for web
    """
    if locale == "es":
        title = "Habilidades Tecnológicas por Nivel de Experiencia"
        hover_label = "Ofertas: "
    else:
        hover_label = "Jobs: "
    
    fig = go.Figure(
        data=go.Heatmap(
            z=pivot_df.values,
            x=pivot_df.columns,
            y=pivot_df.index,
            colorscale=colorscale,
            text=pivot_df.values,
            texttemplate="%{text}",
            textfont={"size": 11},
            hovertemplate=(
                "<b>%{y}</b><br>"
                "%{x}: " + hover_label + "%{z}<br>"
                "<extra></extra>"
            ),
            colorbar=dict(
                title="Count",
                thickness=15,
                len=0.7,
            ),
        )
    )
    
    fig.update_layout(
        title=dict(text=title, x=0.5, xanchor="center", font=dict(size=16)),
        xaxis_title="Seniority Level",
        yaxis_title="Technology",
        height=500,
        width=1000,
        template="plotly_white",
        hovermode="closest",
        margin=dict(l=150, r=100, t=80, b=100),
    )
    
    return fig


# ============================================================================
# COMPLETE WORKFLOW EXAMPLES
# ============================================================================


def seaborn_complete_workflow(
    records: tuple[JoinedObservationRecord, ...],
    output_html_filepath: Optional[str] = None,
) -> str:
    """Complete pipeline: records → pivot → heatmap → base64.
    
    Example:
        >>> from mexico_linkedin_jobs_portfolio.analytics.dataset import CuratedDatasetReader
        >>> from mexico_linkedin_jobs_portfolio.config import CuratedStorageConfig
        >>> 
        >>> reader = CuratedDatasetReader()
        >>> dataset = reader.load(CuratedStorageConfig(...))
        >>> 
        >>> data_uri = seaborn_complete_workflow(dataset.records)
        >>> 
        >>> # Embed in HTML
        >>> html = f'''
        >>> <html>
        >>>   <body>
        >>>     <img src="{data_uri}" alt="Skills Heatmap" />
        >>>   </body>
        >>> </html>
        >>> '''
    """
    # 1. Build pivot table
    pivot = build_tech_seniority_pivot_from_records(
        records,
        top_n_skills=10,
    )
    
    if pivot.empty:
        print("Warning: No data available for heatmap (empty records or no tech_stack/seniority)")
        return ""
    
    # 2. Create figure
    fig = create_seaborn_heatmap(pivot)
    
    # 3. Convert to base64
    data_uri = figure_to_base64_seaborn(fig)
    
    # 4. Optionally save HTML
    if output_html_filepath:
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Skills Heatmap</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                img {{ max-width: 100%; height: auto; }}
            </style>
        </head>
        <body>
            <h1>Tech Skills by Seniority Level</h1>
            <img src="{data_uri}" alt="Skills Heatmap" />
        </body>
        </html>
        """
        with open(output_html_filepath, "w") as f:
            f.write(html_content)
        print(f"✓ HTML saved to {output_html_filepath}")
    
    return data_uri


def plotly_complete_workflow(
    records: tuple[JoinedObservationRecord, ...],
    locale: str = "en",
) -> go.Figure:
    """Complete pipeline: records → pivot → Plotly heatmap.
    
    Returns ready-to-embed Plotly figure (no base64 conversion needed).
    """
    pivot = build_tech_seniority_pivot_from_records(
        records,
        top_n_skills=10,
    )
    
    if pivot.empty:
        print("Warning: No data available for heatmap")
        return go.Figure()
    
    return create_plotly_heatmap(pivot, locale=locale)


# ============================================================================
# INTEGRATION WITH EXISTING ReportMetrics
# ============================================================================


def create_seniority_skills_heatmap_v2(
    metrics: ReportMetrics,
    records: tuple[JoinedObservationRecord, ...],
    locale: str = "en",
) -> go.Figure:
    """Updated heatmap function for charts.py.
    
    Integration note: This requires passing raw records to the chart function.
    Current architecture only passes ReportMetrics, so this needs integration adjustment.
    
    Workaround: Modify MetricsBuildResult to include records tuple, then pass through.
    """
    try:
        pivot = build_tech_seniority_pivot_from_records(
            records,
            top_n_skills=10,
        )
        fig = create_plotly_heatmap(pivot, locale=locale)
    except Exception as e:
        print(f"Warning: Could not generate heatmap: {e}")
        fig = go.Figure()
        fig.add_annotation(
            text="Skill heatmap data unavailable",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
        )
    
    return fig


# ============================================================================
# DESIGN NOTES & BEST PRACTICES
# ============================================================================

"""
SEABORN BEST PRACTICES APPLIED:

1. COLOR MAPPING
   ✓ Diverging colormap (RdYlGn) shows contrasts better than sequential
   ✓ vmin=0 ensures fair scale (not auto-normalized)
   ✓ Annotations show raw numbers to avoid color misinterpretation

2. READABILITY
   ✓ Top-10 skills keeps heatmap scannable (not overwhelming)
   ✓ Square-free cells allow longer skill names
   ✓ White gridlines separate cells clearly
   ✓ Rotated x-axis labels prevent overlap

3. DATA INTEGRITY
   ✓ Zero-filled for skills not present at certain seniorities
   ✓ Maintains all seniority levels for context
   ✓ Logical seniority ordering (Entry → Mid → Senior)

4. MATPLOTLIB TO BASE64
   ✓ Use BytesIO buffer (no temp files needed)
   ✓ DPI=100 works for screen; increase for print
   ✓ Data URI format embeds directly in HTML/CSS
   ✓ No external image server needed

5. PLOTLY ADVANTAGES
   ✓ Interactive tooltips (hover for exact values)
   ✓ Responsive layout (adapts to container width)
   ✓ Better accessibility with standard web tech
   ✓ No image format conversion needed

INTEGRATION CHALLENGES & SOLUTIONS:

Current Architecture Issue:
  ReportMetrics only has aggregates (tech_stack_counts, seniority_counts).
  No cross-tabulation data.

Solution 1 (Quick): Use mock synthetic data for now
  - Fill pivot with proportional estimates
  - Useful for UI/layout testing

Solution 2 (Recommended): Pass raw records through pipeline
  - Modify MetricsBuildResult to include records tuple
  - Update chart functions to accept optional records parameter
  - Build pivot on-demand when records available

Solution 3 (Future): Store pivot in database
  - Add tech_seniority_cross_tab table to curated schema
  - Pre-compute during ingestion for performance
"""
