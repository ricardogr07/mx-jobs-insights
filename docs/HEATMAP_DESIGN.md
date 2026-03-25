# Seaborn Heatmap Design - Complete Blueprint

## 1. Data Structure Design

```
INPUT (JoinedObservationRecord tuples)
├── tech_stack: ("Python", "SQL", "AWS")
├── seniority_level: "Mid-level"
└── [100+ more records]

PROCESSING
├── Step 1: Cross-tabulate (tech × seniority)
├── Step 2: Count co-occurrences
└── Step 3: Build DataFrame (top 10 skills × all seniorities)

OUTPUT (pandas.DataFrame)
           Entry-level  Mid-level  Senior
Python            8         12        15
SQL               5         15        12
AWS               2         18         8
React             6         14        10
...
```

## 2. Complete Data Flow

```
ReportMetrics & RawRecords
         ↓
build_tech_seniority_pivot_from_records()
         ↓
pd.DataFrame (pivot table)
         ↓
    ┌────┴────┐
    ↓         ↓
Seaborn   Plotly
    ↓         ↓
mpl.Figure go.Figure
    ↓         ↓
base64   JSON/HTML
    ↓         ↓
<img/>   <script/>
```

## 3. Generating from ReportMetrics: Three Options

| Level | Approach | Effort | Accuracy | Code |
|-------|----------|--------|----------|------|
| **L1: Current** | Use aggregates only (no cross-tab) | 5 min | Low | `tech_stack_counts` + `seniority_counts` independent |
| **L2: Recommended** | Pass raw records through pipeline | 2 hrs | High | Modify `MetricsBuildResult`, update function signatures |
| **L3: Future** | Pre-compute in database | 1 day | High | Add materialized view to curated schema |

### L1: Quick Mock (for testing UI)
```python
# Create synthetic pivot from separate counts
pivot = pd.DataFrame(
    np.random.randint(0, 20, size=(8, 3)),
    index=[tech for tech, _ in metrics.tech_stack_counts[:8]],
    columns=[sen for sen, _ in metrics.seniority_counts],
)
```

### L2: Recommended (with access to records)
```python
records = dataset.records  # From CuratedDatasetReader
pivot = build_tech_seniority_pivot_from_records(records)
```

## 4. Seaborn Heatmap Best Practices

### Color Mapping
```python
sns.heatmap(
    pivot,
    cmap="RdYlGn",      # ✓ Diverging (not sequential)
    vmin=0,             # ✓ Fair scale (not auto-normalized)
    annot=True,         # ✓ Show actual counts
    fmt="d",            # ✓ Integer format
)
```

**Why RdYlGn?**
- Red = High skill demand (hot jobs)
- Yellow = Medium demand
- Green = Low demand (cool skills for this level)
- Readers immediately see patterns

### Styling Choices
```python
sns.heatmap(
    pivot,
    linewidths=1,           # ✓ Clear cell boundaries
    linecolor="white",      # ✓ High contrast
    square=False,           # ✓ Allow readable skill names
    cbar_kws={"label": "Job Count"},  # ✓ Labeled colorbar
)
```

### Layout Tips
```python
fig, ax = plt.subplots(figsize=(12, 7), dpi=100)  # ✓ Good screen resolution
ax.set_title("...", fontsize=16, fontweight="bold", pad=20)
ax.tick_params(axis="x", rotation=45)  # ✓ Prevent label overlap
plt.tight_layout()  # ✓ Prevent label cutoff
```

## 5. Converting to Base64 PNG for HTML Embedding

### Flow
```
matplotlib.Figure
        ↓
savefig → BytesIO buffer (in memory, no temp files)
        ↓
read buffer → bytes
        ↓
base64.b64encode() → string
        ↓
Prepend "data:image/png;base64," → data URI
        ↓
Direct HTML embedding: <img src="{data_uri}" />
```

### Code
```python
def figure_to_base64_seaborn(fig: plt.Figure) -> str:
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=100, bbox_inches="tight")
    buffer.seek(0)
    
    img_bytes = buffer.read()
    b64_string = base64.b64encode(img_bytes).decode("utf-8")
    return f"data:image/png;base64,{b64_string}"
```

### HTML Usage
```html
<img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAA..." 
     alt="Skills Heatmap" 
     style="max-width: 100%; height: auto;" />
```

**Advantages**
- ✓ No external server needed
- ✓ Single HTML file self-contained  
- ✓ Works offline
- ✓ Fast (no HTTP request)

**Disadvantages**
- ✗ Data URI can be ~2-5MB for large images (usually OK)
- ✗ Less cacheable than URL-based images

**Size Tips**
- `figsize=(12, 7), dpi=100` → ~200-300KB base64
- `dpi=150` → ~500KB (for print quality)
- Reduce with `figsize=(8, 5)` if needed

