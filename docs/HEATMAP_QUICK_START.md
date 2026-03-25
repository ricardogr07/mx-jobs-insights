# Seaborn Heatmap - Quick Reference Guide

## What Was Delivered

| Item | Location | Status |
|------|----------|--------|
| **Design Module** | `heatmap_design.py` | ✓ Complete (364 lines) |
| **Test Suite** | `test_heatmap_design.py` | ✓ Complete, all tests pass |
| **Design Doc** | `docs/HEATMAP_DESIGN.md` | ✓ Complete (detailed blueprint) |
| **Functionality** | Both Seaborn + Plotly | ✓ Both working |
| **Base64 Conversion** | Data URI embedding | ✓ Working (48KB per image) |

---

## 5-Minute Summary

### The Problem
Your ReportMetrics has separate `tech_stack_counts` and `seniority_counts` tuples (aggregates only). You need cross-tabulation (tech × seniority) to visualize skill demand patterns across experience levels.

### The Solution
```python
# 1. Get raw records (they have tech_stack + seniority_level fields)
records = dataset.records  # from CuratedDatasetReader

# 2. Build cross-tab pivot table
pivot = build_tech_seniority_pivot_from_records(records)
#
#            Entry-level  Mid-level  Senior
# Python              8         12        15
# SQL                 5         15        12
# AWS                 2         18         8

# 3. Create visualization
fig = create_seaborn_heatmap(pivot)         # matplotlib version
# OR
fig = create_plotly_heatmap(pivot)          # interactive version

# 4. Convert to base64 for HTML embedding
data_uri = figure_to_base64_seaborn(fig)
html = f'<img src="{data_uri}" />'          # Direct embedding, no server needed
```

---

## Key Concepts

### 1. Data Structure
```
Input: JoinedObservationRecord tuples
  - job_id, tech_stack (tuple), seniority_level (str), ...

Processing:
  - Counter("Python", "Mid-level") = 12 jobs match both
  - Build matrix with all combinations

Output: pandas DataFrame
  Index = Tech Skills (rows)
  Columns = Seniority Levels
  Values = Job counts
```

### 2. Two Approaches

**SEABORN (Static PNG)**
```python
fig = create_seaborn_heatmap(pivot, cmap="RdYlGn")
data_uri = figure_to_base64_seaborn(fig)
# Result: ~50KB base64 PNG, embeds in <img> tag
```

**PLOTLY (Interactive)**
```python
fig = create_plotly_heatmap(pivot)
# Result: Interactive chart, hover for values, zoom/pan
```

### 3. Color Theory
- **RdYlGn**: Red (high demand) → Yellow → Green (low demand)
- **YlOrRd**: Better for showing intensity only
- **Viridis**: Colorblind-friendly, sequential

**Recommendation**: Use **RdYlGn (diverging)** to show contrasts (where skills are hot vs. cold).

### 4. Base64 Flow
```
matplotlib Figure
      ↓
savefig(BytesIO)     [No temp files]
      ↓
read bytes
      ↓
base64.b64encode()   [Standard library]
      ↓
Prepend "data:image/png;base64,"
      ↓
<img src="data:..." />   [Works anywhere HTML works]
```

---

## Complete Example: Records → HTML Report

```python
# Step 1: Load data
from mexico_linkedin_jobs_portfolio.analytics.dataset import CuratedDatasetReader
reader = CuratedDatasetReader()
dataset = reader.load(config)

# Step 2: Build chart
from mexico_linkedin_jobs_portfolio.analytics.heatmap_design import (
    build_tech_seniority_pivot_from_records,
    create_seaborn_heatmap,
    figure_to_base64_seaborn,
)

pivot = build_tech_seniority_pivot_from_records(dataset.records, top_n_skills=10)
fig = create_seaborn_heatmap(pivot)
data_uri = figure_to_base64_seaborn(fig)

# Step 3: Generate HTML report
html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Mexico Jobs - Tech Skills Analysis</title>
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; margin: 40px; background: #f5f5f5; }}
        .container {{ background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 3px solid #007bff; padding-bottom: 10px; }}
        img {{ max-width: 100%; height: auto; }}
        .footer {{ margin-top: 20px; color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Tech Skills by Seniority Level</h1>
        <p>This heatmap shows how many jobs at each experience level require specific technologies.</p>
        <p><strong>Interpretation:</strong> Darker colors = more jobs requiring that skill at that level.</p>
        <img src="{data_uri}" alt="Skills Heatmap" />
        <div class="footer">
            Generated on 2026-03-24 | Data from Mexico LinkedIn Jobs Dataset
        </div>
    </div>
</body>
</html>
"""

# Step 4: Save or serve
with open("skills_report.html", "w") as f:
    f.write(html_content)
print("✓ Report saved: skills_report.html")  # Open in browser!
```

