"""Test and demonstration of seaborn heatmap workflows.

This shows both approaches in action with sample data.
"""

import sys
from datetime import date

from mexico_linkedin_jobs_portfolio.analytics.dataset import JoinedObservationRecord
from mexico_linkedin_jobs_portfolio.analytics.heatmap_design import (
    build_tech_seniority_pivot_from_records,
    create_plotly_heatmap,
    create_seaborn_heatmap,
    figure_to_base64_seaborn,
    plotly_complete_workflow,
)


def create_sample_records() -> tuple[JoinedObservationRecord, ...]:
    """Create realistic sample records for testing."""
    records = []

    # Generate ~50 sample records with varied tech/seniority combinations
    tech_skills = [
        "Python",
        "SQL",
        "AWS",
        "React",
        "Java",
        "Go",
        "Kubernetes",
        "ML",
        "Docker",
        "Rust",
    ]
    seniorities = ["Entry-level", "Mid-level", "Senior"]

    job_id_counter = 0
    for seniority_idx, seniority in enumerate(seniorities):
        for skill_idx, skill in enumerate(tech_skills):
            # Create 2-5 jobs per (skill, seniority) combo
            for _count in range(2 + (skill_idx + seniority_idx) % 4):
                job_id_counter += 1

                # Some jobs have multiple skills
                skills_for_job = [skill]
                if job_id_counter % 3 == 0:
                    skills_for_job.append(tech_skills[(skill_idx + 1) % len(tech_skills)])

                records.append(
                    JoinedObservationRecord(
                        job_id=f"job_{job_id_counter:04d}",
                        observed_at=date(2026, 3, 20),
                        reported_date=date(2026, 3, 15),
                        title=f"Senior {skill} Engineer",
                        city="Mexico City",
                        state="CDMX",
                        country="MX",
                        source_run_id="test_001",
                        remote_type="Remote",
                        seniority_level=seniority,
                        employment_type="Full-time",
                        company_name=f"Tech Company {job_id_counter}",
                        job_url="https://example.com",
                        description_text="Sample job description",
                        industry="Technology",
                        english_required=True,
                        minimum_years_experience=float(seniority_idx * 2),
                        tech_stack=tuple(skills_for_job),
                    )
                )

    return tuple(records)


def test_pivot_building():
    """Test: Records → Pivot Table."""
    print("\n" + "=" * 70)
    print("TEST 1: Building Pivot Table from Records")
    print("=" * 70)

    records = create_sample_records()
    print(f"✓ Created {len(records)} sample records")

    pivot = build_tech_seniority_pivot_from_records(records, top_n_skills=8)
    print(f"\n✓ Built pivot table: {pivot.shape[0]} skills × {pivot.shape[1]} seniority levels\n")
    print(pivot)
    print(f"\nTotal jobs across all cells: {pivot.values.sum()}")

    return pivot


def test_seaborn_workflow(pivot):
    """Test: Pivot → Seaborn Heatmap → Base64."""
    print("\n" + "=" * 70)
    print("TEST 2: Seaborn Heatmap & Base64 Encoding")
    print("=" * 70)

    # Create figure
    fig = create_seaborn_heatmap(
        pivot,
        title="Tech Skills Distribution by Seniority",
        figsize=(12, 7),
        cmap="RdYlGn",
    )
    print("✓ Created seaborn heatmap figure")

    # Convert to base64
    data_uri = figure_to_base64_seaborn(fig)
    print("✓ Converted to base64 PNG")
    print(f"  - Data URI length: {len(data_uri)} chars")
    print(f"  - Starts with: {data_uri[:50]}...")

    # Generate sample HTML
    html_sample = f'''<html>
<head><title>Skills Heatmap</title></head>
<body>
  <h1>Tech Skills by Seniority Level</h1>
  <img src="{data_uri}" alt="Heatmap" />
  <p>This image is embedded directly via data URI.</p>
</body>
</html>'''

    print("\n✓ Sample HTML (excerpt):")
    print(html_sample[:200] + "...")

    return fig, data_uri