## 6. Complete Sample Code: Records → Base64

```python
# 1. Load records
from mexico_linkedin_jobs_portfolio.analytics.dataset import CuratedDatasetReader
from mexico_linkedin_jobs_portfolio.config import CuratedStorageConfig

reader = CuratedDatasetReader()
dataset = reader.load(CuratedStorageConfig(...))
records = dataset.records

# 2. Build pivot
from mexico_linkedin_jobs_portfolio.analytics.heatmap_design import (
    build_tech_seniority_pivot_from_records,
)

pivot = build_tech_seniority_pivot_from_records(
    records,
    top_n_skills=10,
)

# 3. Create heatmap
from mexico_linkedin_jobs_portfolio.analytics.heatmap_design import (
    create_seaborn_heatmap,
)

fig = create_seaborn_heatmap(
    pivot,
    title="Tech Skills by Seniority Level",
    cmap="RdYlGn",
)

# 4. Convert to base64
from mexico_linkedin_jobs_portfolio.analytics.heatmap_design import (
    figure_to_base64_seaborn,
)

data_uri = figure_to_base64_seaborn(fig)

# 5. Embed in HTML template
html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Job Market Insights</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        img {{ max-width: 100%; height: auto; border: 1px solid #ddd; }}
        .chart-container {{ margin: 20px 0; }}
    </style>
</head>
<body>
    <h1>Mexico Tech Job Market</h1>
    <div class="chart-container">
        <h2>Skills in Demand by Experience Level</h2>
        <img src="{data_uri}" alt="Skills Heatmap" />
    </div>
</body>
</html>
"""

with open("report.html", "w") as f:
    f.write(html)

print("✓ Report saved: report.html")
```

## 7. Comparison: Seaborn vs Plotly

| Aspect | Seaborn | Plotly |
|--------|---------|--------|
| **Setup** | pip install seaborn | pip install plotly |
| **Interaction** | Static | Interactive (hover, zoom) |
| **Styling** | Matplotlib customization | JSON-based layouts |
| **Web Ready** | Needs base64 conversion | Native HTML/JSON |
| **File Size** | Smaller (~200-300KB PNG) | Larger (JSON) |
| **Accessibility** | Image (alt text needed) | Vector/HTML (screen readers) |
| **Learning Curve** | Familiar to data scientists | Growing standard for web |
| **Embedding** | `<img src="..." />` | `<script>Plotly.newPlot(...)</script>` |

**Recommendation**: For final reports → **Plotly** (interactive, web-native). For quick exports → **Seaborn** (familiar, simpler).

## 8. Integration Path: Next Steps

### Current State
```
ReportMetrics → chart functions → Plotly figures
                      ✗ No raw record access
```

### Minimal Integration (v1)
```python
# Create a wrapper function that accepts optional records
def create_seniority_skills_heatmap(
    metrics: ReportMetrics,
    records: Optional[tuple[JoinedObservationRecord, ...]] = None,
    use_plotly: bool = True,
) -> go.Figure:
    if records and use_plotly:
        # New: use real data
        pivot = build_tech_seniority_pivot_from_records(records)
        return create_plotly_heatmap(pivot)
    else:
        # Fallback: current placeholder
        return _placeholder_heatmap()
```

### Full Integration (v2)
```python
# Modify MetricsBuildResult to include records
@dataclass
class MetricsBuildResult:
    metrics: ReportMetrics
    latest_jobs: tuple[LatestJobRecord, ...]
    records: tuple[JoinedObservationRecord, ...]  # ← NEW

# Update chart pipeline
charts = create_all_charts(metrics, records=build_result.records)
```

## 9. Key Files Created

1. **`heatmap_design.py`** (364 lines)
   - Core implementation
   - Both seaborn and Plotly approaches
   - Complete workflows
   - Documentation & best practices

2. **`test_heatmap_design.py`** (217 lines)
   - Comprehensive test suite
   - Sample data generation
   - All workflows demonstrated
   - Styling variations tested

## 10. Quick Start

```bash
# Run tests
python -m pytest tests/test_heatmap_design.py -v

# Within your code
from mexico_linkedin_jobs_portfolio.analytics.heatmap_design import (
    seaborn_complete_workflow,
    plotly_complete_workflow,
)

# Get base64 PNG for HTML embedding
data_uri = seaborn_complete_workflow(records)

# Get interactive Plotly figure
fig = plotly_complete_workflow(records)
```

---

**Status**: ✓ Design complete, implementation ready, test suite provided

**Next Actions**:
1. Run tests to validate
2. Choose integration path (v1 wrapper vs v2 full)
3. Update `charts.py` with new heatmap function
4. Test with real curated data