---

## Function Reference

### Core Functions

```python
# Main entry point
pivot = build_tech_seniority_pivot_from_records(
    records: tuple[JoinedObservationRecord, ...],
    top_n_skills: int = 10,
    top_n_seniorities: Optional[int] = None,
) → pd.DataFrame

# Seaborn pipeline
fig = create_seaborn_heatmap(
    pivot_df: pd.DataFrame,
    title: str = "...",
    figsize: tuple = (12, 7),
    cmap: str = "RdYlGn",      # Color scheme
    annot: bool = True,         # Show cell values
) → plt.Figure

data_uri = figure_to_base64_seaborn(
    fig: plt.Figure,
    format: str = "png",       # png, jpg, webp
    dpi: int = 100,            # 100=screen, 150=print
) → str                         # "data:image/png;base64,..."

# Plotly alternative
fig = create_plotly_heatmap(
    pivot_df: pd.DataFrame,
    locale: str = "en",
) → go.Figure

# One-shot workflows
data_uri = seaborn_complete_workflow(records)
fig = plotly_complete_workflow(records, locale="en")
```

---

## Integration with Your Project

### Current Architecture
```
ReportMetrics (aggregates only)
    ↓
chart functions
    ↓
Plotly figures
Issue: No cross-tabulation, no raw records passed
```

### Minimal Fix (Recommended)
```python
# In charts.py, update function signature:
def create_seniority_skills_heatmap(
    metrics: ReportMetrics,
    records: Optional[tuple[JoinedObservationRecord, ...]] = None,
) → go.Figure:
    if records:
        pivot = build_tech_seniority_pivot_from_records(records)
        return create_plotly_heatmap(pivot)
    else:
        return _placeholder()  # Fallback

# In metrics.py, pass records:
charts = create_all_charts(
    metrics,
    records=build_result.records  # ← Need to add this
)
```

### Future Integration (v2)
```python
# Modify MetricsBuildResult:
@dataclass
class MetricsBuildResult:
    metrics: ReportMetrics
    latest_jobs: tuple[LatestJobRecord, ...]
    records: tuple[JoinedObservationRecord, ...]  # ← ADD THIS

# Then no changes needed in chart functions
```

---

## Testing & Validation

```bash
# Run all tests
python -m pytest tests/test_heatmap_design.py -v

# Results:
# ✓ Pivot building from records works
# ✓ Seaborn styling works
# ✓ Plotly generation works
# ✓ Base64 conversion produces valid data URIs
# ✓ All 4 colormaps work (RdYlGn, YlOrRd, viridis, cool)
# ✓ Complete workflows execute end-to-end
```

---

## Files Overview

### `heatmap_design.py` (364 lines)
- **Pivot building**: Cross-tab logic using defaultdict + Counter
- **Seaborn heatmap**: Full styling with best practices applied
- **Plotly heatmap**: Interactive alternative with tooltips
- **Base64 conversion**: Buffer → bytes → base64 → data URI
- **Complete workflows**: Records → visualization end-to-end
- **Integration helpers**: Ready-to-use functions for charts.py

### `test_heatmap_design.py` (217 lines)
- **Sample data**: Realistic JoinedObservationRecord generators
- **5 test suites**: Pivot, seaborn, Plotly, workflows, styling
- **Validation**: All components tested with real data flow
- **Usage examples**: Copy-paste ready code snippets

### `docs/HEATMAP_DESIGN.md` (420 lines)
- **Complete blueprint**: Design decisions explained
- **Data flow diagrams**: Visual architecture
- **Best practices**: Seaborn styling theory & application
- **Integration paths**: Current state → recommended solution
- **Quick start**: Copy-paste to get started

---

## Common Questions

**Q: Should I use Seaborn or Plotly?**
A: **Plotly for production** (interactive, web-native). **Seaborn for quick exports** (familiar to data scientists).

**Q: How big is the base64 image?**
A: ~50-60KB for figsize=(12,7), dpi=100. Add more if needed.

**Q: Can I embed this directly in a Streamlit app?**
A: Yes! `st.plotly_chart(fig)` works directly.

**Q: What if ReportMetrics doesn't have raw records?**
A: Use mock synthetic data for UI testing, or implement L2/L3 integration path to access records.

**Q: Why RdYlGn colormap?**
A: Diverging colormaps show contrasts better (skill is hot at Senior but cold at Entry-level), plus it's somewhat colorblind-friendly.

---

## Status: ✓ READY TO USE

All implementations tested and working. No additional dependencies needed (seaborn already in `viz` optional-dependencies).

**Next Step**: Choose integration path and update `charts.py` to pass raw records to heatmap function.