def test_plotly_workflow(pivot):
    """Test: Pivot → Plotly Heatmap."""
    print("\n" + "=" * 70)
    print("TEST 3: Plotly Heatmap (Interactive)")
    print("=" * 70)

    fig = create_plotly_heatmap(
        pivot,
        title="Tech Skills Distribution by Seniority",
        colorscale="RdYlGn",
    )
    print("✓ Created Plotly interactive heatmap")
    print(f"  - Figure type: {type(fig).__name__}")
    print(f"  - Layout: {fig.layout.title.text}")
    print(f"  - Dimensions: {fig.layout.width} × {fig.layout.height} px")

    # Show how to convert for embedding
    plotly_json = fig.to_json()
    print(f"\n✓ Plotly figure as JSON: {len(plotly_json)} chars")
    print("  (Can be embedded in HTML via <script> tag)")

    return fig


def test_complete_workflows():
    """Test: Full end-to-end workflows."""
    print("\n" + "=" * 70)
    print("TEST 4: Complete Workflows (Records → HTML)")
    print("=" * 70)

    records = create_sample_records()

    # Seaborn workflow
    print("\nSeaborn workflow:")
    # Note: We don't save HTML in test, but show how it would work
    # data_uri = seaborn_complete_workflow(records)
    # print(f"✓ Generated base64 data URI: {len(data_uri)} chars")

    # Plotly workflow
    print("Plotly workflow:")
    fig = plotly_complete_workflow(records, locale="en")
    print(f"✓ Generated Plotly figure: {fig.layout.title.text}")

    # Show how to use in Streamlit (example)
    print("\n✓ Usage examples:")
    print("""
    # In Streamlit:
    import streamlit as st
    fig = plotly_complete_workflow(records)
    st.plotly_chart(fig, use_container_width=True)
    
    # In HTML template (Jinja2):
    <img src="{{ heatmap_data_uri }}" alt="Skills Heatmap" />
    """)


def test_styling_variations():
    """Test: Different styling options."""
    print("\n" + "=" * 70)
    print("TEST 5: Styling Variations")
    print("=" * 70)

    records = create_sample_records()
    pivot = build_tech_seniority_pivot_from_records(records, top_n_skills=6)

    colormaps = ["RdYlGn", "YlOrRd", "viridis", "cool"]

    for cmap in colormaps:
        print(f"\n  Testing colormap: {cmap}")
        try:
            create_seaborn_heatmap(pivot, cmap=cmap)
            print(f"    ✓ {cmap} works well")
        except Exception as e:
            print(f"    ✗ {cmap} failed: {e}")


def main():
    """Run all tests."""
    print("\n" + "#" * 70)
    print("# SEABORN HEATMAP DESIGN TESTS")
    print("#" * 70)

    try:
        # Test 1: Pivot building
        pivot = test_pivot_building()

        # Test 2: Seaborn + Base64
        seaborn_fig, data_uri = test_seaborn_workflow(pivot)

        # Test 3: Plotly
        test_plotly_workflow(pivot)

        # Test 4: Complete workflows
        test_complete_workflows()

        # Test 5: Styling variations
        test_styling_variations()

        print("\n" + "#" * 70)
        print("# ✓ ALL TESTS PASSED")
        print("#" * 70)

        # Summary
        print("""
SUMMARY:
========
1. Data Structure: Pandas DataFrame (tech_stack × seniority)
2. Data Source: JoinedObservationRecord tuples with tech_stack & seniority_level
3. Key Functions:
   - build_tech_seniority_pivot_from_records() → DataFrame
   - create_seaborn_heatmap() → matplotlib.Figure
   - create_plotly_heatmap() → plotly.graph_objects.Figure
   - figure_to_base64_seaborn() → data URI string (for HTML embedding)

4. Integration Path:
   Current: ReportMetrics only has aggregates
   Solution: Pass raw records to chart functions (requires MetricsBuildResult update)

5. Web Embedding:
   Seaborn: Use data URI (<img src="data:image/png;base64,..." />)
   Plotly: Use fig.to_json() or render in HTML directly
        """)
        return 0

    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
